"""A local, session-only career-planning conversation."""

import os
from uuid import uuid4

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from agent import ChatError, DEFAULT_MODEL, MAX_MESSAGE_CHARS, generate_plan, reply, validate_history
from models import MAX_PLAN_DAYS, MIN_PLAN_DAYS, format_plan, validate_duration, PlanValidationError
from prompts import WELCOME

# Configure the page before drawing the visible chat interface.
st.set_page_config(page_title="Career Planning Assistant", page_icon="💬", layout="centered")


def setting(name: str, default: str = "") -> str:
    """Read an environment setting first, then private Streamlit secrets."""
    value = os.environ.get(name, "").strip()
    if value:
        return value
    try:
        # Streamlit reads .streamlit/secrets.toml from the project directory.
        value = st.secrets.get(name, default)
    except (StreamlitSecretNotFoundError, FileNotFoundError, KeyError):
        # Missing setup is a normal first-use state: the page can still open.
        return default
    return value.strip() if isinstance(value, str) else default


def new_conversation() -> None:
    """Initialize this browser session and invalidate any older pending reply."""
    # The greeting is local text. It does not make an API request.
    st.session_state.messages = [{"role": "assistant", "content": WELCOME}]
    # This is a local request identifier, not a credential or API key.
    st.session_state.request_token = uuid4().hex
    # queued grants permission for one request on the next script run.
    st.session_state.queued = False
    # Error messages stay separate from the conversation sent to the model.
    st.session_state.reply_error = None
    st.session_state.request_kind = "chat"
    st.session_state.request_days = None
    st.session_state.plan_duration = 7


def queue_message(content: str, *, kind: str = "chat", days: int | None = None) -> None:
    """Save one user turn with an immutable snapshot of its requested action."""
    candidate = st.session_state.messages + [{"role": "user", "content": content.strip()}]
    validate_history(candidate)
    st.session_state.messages = candidate
    st.session_state.reply_error = None
    st.session_state.request_token = uuid4().hex
    st.session_state.request_kind = kind
    st.session_state.request_days = days
    st.session_state.queued = True


if "messages" not in st.session_state:
    # Ordinary Python variables reset on a rerun; session_state keeps this chat.
    new_conversation()

# Existing browser sessions may survive this code update. Add new fields without
# resetting a learner's already working conversation.
st.session_state.setdefault("request_kind", "chat")
st.session_state.setdefault("request_days", None)
st.session_state.setdefault("plan_duration", 7)

st.title("Career Planning Assistant")
st.write("Talk through your career uncertainty and find a practical next step.")
st.caption("Messages you send are shared with DeepSeek. This app keeps chat history only in this session.")

if st.button("New Conversation"):
    new_conversation()
    # Restart the script immediately so cleared history is what the user sees.
    st.rerun()

api_key = setting("DEEPSEEK_API_KEY")
model = setting("DEEPSEEK_MODEL", DEFAULT_MODEL)
configured = bool(api_key) and api_key != "paste-your-deepseek-key-here"

if not configured:
    st.info("Chat is not configured yet. Complete the local setup to begin.")

# Consume the queued flag before doing any network work. A later ordinary rerun
# must not automatically send the same message again.
request_now = st.session_state.queued
st.session_state.queued = False

# Redraw saved messages on every run; rendering history does not call DeepSeek.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("schedule_checked"):
            st.caption("Task fields and schedule checked. Career suitability still needs your judgment.")
        st.markdown(message["content"])

# A final user message means its assistant reply has not succeeded yet.
awaiting_reply = st.session_state.messages[-1]["role"] == "user"

# An explicit duration selection gives the validator a trusted value to compare
# with the model's claimed duration. Changing this widget makes no model request.
with st.expander("Create a task plan"):
    days = st.number_input(
        "Plan length (days)", min_value=MIN_PLAN_DAYS, max_value=MAX_PLAN_DAYS,
        step=1, key="plan_duration", disabled=awaiting_reply,
    )
    has_background = any(message["role"] == "user" for message in st.session_state.messages)
    st.caption("Share your background in the chat, then choose a period for a checked task plan.")
    if st.button("Create checked plan", disabled=not configured or awaiting_reply or not has_background):
        try:
            # Widget bounds are helpful UX, but Python checks again before use.
            validate_duration(days)
            queue_message(
                f"Create a checked {days}-day career exploration plan using the background I have shared.",
                kind="plan", days=days,
            )
        except (ChatError, PlanValidationError) as error:
            st.warning(str(error))
        else:
            st.rerun()

if awaiting_reply and not request_now:
    st.error(st.session_state.reply_error or "Your last message has no reply yet. Retry when you are ready.")
    if st.button("Retry Reply", disabled=not configured):
        # Retry the existing user turn instead of appending a duplicate message.
        st.session_state.reply_error = None
        st.session_state.request_token = uuid4().hex
        st.session_state.queued = True
        st.rerun()

prompt = st.chat_input(
    "Tell me what feels uncertain about your career...",
    max_chars=MAX_MESSAGE_CHARS,
    disabled=not configured or awaiting_reply,
)

if prompt:
    try:
        queue_message(prompt)
    except ChatError as error:
        st.warning(str(error))
    else:
        # The next run shows the saved user message and disables the composer
        # before processing the queued request.
        st.rerun()

if request_now and awaiting_reply:
    # Keep a snapshot of which request this response belongs to.
    token = st.session_state.request_token
    checked = False
    try:
        with st.spinner("Thinking about your next step..."):
            # Pass a list snapshot to the API layer; UI state stays in this file.
            if st.session_state.request_kind == "plan":
                plan = generate_plan(
                    list(st.session_state.messages), duration_days=st.session_state.request_days,
                    api_key=api_key, model=model,
                )
                answer = format_plan(plan)
                checked = True
            else:
                answer = reply(list(st.session_state.messages), api_key=api_key, model=model)
    except ChatError as error:
        # Expected application errors already contain a safe display message.
        if token == st.session_state.request_token:
            st.session_state.reply_error = str(error)
    except Exception:
        # Unexpected errors must not expose credentials or provider payloads.
        if token == st.session_state.request_token:
            st.session_state.reply_error = "The reply could not be completed. Please retry or start a new conversation."
    else:
        # Ignore a stale result if the user has started a different conversation.
        if token == st.session_state.request_token:
            st.session_state.messages.append({
                "role": "assistant", "content": answer, "schedule_checked": checked,
            })
            st.session_state.reply_error = None
    # Render the new reply or retry control; the queued flag is already cleared.
    st.rerun()
