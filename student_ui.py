"""Student workspace widgets; local tools never need a model or a network grant."""

from collections.abc import Callable

import streamlit as st

from student_tools import (
    APPLICATION_STATUSES, CITIES, GOALS, ROLES, SKILLS, STAGES,
    ApplicationEntry, StudentProfile, compare_skills, export_applications,
    import_applications,
)


def initialize_student_state() -> None:
    """Keep durable session data separate from conditionally visible widget keys."""
    for name, default in (
        ("student_profile", StudentProfile()), ("profile_saved", False),
        ("applications", []), ("skill_result", None), ("market_result", None),
        ("market_error", None), ("market_evidence", None),
    ):
        st.session_state.setdefault(name, default)


def render_profile(on_saved: Callable[[], None], *, disabled: bool = False) -> None:
    """Only a submitted, validated profile changes the active conversation."""
    profile = st.session_state.student_profile

    def save() -> None:
        try:
            candidate = StudentProfile(
                major=st.session_state.profile_major,
                stage=st.session_state.profile_stage,
                target_role=st.session_state.profile_role,
                city=st.session_state.profile_city,
                goal=st.session_state.profile_goal,
                skills=st.session_state.profile_skills,
                weekly_hours=st.session_state.profile_hours,
            )
        except ValueError:
            st.session_state.profile_notice = "Check your profile fields and try again."
            return
        if candidate != st.session_state.student_profile:
            on_saved()
            st.session_state.market_result = None
            st.session_state.market_error = None
            st.session_state.market_evidence = None
            st.session_state.skill_result = None
        st.session_state.student_profile = candidate
        st.session_state.profile_saved = True
        st.session_state.profile_notice = "Profile saved. Changed details start a fresh conversation."

    with st.expander("Your student profile", expanded=not st.session_state.profile_saved,
                     icon=":material/school:"):
        st.caption("Mainland China · campus recruitment and internships")
        with st.form("student_profile_form"):
            st.text_input("Major or field of study", value=profile.major, max_chars=120,
                          key="profile_major", disabled=disabled)
            st.selectbox("Study stage", STAGES, index=STAGES.index(profile.stage),
                         key="profile_stage", disabled=disabled)
            st.selectbox("Target role", tuple(ROLES), index=list(ROLES).index(profile.target_role),
                         format_func=ROLES.get, key="profile_role", disabled=disabled)
            st.selectbox("Target city", tuple(CITIES), index=list(CITIES).index(profile.city),
                         format_func=CITIES.get, key="profile_city", disabled=disabled)
            st.selectbox("Job search goal", GOALS, index=GOALS.index(profile.goal),
                         key="profile_goal", disabled=disabled)
            st.multiselect("Skills you have practiced", tuple(SKILLS), default=profile.skills,
                           format_func=SKILLS.get, key="profile_skills", disabled=disabled)
            st.number_input("Preparation hours per week", min_value=1, max_value=40,
                            value=profile.weekly_hours, step=1, key="profile_hours", disabled=disabled)
            st.form_submit_button("Save profile", on_click=save, disabled=disabled, width="stretch")
        st.caption("Online advice shares this profile with DeepSeek. Search uses only preset role, city and goal terms. Avoid contact details or other sensitive information.")
        if st.session_state.get("profile_notice"):
            st.caption(st.session_state.profile_notice)


def export_advice(text: str, evidence: dict | None) -> str:
    """Keep source records with a downloaded plan or brief; never include credentials."""
    result = text + "\n\n---\nGenerated guidance; review facts and suitability before acting.\n"
    if evidence:
        result += f"\nSources retrieved: {evidence.get('checked_at', 'Unknown')} (UTC)\n"
        for source in evidence.get("sources", []):
            result += f"\n[{source['id']}] {source['url']}\nPublication date: {source.get('published_date') or 'Unknown'}\n"
    return result


def render_skill_comparison() -> None:
    st.subheader("Compare a job description")
    st.caption("Paste a Chinese or English job description. This local tool finds skill mentions and compares them with your saved profile; it does not score your chances of being hired.")
    with st.form("skill_compare_form"):
        job_text = st.text_area("Job description", max_chars=12000, height=170,
                                key="job_description", persist_state="session")
        submitted = st.form_submit_button("Compare skills", type="primary")
    if submitted:
        try:
            rows = compare_skills(job_text, st.session_state.student_profile.skills)
        except ValueError:
            st.warning("Paste a job description of up to 12,000 characters and check your saved skills.")
        else:
            st.session_state.skill_result = rows
    rows = st.session_state.skill_result
    if rows is not None:
        st.caption("Last submitted comparison. A mention may be optional or negated; read its original context. Your selected skills are self-reported.")
        if not rows:
            st.info("No supported skill terms were found. Read the role requirements manually; the catalog is intentionally limited.")
        else:
            view = [{"Skill": row["skill"], "Your profile": "Practiced" if row["declared"] else "Not selected",
                     "Posting excerpt": row["evidence"], "Practice idea": row["practice"]} for row in rows]
            st.dataframe(view, hide_index=True, width="stretch", alt="Skills mentioned in the submitted job description, with practice ideas")


def render_application_tracker() -> None:
    if st.session_state.pop("application_added", False):
        # Clear a successfully saved draft before creating its widgets. Invalid
        # drafts stay intact so a typo never destroys the student's work.
        for field in ("company", "role", "city", "url", "deadline", "notes"):
            st.session_state[f"application_{field}"] = ""
        st.session_state.application_status = APPLICATION_STATUSES[0]
        st.success("Application added.")
    st.subheader("Track applications")
    st.caption("Records stay in this session and are not sent to DeepSeek. Download a CSV before closing or refreshing the app; import it next time. Up to 200 records.")
    with st.expander("Add an application", icon=":material/add:"):
        with st.form("application_add"):
            company = st.text_input("Company", max_chars=120, key="application_company")
            role = st.text_input("Role", max_chars=120, key="application_role")
            city = st.text_input("City", max_chars=80, key="application_city")
            url = st.text_input("Posting URL (optional, HTTPS)", max_chars=2048, key="application_url")
            deadline = st.text_input("Deadline (optional, YYYY-MM-DD)", max_chars=10, key="application_deadline")
            status = st.selectbox("Status", APPLICATION_STATUSES, key="application_status")
            notes = st.text_area("Next step or notes", max_chars=500, key="application_notes")
            add = st.form_submit_button("Add record")
        if add:
            try:
                entry = ApplicationEntry(company=company, role=role, city=city, job_url=url,
                                         deadline=deadline, status=status, notes=notes)
                if len(st.session_state.applications) >= 200:
                    raise ValueError("Limit")
            except ValueError:
                st.warning("Check company, role, date and HTTPS URL, and keep the tracker below 200 records.")
            else:
                st.session_state.applications = [*st.session_state.applications, entry]
                st.session_state.application_added = True
                st.rerun()

    entries = st.session_state.applications
    if entries:
        st.dataframe([{"Company": e.company, "Role": e.role, "City": e.city,
                       "Status": e.status, "Deadline": e.deadline, "Next step": e.notes,
                       "Posting URL": e.job_url} for e in entries], hide_index=True,
                     width="stretch", alt="Your saved application records for this session")
        with st.expander("Update or remove a record"):
            by_id = {entry.id: entry for entry in entries}
            chosen = st.selectbox("Application", tuple(by_id), key="application_selected",
                                 format_func=lambda value: f"{by_id[value].company} · {by_id[value].role} · {value[:8]}")
            selected = by_id[chosen]
            with st.form(f"application_update_{chosen}"):
                updated_status = st.selectbox("Updated status", APPLICATION_STATUSES,
                                              index=APPLICATION_STATUSES.index(selected.status))
                updated_notes = st.text_area("Updated next step", value=selected.notes, max_chars=500)
                update = st.form_submit_button("Save record changes")
            if update:
                try:
                    replacement = ApplicationEntry.model_validate({**selected.model_dump(),
                                                                  "status": updated_status, "notes": updated_notes})
                except ValueError:
                    st.warning("Check the status and notes and try again.")
                else:
                    st.session_state.applications = [replacement if e.id == chosen else e for e in entries]
                    st.rerun()
            if st.button("Remove selected record", key="application_remove"):
                st.session_state.applications = [entry for entry in entries if entry.id != chosen]
                st.rerun()
    else:
        st.info("Add your first target role, or import a previously downloaded tracker.")
    st.download_button("Download application CSV", export_applications(entries),
                       file_name="graduate-applications.csv", mime="text/csv", on_click="ignore")
    with st.expander("Import a tracker CSV"):
        uploaded = st.file_uploader("Application CSV (up to 3 MB)", type="csv", max_upload_size=3,
                                    key="application_import_file")
        st.caption("Import replaces the current session's records. Download them first if you want to keep a separate copy.")
        if st.button("Replace records with CSV", disabled=uploaded is None):
            try:
                incoming = import_applications(uploaded.getvalue())
            except (ValueError, AttributeError):
                st.warning("The CSV could not be read. Use an exported tracker with valid fields, up to 200 records and 3 MB.")
            else:
                st.session_state.applications = incoming
                st.rerun()
