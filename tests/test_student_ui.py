"""Exercise student workflows and their network boundaries through the real page."""

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from agent import ChatError
from models import CareerPlan
from permissions import MODEL_RESOURCE, SEARCH_RESOURCE
from student_market import MarketBrief
from student_tools import ApplicationEntry, export_applications
from evidence_fixtures import ready_evidence
from plan_fixtures import plan_data
from test_permission_ui import offline_provider

APP = Path(__file__).resolve().parents[1] / "app.py"
BRIEF = "## Skill demand\nCompare posting requirements [S1].\n## Market signals\nInsufficient evidence.\n## Pay evidence\nNot available.\n## Next steps\nRead original postings [S1]."
BRIEF_JSON = json.dumps({"skill_demand": "Compare posting requirements [S1].",
                         "market_signals": "Insufficient local evidence.",
                         "next_steps": "Read original postings [S1]."})


@patch("streamlit.secrets", {})
@patch.dict(os.environ, {"DEEPSEEK_API_KEY": "fictional-offline-key"})
class StudentPageTests(unittest.TestCase):
    def page(self):
        page = AppTest.from_file(str(APP), default_timeout=15).run()
        self.assertFalse(page.exception)
        return page

    def button(self, page, label):
        return next(button for button in page.button if button.label == label)

    def view(self, page, value):
        page.segmented_control(key="workspace_view").set_value(value).run()
        self.assertFalse(page.exception)

    @patch("agent.reply", return_value="Consider a small portfolio exercise.")
    def test_profile_is_saved_explicitly_and_changed_context_starts_fresh(self, reply):
        page = self.page()
        page.chat_input[0].set_value("Old private background.").run()
        page.text_input(key="profile_major").set_value("Computer science")
        page.selectbox(key="profile_role").set_value("software")
        page.multiselect(key="profile_skills").set_value(["python", "git"])
        self.button(page, "Save profile").click().run()
        self.assertFalse(page.exception)
        self.assertEqual(len(page.chat_message), 1)
        self.assertEqual(reply.call_count, 1)
        page.chat_input[0].set_value("How can I prepare for an internship?").run()
        profile = reply.call_args.kwargs["student_profile"]
        self.assertEqual(profile.major, "Computer science")
        self.assertEqual(profile.skills, ["python", "git"])
        self.assertNotIn("Old private background", str(reply.call_args.args[0]))
        self.button(page, "New Conversation").click().run()
        self.assertEqual(page.session_state.student_profile, profile)

    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": ""})
    @patch("agent._provider_complete")
    @patch("evidence._search")
    def test_tools_work_without_credentials_and_never_call_network(self, search, complete):
        page = self.page()
        self.view(page, "Job tools")
        page.text_area(key="job_description").set_value("实习岗位：需要 Python 和 SQL；团队协作，JavaScript 加分。")
        self.button(page, "Compare skills").click().run()
        self.assertFalse(page.exception)
        rows = page.session_state.skill_result
        self.assertIn("python", {row["skill_id"] for row in rows})
        self.assertNotIn("java", {row["skill_id"] for row in rows})
        page.text_input(key="application_company").set_value("Fictional employer")
        page.text_input(key="application_role").set_value("Data intern")
        page.text_input(key="application_deadline").set_value("2026-11-30")
        self.button(page, "Add record").click().run()
        self.assertFalse(page.exception)
        self.assertEqual(len(page.session_state.applications), 1)
        self.view(page, "Career chat")
        self.button(page, "New Conversation").click().run()
        self.view(page, "Job tools")
        self.assertEqual(len(page.session_state.applications), 1)
        search.assert_not_called()
        complete.assert_not_called()

    def test_csv_import_is_explicit_and_invalid_file_preserves_records(self):
        page = self.page()
        self.view(page, "Job tools")
        entry = ApplicationEntry(company="Fictional employer", role="Graduate analyst")
        data = export_applications([entry])
        page.file_uploader[0].set_value(("tracker.csv", data, "text/csv")).run()
        self.assertEqual(page.session_state.applications, [])
        self.button(page, "Replace records with CSV").click().run()
        self.assertFalse(page.exception)
        self.assertEqual(page.session_state.applications, [entry])
        page.file_uploader[0].set_value(("bad.csv", b"wrong,fields\n=CMD(),x\n", "text/csv")).run()
        self.button(page, "Replace records with CSV").click().run()
        self.assertTrue(page.warning)
        self.assertEqual(page.session_state.applications, [entry])
        self.button(page, "Remove selected record").click().run()
        self.assertFalse(page.exception)
        self.assertEqual(page.session_state.applications, [])

    def test_market_uses_real_bounded_transport_and_reruns_do_not_repeat(self):
        with offline_provider(BRIEF_JSON, source_count=3) as requests:
            page = self.page()
            self.view(page, "Market brief")
            self.assertEqual(requests, [])
            self.button(page, "Generate market brief").click().run()
            self.assertFalse(page.exception)
            self.assertFalse(page.error)
            self.assertEqual([endpoint for endpoint, _ in requests], [SEARCH_RESOURCE, SEARCH_RESOURCE, MODEL_RESOURCE])
            self.assertTrue(page.session_state.last_permission["closed"])
            self.assertIn("Compare posting requirements [S1].", page.session_state.market_result)
            page.run()
            self.view(page, "Job tools")
            self.view(page, "Market brief")
            self.assertEqual(len(requests), 3)
            page.text_input(key="profile_major").set_value("Business")
            self.button(page, "Save profile").click().run()
            self.assertIsNone(page.session_state.market_result)
            self.assertEqual(len(requests), 3)

    def test_paused_market_is_denied_before_any_transport(self):
        with offline_provider(BRIEF) as requests:
            page = self.page()
            page.checkbox(key="permission_online").set_value(False).run()
            self.view(page, "Market brief")
            self.button(page, "Generate market brief").click().run()
            self.assertFalse(page.exception)
            self.assertTrue(page.error)
            self.assertEqual(requests, [])
            self.assertTrue(page.session_state.last_permission["closed"])
            page.checkbox(key="permission_online").set_value(True).run()
            self.assertEqual(requests, [])

    @patch("student_market.market_brief")
    def test_failed_refresh_removes_previous_success(self, brief):
        brief.side_effect = [MarketBrief(BRIEF, ready_evidence()), ChatError("Sources unavailable.")]
        page = self.page()
        self.view(page, "Market brief")
        self.button(page, "Generate market brief").click().run()
        self.assertTrue(page.session_state.market_result)
        self.button(page, "Generate market brief").click().run()
        self.assertFalse(page.exception)
        self.assertIsNone(page.session_state.market_result)
        self.assertTrue(page.error)

    @patch("agent.reply", return_value="Consider comparing two internships.")
    @patch("agent.generate_plan", return_value=CareerPlan.model_validate(plan_data()))
    def test_plan_started_from_tools_returns_to_chat_and_can_be_downloaded(self, plan, reply):
        page = self.page()
        page.chat_input[0].set_value("I have three days to explore data internships.").run()
        self.view(page, "Job tools")
        page.number_input(key="plan_duration").set_value(3).run()
        self.button(page, "Create checked plan").click().run()
        self.assertFalse(page.exception)
        self.assertEqual(page.session_state.workspace_view, "Career chat")
        self.assertEqual(plan.call_count, 1)
        self.assertTrue(any(button.label == "Download action plan" for button in page.download_button))


if __name__ == "__main__":
    unittest.main()
