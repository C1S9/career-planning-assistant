"""DeepSeek calls, response validation, and safe application errors."""

from collections.abc import Sequence
import json

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from models import CareerPlan, ChatMessage, PlanValidationError, parse_plan, validate_duration
from prompts import PLAN_SYSTEM_PROMPT, SYSTEM_PROMPT

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
    messages: Sequence[ChatMessage], *, api_key: str, model: str = DEFAULT_MODEL
) -> str:
    """Return one complete DeepSeek reply, or raise a safe ChatError."""
    # Validate here as well as in the page so this module is safe to reuse.
    validate_history(messages)
    if not api_key.strip():
        raise ChatError("Chat is not configured yet. Complete the local setup to begin.")

    # The system message defines the assistant's behavior. User and assistant
    # messages provide the conversation context for this particular request.
    payload = [{"role": "system", "content": SYSTEM_PROMPT}]
    payload.extend({"role": item["role"], "content": item["content"]} for item in messages)

    return _complete(payload, api_key=api_key, model=model)


def generate_plan(
    messages: Sequence[ChatMessage],
    *,
    duration_days: int,
    api_key: str,
    model: str = DEFAULT_MODEL,
) -> CareerPlan:
    """Generate, check, and at most once regenerate a structured task plan."""
    validate_history(messages)
    try:
        validate_duration(duration_days)
    except PlanValidationError as error:
        raise ChatError(str(error)) from None

    schema = json.dumps(CareerPlan.model_json_schema(), ensure_ascii=True)
    instruction = (
        PLAN_SYSTEM_PROMPT
        + f"\nThe selected planning period is exactly {duration_days} days."
        + "\nThe first task starts on day 1. Sort tasks by start day."
        + " All end days must fit the selected period."
        + "\nFollow this JSON schema:\n" + schema
        + '\nExample JSON shape (replace all example text and timing): '
        + '{"summary":"An exploration plan.","assumptions":[],"duration_days":3,'
        + '"tasks":[{"title":"Identify skills","action":"Write five skills.",'
        + '"start_day":1,"end_day":1,"reason":"Uses prior work experience.",'
        + '"completion_criterion":"A written list of five skills."},'
        + '{"title":"Compare directions","action":"Compare two roles.",'
        + '"start_day":2,"end_day":2,"reason":"Tests possible interests.",'
        + '"completion_criterion":"A comparison note."},'
        + '{"title":"Take a next step","action":"Send one outreach message.",'
        + '"start_day":3,"end_day":3,"reason":"Creates a practical next step.",'
        + '"completion_criterion":"One message sent."}]}'
    )
    feedback = ""
    for attempt in range(2):
        # Only a structural/schedule failure reaches a second request. Network,
        # authentication, and incomplete-output errors stop immediately.
        payload = [{"role": "system", "content": instruction + feedback}]
        payload.extend({"role": item["role"], "content": item["content"]} for item in messages)
        raw = _complete(payload, api_key=api_key, model=model, json_mode=True)
        try:
            return parse_plan(raw, expected_days=duration_days)
        except PlanValidationError as error:
            if attempt == 1:
                raise ChatError(
                    "The plan did not pass its field and schedule checks after one correction. "
                    "Your message is saved; you can retry."
                ) from None
            # This feedback contains fixed rule descriptions, not invalid output
            # or private input values from a validation exception.
            feedback = "\nThe previous attempt failed validation: " + str(error) + ". Generate a corrected JSON plan."
    raise ChatError("The plan could not be completed.")


def _complete(
    payload: list[dict[str, str]], *, api_key: str, model: str, json_mode: bool = False
) -> str:
    """Share one provider request boundary between chat and checked plans."""
    if not api_key.strip():
        raise ChatError("Chat is not configured yet. Complete the local setup to begin.")

    try:
        # 'with' closes the client's network resources when this request ends.
        with OpenAI(
            api_key=api_key.strip(),
            base_url=BASE_URL,
            timeout=60.0,
            # A retry should be an explicit user action, not a hidden extra call.
            max_retries=0,
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
