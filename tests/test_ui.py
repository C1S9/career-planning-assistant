"""Chat UI checks with simulated replies and no external API calls."""

import os
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from agent import ChatError
from models import CareerPlan
from plan_fixtures import plan_data

APP = Path(__file__).resolve().parents[1] / "app.py"


@patch("streamlit.secrets", {})
class ChatPageTests(unittest.TestCase):
    def page(self):
        page = AppTest.from_file(str(APP), default_timeout=10).run()
        self.assertEqual(len(page.exception), 0)
        return page

    @patch("streamlit.secrets", {})
    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": ""})
    @patch("agent.reply")
    def test_missing_setup_shows_welcome_without_call(self, mocked_reply):
        page = self.page()
        self.assertEqual(len(page.chat_message), 1)
        self.assertTrue(page.chat_input[0].disabled)
        self.assertTrue(page.info)
        mocked_reply.assert_not_called()

    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"})
    @patch("agent.reply", return_value="What would you like to change about your work?")
    def test_context_rerun_and_new_conversation(self, mocked_reply):
        page = self.page()
        page.chat_input[0].set_value("I studied business and work in retail.").run()
        self.assertEqual(len(page.exception), 0)
        self.assertEqual(len(page.chat_message), 3)
        page.chat_input[0].set_value("How could my degree help?").run()
        self.assertEqual(len(page.chat_message), 5)
        history = mocked_reply.call_args.args[0]
        self.assertIn("business", history[1]["content"])
        self.assertEqual(mocked_reply.call_count, 2)
        page.run()
        self.assertEqual(mocked_reply.call_count, 2)
        next(button for button in page.button if button.label == "New Conversation").click().run()
        self.assertEqual(len(page.chat_message), 1)
        page.chat_input[0].set_value("I want to explore a different career.").run()
        history = mocked_reply.call_args.args[0]
        self.assertEqual(len(history), 2)
        self.assertNotIn("business", str(history))

    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"})
    @patch("agent.reply", side_effect=[ChatError("Please retry later."), "Let's explore your next step."])
    def test_retry_preserves_one_user_message(self, mocked_reply):
        page = self.page()
        page.chat_input[0].set_value("I feel uncertain about work.").run()
        self.assertEqual(len(page.exception), 0)
        self.assertEqual(len(page.chat_message), 2)
        self.assertTrue(page.error)
        self.assertTrue(page.chat_input[0].disabled)
        page.run()
        self.assertEqual(mocked_reply.call_count, 1)
        next(button for button in page.button if button.label == "Retry Reply").click().run()
        self.assertEqual(len(page.exception), 0)
        self.assertEqual(len(page.chat_message), 3)
        self.assertEqual(mocked_reply.call_count, 2)
        self.assertEqual(sum(item["role"] == "user" for item in mocked_reply.call_args.args[0]), 1)
        self.assertFalse(page.chat_input[0].disabled)

    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"})
    @patch("agent.reply", return_value="Let's explore your career direction.")
    @patch("agent.generate_plan")
    def test_checked_plan_uses_selected_days_and_context(self, mocked_plan, mocked_reply):
        mocked_plan.return_value = CareerPlan.model_validate(plan_data())
        page = self.page()
        create = next(button for button in page.button if button.label == "Create checked plan")
        self.assertTrue(create.disabled)
        page.chat_input[0].set_value("I studied business and have two years in retail.").run()
        page.number_input[0].set_value(3).run()
        self.assertEqual(mocked_reply.call_count, 1)
        mocked_plan.assert_not_called()
        next(button for button in page.button if button.label == "Create checked plan").click().run()
        self.assertEqual(len(page.exception), 0)
        self.assertEqual(mocked_plan.call_count, 1)
        self.assertEqual(mocked_plan.call_args.kwargs["duration_days"], 3)
        self.assertIn("retail", str(mocked_plan.call_args.args[0]))
        self.assertTrue(any("Task fields and schedule checked" in caption.value for caption in page.caption))
        self.assertIn("3-day action plan", page.chat_message[-1].markdown[0].value)
        page.run()
        self.assertEqual(mocked_plan.call_count, 1)
        self.assertEqual(mocked_reply.call_count, 1)
        next(button for button in page.button if button.label == "New Conversation").click().run()
        self.assertFalse(any("Task fields and schedule checked" in caption.value for caption in page.caption))
        self.assertEqual(page.number_input[0].value, 7)

    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"})
    @patch("agent.reply", return_value="Thanks for sharing your background.")
    @patch("agent.generate_plan")
    def test_failed_plan_is_not_shown_as_checked_and_retry_keeps_its_period(self, mocked_plan, mocked_reply):
        mocked_plan.side_effect = [ChatError("Plan checks failed."), CareerPlan.model_validate(plan_data())]
        page = self.page()
        page.chat_input[0].set_value("I studied business and work in retail.").run()
        page.number_input[0].set_value(3).run()
        next(button for button in page.button if button.label == "Create checked plan").click().run()
        self.assertEqual(len(page.exception), 0)
        self.assertTrue(page.error)
        self.assertFalse(any("Task fields and schedule checked" in caption.value for caption in page.caption))
        page.run()
        self.assertEqual(mocked_plan.call_count, 1)
        next(button for button in page.button if button.label == "Retry Reply").click().run()
        self.assertEqual(len(page.exception), 0)
        self.assertEqual(mocked_plan.call_count, 2)
        self.assertEqual(mocked_plan.call_args.kwargs["duration_days"], 3)
        requests = [item for item in mocked_plan.call_args.args[0] if item["role"] == "user"]
        self.assertEqual(len(requests), 2)
        self.assertEqual(mocked_reply.call_count, 1)


if __name__ == "__main__":
    unittest.main()
