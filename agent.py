"""DeepSeek calls, response validation, and safe application errors."""

from collections.abc import Callable, Sequence
import json
import httpx2 as httpx

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from models import CareerPlan, ChatMessage, PlanValidationError, parse_plan, validate_duration
from mentors import DEFAULT_MENTOR
from prompts import plan_system_prompt, system_prompt
from evidence import EvidenceBundle, retrieve_evidence
from references import ReferenceError, validate_references
from search_topics import search_topic
from permissions import MODEL_RESOURCE, PermissionDenied, PermissionGateway

# The destination is DeepSeek, even though the compatible client is named OpenAI.
BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"
# Application limits bound input growth; they are not model token-limit claims.
MAX_MESSAGE_CHARS = 4_000
MAX_HISTORY_CHARS = 60_000
MAX_USER_TURNS = 40


class ChatError(Exception):
    """An error that is safe to display without revealing provider details."""


def validate_history(messages: Sequence[ChatMessage]) -> None:
    """Reject unusable or oversized conversations before a provider request."""
    if not messages or messages[-1].get("role") != "user":
        raise ChatError("Send a message before requesting a reply.")
    for message in messages:
        content = message.get("content")
        if message.get("role") not in {"user", "assistant"}:
            raise ChatError("This conversation could not be read. Start a new conversation.")
        if not isinstance(content, str) or not content.strip():
            raise ChatError("Please enter a message before sending.")
        if message["role"] == "user" and len(content) > MAX_MESSAGE_CHARS:
            raise ChatError("Please keep each message to 4,000 characters or fewer.")
    if (
        # Python counts True as 1, so this counts submitted user turns.
        sum(message["role"] == "user" for message in messages) > MAX_USER_TURNS
        or sum(len(message["content"]) for message in messages) > MAX_HISTORY_CHARS
    ):
        raise ChatError("This conversation has reached its limit. Start a new conversation.")


def reply(
    messages: Sequence[ChatMessage], *, api_key: str, model: str = DEFAULT_MODEL,
    mentor_id: str = DEFAULT_MENTOR, source_region: str = "Not specified",
    on_evidence: Callable[[EvidenceBundle], None] | None = None,
    gateway: PermissionGateway | None = None,
) -> str:
    """One explicit request grants bounded tools; always revoke them afterward."""
    gate = _request_gateway(gateway, model_limit=1)
    try:
        return _reply(messages, api_key=api_key, model=model, mentor_id=mentor_id,
                      source_region=source_region, on_evidence=on_evidence, gateway=gate)
    except PermissionDenied:
        raise ChatError("This action is outside the current permission, expired, paused, or over its call limit. Review Permissions and retry when ready.") from None
    finally:
        gate.revoke()


def _request_gateway(gateway, *, model_limit):
    if gateway is None:
        return PermissionGateway(model_limit=model_limit)
    if not isinstance(gateway, PermissionGateway):
        raise ChatError("The request permission could not be read. Start a new conversation.")
    return gateway


def _reply(
    messages: Sequence[ChatMessage], *, api_key: str, model: str = DEFAULT_MODEL,
    mentor_id: str = DEFAULT_MENTOR,
    source_region: str = "Not specified",
    on_evidence: Callable[[EvidenceBundle], None] | None = None,
    gateway: PermissionGateway,
) -> str:
    """Return one complete DeepSeek reply, or raise a safe ChatError."""
    # Validate here as well as in the page so this module is safe to reuse.
    validate_history(messages)
    if not api_key.strip():
        raise ChatError("Chat is not configured yet. Complete the local setup to begin.")

    # The system message defines the assistant's behavior. User and assistant
    # messages provide the conversation context for this particular request.
    try:
        instruction = system_prompt(mentor_id)
    except ValueError as error:
        raise ChatError(str(error)) from None
    evidence = _research(messages, api_key=api_key, mentor_id=mentor_id,
                         source_region=source_region, on_evidence=on_evidence, gateway=gateway)
    if evidence.status != "ready":
        # Search failure cannot silently become apparently researched advice.
        return (
            "I could not retrieve suitable primary sources for this reply, so I cannot "
            "offer source-grounded advice yet. No recommendation has been verified. "
            "You can retry, choose a source region, or clarify your concern. "
            "What decision would you most like help clarifying?"
        )
    instruction += "\n" + evidence.as_prompt()
    payload = [{"role": "system", "content": instruction}]
    payload.extend({"role": item["role"], "content": item["content"]} for item in messages)

    answer = _complete(payload, api_key=api_key, model=model, gateway=gateway)
    try:
        validate_references(answer, evidence)
    except ReferenceError:
        raise ChatError("The reply did not pass its source-reference checks. Your message is saved; you can retry.") from None
    return answer


def generate_plan(
    messages: Sequence[ChatMessage], *, duration_days: int, api_key: str,
    model: str = DEFAULT_MODEL, mentor_id: str = DEFAULT_MENTOR,
    source_region: str = "Not specified",
    on_evidence: Callable[[EvidenceBundle], None] | None = None,
    gateway: PermissionGateway | None = None,
) -> CareerPlan:
    """A plan correction shares the original call budget and authorization."""
    gate = _request_gateway(gateway, model_limit=2)
    try:
        return _generate_plan(messages, duration_days=duration_days, api_key=api_key,
                              model=model, mentor_id=mentor_id, source_region=source_region,
                              on_evidence=on_evidence, gateway=gate)
    except PermissionDenied:
        raise ChatError("This action is outside the current permission, expired, paused, or over its call limit. Review Permissions and retry when ready.") from None
    finally:
        gate.revoke()


def _generate_plan(
    messages: Sequence[ChatMessage],
    *,
    duration_days: int,
    api_key: str,
    model: str = DEFAULT_MODEL,
    mentor_id: str = DEFAULT_MENTOR,
    source_region: str = "Not specified",
    on_evidence: Callable[[EvidenceBundle], None] | None = None,
    gateway: PermissionGateway,
) -> CareerPlan:
    """Generate, check, and at most once regenerate a structured task plan."""
    validate_history(messages)
    try:
        validate_duration(duration_days)
    except PlanValidationError as error:
        raise ChatError(str(error)) from None

    try:
        mentor_instruction = plan_system_prompt(mentor_id)
    except ValueError as error:
        raise ChatError(str(error)) from None
    if not api_key.strip():
        raise ChatError("Chat is not configured yet. Complete the local setup to begin.")
    evidence = _research(messages, api_key=api_key, mentor_id=mentor_id,
                         source_region=source_region, on_evidence=on_evidence, gateway=gateway)
    if evidence.status != "ready":
        raise ChatError("Suitable primary sources could not be retrieved. A source-grounded plan was not generated. Retry or clarify your concern.")
    schema = json.dumps(CareerPlan.model_json_schema(), ensure_ascii=True)
    instruction = (
        mentor_instruction
        + "\n" + evidence.as_prompt()
        + "\nCite at least one current source ID, such as [S1], in a relevant task reason or summary."
        + f"\nThe selected planning period is exactly {duration_days} days."
        + "\nThe first task starts on day 1. Sort tasks by start day."
        + " All end days must fit the selected period."
        + "\nFollow this JSON schema:\n" + schema
        + '\nExample JSON shape (replace all example text and timing): '
        + '{"summary":"An exploration plan.","assumptions":[],"duration_days":3,'
        + '"tasks":[{"title":"Identify priorities","action":"Write three priorities.",'
        + '"start_day":1,"end_day":1,"reason":"Clarifies the current concern.",'
        + '"completion_criterion":"A written list of three priorities."},'
        + '{"title":"Compare options","action":"Compare two approaches.",'
        + '"start_day":2,"end_day":2,"reason":"Tests possible directions.",'
        + '"completion_criterion":"A comparison note."},'
        + '{"title":"Take a next step","action":"Try one small experiment.",'
        + '"start_day":3,"end_day":3,"reason":"Creates a practical next step.",'
        + '"completion_criterion":"One experiment completed and a note written."}]}'
    )
    feedback = ""
    for attempt in range(2):
        # Only a structural/schedule failure reaches a second request. Network,
        # authentication, and incomplete-output errors stop immediately.
        payload = [{"role": "system", "content": instruction + feedback}]
        payload.extend({"role": item["role"], "content": item["content"]} for item in messages)
        raw = _complete(payload, api_key=api_key, model=model, json_mode=True, gateway=gateway)
        try:
            plan = parse_plan(raw, expected_days=duration_days)
            validate_references(plan.model_dump_json(), evidence)
            return plan
        except (PlanValidationError, ReferenceError) as error:
            if attempt == 1:
                raise ChatError(
                    "The plan did not pass its field, schedule, and source-reference checks after one correction. "
                    "Your message is saved; you can retry."
                ) from None
            # This feedback contains fixed rule descriptions, not invalid output
            # or private input values from a validation exception.
            feedback = "\nThe previous attempt failed validation: " + str(error) + ". Generate a corrected JSON plan."
    raise ChatError("The plan could not be completed.")


def _research(messages, *, api_key, mentor_id, source_region, on_evidence, gateway):
    """Always retrieve before advice; share one result across a plan correction."""
    try:
        query = search_topic(messages, mentor_id, source_region)
    except ValueError as error:
        raise ChatError(str(error)) from None
    researcher = gateway.delegate("research", tools=("web.search",))
    evidence = retrieve_evidence(query, api_key=api_key, mentor_id=mentor_id, gateway=researcher)
    if on_evidence is not None:
        on_evidence(evidence)
    return evidence


def _complete(
    payload: list[dict[str, str]], *, api_key: str, model: str, json_mode: bool = False,
    gateway: PermissionGateway | None = None,
) -> str:
    """Share one provider request boundary between chat and checked plans."""
    if not isinstance(gateway, PermissionGateway):
        raise PermissionDenied("A request permission is required.")
    writer = gateway.delegate("writer", tools=("model.complete",))
    return writer.run(
        "model.complete", resource=MODEL_RESOURCE,
        data_class="conversation",
        operation=lambda: _provider_complete(payload, api_key=api_key, model=model, json_mode=json_mode),
    )


def _provider_complete(payload, *, api_key, model, json_mode):
    """Private transport; called only inside an authorized tool operation."""
    if not api_key.strip():
        raise ChatError("Chat is not configured yet. Complete the local setup to begin.")

    try:
        # 'with' closes the client's network resources when this request ends.
        with httpx.Client(follow_redirects=False, trust_env=False, timeout=60.0) as transport, OpenAI(
            api_key=api_key.strip(),
            base_url=BASE_URL,
            timeout=60.0,
            # A retry should be an explicit user action, not a hidden extra call.
            max_retries=0,
            # Keep credentials on the approved host: do not follow redirects.
            http_client=transport,
        ) as client:
            response = client.chat.completions.create(
                model=model.strip() or DEFAULT_MODEL,
                messages=payload,
                max_tokens=4_000 if json_mode else 2_500,
                # The first version waits for one complete reply before display.
                stream=False,
                # Use the documented non-thinking mode for ordinary chat.
                extra_body={"thinking": {"type": "disabled"}},
                **({"response_format": {"type": "json_object"}} if json_mode else {}),
            )
    except APITimeoutError:
        raise ChatError("The reply took too long. Your message is saved; you can retry.") from None
    except APIConnectionError:
        raise ChatError("Could not reach the conversation service. Check your connection and retry.") from None
    except APIStatusError as error:
        # Map HTTP status codes to helpful messages without showing the raw
        # provider response, which may contain private request information.
        if error.status_code in {401, 403}:
            message = "Model access was denied. Check the local DeepSeek credentials and permissions."
        elif error.status_code == 402:
            message = "The DeepSeek account needs available API balance before chat can continue."
        elif error.status_code == 429:
            message = "The conversation service is busy or its request limit was reached. Please retry later."
        elif error.status_code in {400, 404, 422}:
            message = "The conversation request was rejected. Check the configured model and setup."
        else:
            message = "The conversation service could not complete the reply. Please retry later."
        raise ChatError(message) from None

    # A successful HTTP request is not enough: a usable answer must exist.
    if not response.choices:
        raise ChatError("No reply was returned. Please retry.")
    choice = response.choices[0]
    if choice.finish_reason != "stop":
        # A truncated response must not be treated as a complete consultation.
        raise ChatError("The reply was incomplete. Retry, or start a shorter conversation.")
    content = choice.message.content
    if not isinstance(content, str) or not content.strip():
        raise ChatError("An empty reply was returned. Please retry.")
    return content.strip()
