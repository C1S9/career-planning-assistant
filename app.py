"""A focused coaching conversation with explicit, independently checked plans."""

import os
from uuid import uuid4

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from agent import ChatError, DEFAULT_MODEL, MAX_MESSAGE_CHARS, generate_plan, reply, validate_history
from mentors import DEFAULT_MENTOR, MENTORS, get_mentor
from models import MAX_PLAN_DAYS, MIN_PLAN_DAYS, PlanValidationError, format_plan, validate_duration
from version import APP_NAME, __version__
from coaching_skills import active_skill_names
from permissions import AuditTrail, PermissionGateway
from student_market import market_brief
from student_ui import (
    export_advice, initialize_student_state, render_application_tracker,
    render_profile, render_skill_comparison,
)

st.set_page_config(
    page_title=APP_NAME, page_icon=":material/explore:", layout="centered",
    initial_sidebar_state="expanded",
    menu_items={"About": f"{APP_NAME} v{__version__}. Student career preparation with DeepSeek."},
)
# Use the tracker's validated CSV download instead of generic table exports,
# which omit its schema and spreadsheet-formula escaping.
st.set_option("client.disableDataExport", True)


def setting(name: str, default: str = "") -> str:
    """Read local credentials without copying them into public source or logs."""
    value = os.environ.get(name, "").strip()
    if value:
        return value
    try:
        value = st.secrets.get(name, default)
    except (StreamlitSecretNotFoundError, FileNotFoundError, KeyError):
        return default
    return value.strip() if isinstance(value, str) else default


def new_conversation(mentor_id: str | None = None) -> None:
    """Clear old context and invalidate its pending response when the mentor changes."""
    current = st.session_state.get("current_permission")
    if isinstance(current, PermissionGateway):
        current.revoke()
    st.session_state.current_permission = None
    st.session_state.permission_audit = AuditTrail()
    st.session_state.last_permission = None
    selected = mentor_id or st.session_state.get("active_mentor", DEFAULT_MENTOR)
    st.session_state.active_mentor = selected
    st.session_state.messages = [{"role": "assistant", "content": get_mentor(selected).welcome}]
    st.session_state.request_token = uuid4().hex
    st.session_state.queued = False
    st.session_state.reply_error = None
    st.session_state.request_kind = "chat"
    st.session_state.request_days = None
    st.session_state.plan_duration = 7
    st.session_state.failed_evidence = None


def queue_message(content: str, *, kind: str = "chat", days: int | None = None) -> None:
    """One user action grants permission for exactly one queued request."""
    candidate = st.session_state.messages + [{"role": "user", "content": content.strip()}]
    validate_history(candidate)
    st.session_state.messages = candidate
    st.session_state.reply_error = None
    st.session_state.failed_evidence = None
    st.session_state.request_token = uuid4().hex
    st.session_state.request_kind = kind
    st.session_state.request_days = days
    st.session_state.queued = True


def use_session_connection() -> None:
    """Keep a pasted key in this browser session only; never write it to disk."""
    supplied = st.session_state.get("connection_key", "").strip()
    if supplied:
        st.session_state.session_api_key = supplied
        st.session_state.connection_key = ""
        st.session_state.connection_notice = "API key is available for this session."
    else:
        st.session_state.connection_notice = "Existing local settings will be used when available."


def show_evidence(record: dict) -> None:
    """Render application-owned retrieval records separately from generated text."""
    if record.get("status") == "ready":
        with st.expander("Sources consulted", icon=":material/travel_explore:"):
            st.caption("Primary-source excerpts retrieved before this reply. This does not verify every claim or personal suitability.")
            st.caption(f"Search topic: {record['query']} · Retrieved: {record['checked_at']} (UTC)")
            for source in record["sources"]:
                st.link_button(f"[{source['id']}] {source['title']}", source["url"])
                st.caption(f"Publication date reported by search: {source.get('published_date') or 'Unknown'}")
                st.text(source["excerpt"])
    else:
        st.warning(record.get("note") or "Suitable primary sources were not available. No source-grounded recommendation was generated.")


st.session_state.setdefault("mentor_choice", DEFAULT_MENTOR)
st.session_state.setdefault("active_mentor", DEFAULT_MENTOR)
initialize_student_state()
st.session_state.setdefault("workspace_view", "Career chat")
if "messages" not in st.session_state:
    new_conversation()
if "permission_audit" not in st.session_state:
    # Existing source-mode sessions may survive a development hot reload.
    st.session_state.permission_audit = AuditTrail()
for name, default in (("request_kind", "chat"), ("request_days", None), ("plan_duration", 7)):
    st.session_state.setdefault(name, default)

with st.sidebar:
    st.caption(f"{APP_NAME.upper()} · v{__version__}")
    selected = st.selectbox(
        "Choose your mentor", tuple(MENTORS), key="mentor_choice",
        format_func=lambda mentor_id: get_mentor(mentor_id).name,
        help="Changing mentors starts a fresh conversation, so their contexts stay separate.",
    )
    if selected != st.session_state.active_mentor:
        # This happens before the plan widgets are drawn, so their state can reset.
        new_conversation(selected)
    mentor = get_mentor(selected)
    st.caption(mentor.description)
    if st.button("New Conversation", icon=":material/add:", width="stretch"):
        new_conversation()
        st.rerun()

    local_key = setting("DEEPSEEK_API_KEY")
    current_key = st.session_state.get("session_api_key", "") or local_key
    with st.expander("Connection", icon=":material/key:"):
        st.caption("Use your DeepSeek key. A pasted key stays in this session and is not saved to disk.")
        with st.form("connection_form"):
            st.text_input("DeepSeek API key", type="password", key="connection_key")
            st.text_input("Model", value=setting("DEEPSEEK_MODEL", DEFAULT_MODEL), key="connection_model")
            st.form_submit_button("Use for this session", on_click=use_session_connection)
        if st.session_state.get("connection_notice"):
            st.caption(st.session_state.connection_notice)
        if st.session_state.get("session_api_key") and st.button("Forget session key"):
            del st.session_state.session_api_key
            st.session_state.connection_notice = "Session key removed. Local settings, if present, still apply."
            st.rerun()

api_key = st.session_state.get("session_api_key", "") or local_key
model = st.session_state.get("connection_model", "").strip() or DEFAULT_MODEL
configured = bool(api_key) and api_key not in {"paste", "paste-your-deepseek-key-here", "YOUR_API_KEY"}
request_now = st.session_state.queued
st.session_state.queued = False
if request_now:
    st.session_state.workspace_view = "Career chat"
awaiting_reply = st.session_state.messages[-1]["role"] == "user"

with st.sidebar:
    with st.expander("Create a task plan", icon=":material/checklist:"):
        days = st.number_input(
            "Plan length (days)", min_value=MIN_PLAN_DAYS, max_value=MAX_PLAN_DAYS,
            step=1, key="plan_duration", disabled=awaiting_reply,
        )
        st.caption("Share your situation first, then turn the conversation into practical tasks.")
        st.caption("Planning also uses the realistic-action-planning skill.")
        has_background = any(message["role"] == "user" for message in st.session_state.messages)
        if st.button("Create checked plan", type="primary", width="stretch", disabled=not configured or awaiting_reply or not has_background):
            try:
                validate_duration(days)
                queue_message(
                    f"Create a checked {days}-day action plan using the background I have shared.",
                    kind="plan", days=days,
                )
            except (ChatError, PlanValidationError) as error:
                st.warning(str(error))
            else:
                st.rerun()
    st.caption("Switch light or dark from the top-right app menu.")
    render_profile(new_conversation, disabled=request_now)
    st.caption("Career preparation. Your choices remain yours.")
    with st.expander("Sources and skills", icon=":material/travel_explore:"):
        st.caption("Source market: mainland China. Set your target role and city in Your student profile.")
        st.caption("Before advice, the app searches primary sources through DeepSeek using a general topic, not your full message. Search may add API charges.")
        st.caption("Search excerpts can be incomplete or outdated. Open the employer's original posting before applying.")
        st.caption("Active coaching skills: " + ", ".join(active_skill_names(selected, planning=False)))

    with st.expander("Permissions", icon=":material/security:"):
        online = st.checkbox("Allow online requests", value=True, key="permission_online")
        if not online:
            current = st.session_state.get("current_permission")
            if isinstance(current, PermissionGateway):
                current.revoke()
        st.number_input("Search calls per request", min_value=1, max_value=2, value=2,
                        step=1, key="permission_search_limit")
        st.number_input("Model calls per plan", min_value=1, max_value=2, value=2,
                        step=1, key="permission_model_limit")
        st.caption("Sending a message or generating a market brief authorizes one request for up to 10 minutes. Chat and briefs use at most one model call; a plan may use a second call to correct invalid output.")
        st.caption("Search receives preset topics. The model receives your student profile and, for chat or plans, your conversation. Both use fixed DeepSeek endpoints. Failed calls count toward these limits; these are not spending limits.")
        st.caption("Pausing blocks new calls when the setting is processed. A request already in progress cannot be recalled. Sending messages, payments, and file deletion are unavailable.")

    with st.expander("Recent activity", icon=":material/history:"):
        snapshot = st.session_state.get("last_permission")
        if snapshot:
            st.caption(f"Last request: {snapshot['search_used']}/{snapshot['search_limit']} search calls · {snapshot['model_used']}/{snapshot['model_limit']} model calls. Permission closed after completion.")
        records = st.session_state.permission_audit.to_records()
        if records:
            st.dataframe([{key: row[key] for key in ("timestamp", "principal", "tool", "status", "reason")} for row in records],
                         hide_index=True, width="stretch")
        else:
            st.caption("No activity yet.")
        st.caption("Up to 200 metadata events in this conversation. No keys, messages, search queries, or source text are recorded here. New Conversation clears this history.")

st.title("Graduate career workbench")
st.caption("Explore a direction. Understand the requirements. Prepare your next application.")
view = st.segmented_control("Workspace", ("Career chat", "Market brief", "Job tools"),
                            key="workspace_view", required=True)

if view == "Job tools":
    render_skill_comparison()
    st.divider()
    render_application_tracker()
    st.stop()

if not configured:
    st.info("Open Connection in the sidebar and enter your DeepSeek API key for online advice. Job tools work without a key.")
if not st.session_state.permission_online:
    st.info("Online requests are paused. Job tools remain available.")

if view == "Market brief":
    from student_tools import CITIES, ROLES

    profile = st.session_state.student_profile
    st.subheader("Research your target market")
    st.write(f"{ROLES[profile.target_role]} · {CITIES[profile.city]} · {profile.goal}")
    st.caption("Uses your saved profile. A brief looks for primary-source evidence on skills, market conditions and pay. General statistics do not establish graduate salaries or live vacancies.")
    with st.container(horizontal=True):
        st.link_button("Browse NCSS internships", "https://www.ncss.cn/student/jobs/internindex.html")
        st.link_button("Browse NCSS graduate jobs", "https://www.ncss.cn/student/jobs/index.html")
    st.caption("These official portal links open in your browser. Check each employer's dates and requirements; the links are not evidence that a job is open.")
    if st.button("Generate market brief", type="primary", disabled=not configured):
        records = []
        gateway = None
        st.session_state.market_result = None
        st.session_state.market_error = None
        st.session_state.market_evidence = None
        try:
            online = st.session_state.permission_online
            if type(online) is not bool:
                raise ChatError("Invalid permission settings. Review Permissions and retry.")
            try:
                gateway = PermissionGateway(search_enabled=online,
                    search_limit=st.session_state.permission_search_limit,
                    model_limit=1 if online else 0, audit=st.session_state.permission_audit)
            except ValueError:
                raise ChatError("Invalid permission settings. Review Permissions and retry.") from None
            st.session_state.current_permission = gateway
            with st.spinner("Checking primary sources for your target role and city..."):
                brief = market_brief(profile, api_key=api_key, model=model, gateway=gateway,
                                     on_evidence=records.append)
            st.session_state.market_result = brief.text
            st.session_state.market_evidence = brief.evidence.to_dict()
        except ChatError as error:
            st.session_state.market_error = str(error)
            st.session_state.market_evidence = records[-1].to_dict() if records else None
        except Exception:
            st.session_state.market_error = "The market brief could not be completed. Please try again."
        finally:
            if gateway is not None:
                gateway.close()
                st.session_state.last_permission = gateway.snapshot()
                st.session_state.current_permission = None
        st.rerun()
    if st.session_state.market_error:
        st.error(st.session_state.market_error)
    if st.session_state.market_result:
        st.markdown(st.session_state.market_result)
        st.download_button("Download market brief", export_advice(st.session_state.market_result,
                            st.session_state.market_evidence), file_name="graduate-market-brief.md",
                            mime="text/markdown", on_click="ignore")
    if st.session_state.market_evidence:
        show_evidence(st.session_state.market_evidence)
    st.stop()

st.write(mentor.description)
st.caption(f"{mentor.name} mentor · Profile and messages are sent to DeepSeek. History stays in this session.")

for index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message.get("schedule_checked"):
            st.caption("Task fields and schedule checked. Source identities checked; facts and suitability still need judgment.")
        st.markdown(message["content"])
        if message.get("evidence"):
            show_evidence(message["evidence"])
        if message.get("schedule_checked"):
            st.download_button("Download action plan", export_advice(message["content"], message.get("evidence")),
                               file_name="graduate-action-plan.md", mime="text/markdown",
                               key=f"plan_download_{index}", on_click="ignore")

if awaiting_reply and not request_now:
    st.error(st.session_state.reply_error or "Your last message has no reply yet. Retry when you are ready.")
    if st.session_state.get("failed_evidence"):
        show_evidence(st.session_state.failed_evidence)
    if st.button("Retry Reply", disabled=not configured):
        st.session_state.reply_error = None
        st.session_state.request_token = uuid4().hex
        st.session_state.queued = True
        st.rerun()

prompt = st.chat_input(
    "Tell me about your studies, target role or job search question...", max_chars=MAX_MESSAGE_CHARS,
    disabled=not configured or awaiting_reply,
)
if prompt:
    try:
        queue_message(prompt)
    except ChatError as error:
        st.warning(str(error))
    else:
        st.rerun()

if request_now and awaiting_reply:
    token = st.session_state.request_token
    selected_mentor = st.session_state.active_mentor
    checked = False
    research_records = []
    gateway = None
    try:
        # Widget bounds are a convenience; the Python gateway validates the
        # actual authorization before any network client can be constructed.
        online = st.session_state.permission_online
        model_limit = st.session_state.permission_model_limit
        if type(online) is not bool or type(model_limit) is not int or not 1 <= model_limit <= 2:
            raise ChatError("Invalid permission settings. Restore the allowed limits and retry.")
        try:
            gateway = PermissionGateway(token, search_enabled=online,
                                        search_limit=st.session_state.permission_search_limit,
                                        model_limit=(model_limit if st.session_state.request_kind == "plan" else 1) if online else 0,
                                        audit=st.session_state.permission_audit)
        except ValueError:
            raise ChatError("Invalid permission settings. Restore the allowed limits and retry.") from None
        st.session_state.current_permission = gateway
        with st.spinner("Checking primary sources, then working through your next step..."):
            if st.session_state.request_kind == "plan":
                plan = generate_plan(
                    list(st.session_state.messages), duration_days=st.session_state.request_days,
                    api_key=api_key, model=model, mentor_id=selected_mentor,
                    source_region="China", student_profile=st.session_state.student_profile,
                    on_evidence=research_records.append,
                    gateway=gateway,
                )
                answer = format_plan(plan)
                checked = True
            else:
                answer = reply(list(st.session_state.messages), api_key=api_key, model=model, mentor_id=selected_mentor,
                               source_region="China", student_profile=st.session_state.student_profile,
                               on_evidence=research_records.append,
                               gateway=gateway)
    except ChatError as error:
        if token == st.session_state.request_token:
            st.session_state.reply_error = str(error)
            st.session_state.failed_evidence = research_records[-1].to_dict() if research_records else None
    except Exception:
        if token == st.session_state.request_token:
            st.session_state.reply_error = "The reply could not be completed. Please retry or start a new conversation."
            st.session_state.failed_evidence = None
    else:
        if token == st.session_state.request_token:
            st.session_state.messages.append({"role": "assistant", "content": answer, "schedule_checked": checked,
                                             "evidence": research_records[-1].to_dict() if research_records else None})
            st.session_state.reply_error = None
            st.session_state.failed_evidence = None
    finally:
        if gateway is not None:
            gateway.close()
            if token == st.session_state.request_token:
                st.session_state.last_permission = gateway.snapshot()
                st.session_state.current_permission = None
    st.rerun()
