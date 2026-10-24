"""Regression checks for form recovery and local work after a chat failure."""

import os
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from agent import ChatError


APP = Path(__file__).resolve().parents[1] / "app.py"


@patch("streamlit.secrets", {})
@patch.dict(os.environ, {"DEEPSEEK_API_KEY": "fictional-offline-key"})
class StudentRecoveryTests(unittest.TestCase):
    def page(self):
        page = AppTest.from_file(str(APP), default_timeout=15).run()
        self.assertFalse(page.exception)
        return page

    @staticmethod
    def button(page, label):
        return next(button for button in page.button if button.label == label)

    def switch(self, page, view):
        control = page.segmented_control(key="workspace_view")
        self.assertFalse(control.disabled)
        control.set_value(view).run()
        self.assertFalse(page.exception)

    def test_invalid_application_keeps_draft_then_success_clears_fields(self):
        page = self.page()
        self.switch(page, "Job tools")
        page.text_input(key="application_company").set_value("Fictional employer")
        page.text_input(key="application_role").set_value("Graduate analyst")
        page.text_input(key="application_deadline").set_value("2026-02-30")
        page.text_area(key="application_notes").set_value("Prepare a portfolio example.")
        self.button(page, "Add record").click().run()
        self.assertFalse(page.exception)
        self.assertTrue(page.warning)
        self.assertEqual(page.session_state.applications, [])
        self.assertEqual(page.text_input(key="application_company").value, "Fictional employer")
        self.assertEqual(page.text_input(key="application_role").value, "Graduate analyst")
        self.assertEqual(page.text_input(key="application_deadline").value, "2026-02-30")
        self.assertEqual(page.text_area(key="application_notes").value, "Prepare a portfolio example.")
        page.text_input(key="application_deadline").set_value("2026-11-30")
        self.button(page, "Add record").click().run()
        self.assertFalse(page.exception)
        self.assertEqual(len(page.session_state.applications), 1)
        self.assertEqual(page.session_state.applications[0].notes, "Prepare a portfolio example.")
        self.assertEqual(page.text_input(key="application_company").value, "")
        self.assertEqual(page.text_input(key="application_role").value, "")
        self.assertEqual(page.text_input(key="application_deadline").value, "")
        self.assertEqual(page.text_area(key="application_notes").value, "")

    @patch("agent.reply", side_effect=[ChatError("Fictional provider failure."), "Try a portfolio exercise."])
    def test_failed_chat_allows_local_work_and_retry_still_requires_click(self, reply):
        page = self.page()
        page.chat_input[0].set_value("Help me find an internship.").run()
        self.assertFalse(page.exception)
        self.assertTrue(page.error)
        self.assertEqual(reply.call_count, 1)
        self.switch(page, "Job tools")
        page.text_area(key="job_description").set_value("需要 Python 和 SQL。")
        self.button(page, "Compare skills").click().run()
        self.assertFalse(page.exception)
        self.assertEqual({row["skill_id"] for row in page.session_state.skill_result}, {"python", "sql"})
        page.text_input(key="application_company").set_value("Fictional employer")
        page.text_input(key="application_role").set_value("Python intern")
        self.button(page, "Add record").click().run()
        self.assertFalse(page.exception)
        self.assertEqual(len(page.session_state.applications), 1)
        self.assertEqual(reply.call_count, 1)
        self.switch(page, "Career chat")
        self.assertTrue(page.error)
        self.assertTrue(page.chat_input[0].disabled)
        self.assertEqual(reply.call_count, 1)
        self.button(page, "Retry Reply").click().run()
        self.assertFalse(page.exception)
        self.assertFalse(page.error)
        self.assertEqual(reply.call_count, 2)
        self.assertEqual(sum(message["role"] == "user" for message in page.session_state.messages), 1)
        self.assertEqual(len(page.session_state.applications), 1)


if __name__ == "__main__":
    unittest.main()
