"""Prove that mentor selection changes requests without sharing prior context."""

import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from agent import ChatError, generate_plan, reply
from mentors import MENTORS, get_mentor
from plan_fixtures import plan_data

APP = Path(__file__).resolve().parents[1] / "app.py"


class MentorRequestTests(unittest.TestCase):
    @patch("agent._complete", return_value="Let's choose a manageable next step.")
    def test_each_mentor_reaches_the_chat_system_message(self, complete):
        messages = [{"role": "user", "content": "Help me clarify my next step."}]
        for mentor_id, mentor in MENTORS.items():
            with self.subTest(mentor=mentor_id):
                reply(messages, api_key="test-key", mentor_id=mentor_id)
                instruction = complete.call_args.args[0][0]["content"]
                self.assertIn(mentor.name, instruction)
                self.assertIn(mentor.instructions, instruction)
                self.assertEqual(complete.call_args.args[0][1:], messages)

    @patch("agent._complete")
    def test_checked_plans_use_the_selected_mentor_and_period(self, complete):
        complete.return_value = json.dumps(plan_data())
        generate_plan([{"role": "user", "content": "I can study for 30 minutes a day."}], duration_days=3, api_key="test-key", mentor_id="learning")
        instruction = complete.call_args.args[0][0]["content"]
        self.assertIn(MENTORS["learning"].instructions, instruction)
        self.assertIn("exactly 3 days", instruction)
        self.assertTrue(complete.call_args.kwargs["json_mode"])

    @patch("agent._complete")
    def test_unknown_mentor_stops_before_a_paid_request(self, complete):
        for call in (
            lambda: reply([{"role": "user", "content": "hello"}], api_key="test-key", mentor_id="missing"),
            lambda: generate_plan([{"role": "user", "content": "hello"}], duration_days=3, api_key="test-key", mentor_id="missing"),
        ):
            with self.assertRaises(ChatError):
                call()
        complete.assert_not_called()


@patch("streamlit.secrets", {})
class MentorPageTests(unittest.TestCase):
    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"})
    @patch("agent.reply", return_value="What would you like to explore?")
    def test_switching_mentors_resets_context_without_a_request(self, mocked_reply):
        page = AppTest.from_file(str(APP)).run()
        page.chat_input[0].set_value("I have private career context.").run()
        page.number_input[0].set_value(90).run()
        page.selectbox(key="mentor_choice").set_value("relationships").run()
        self.assertFalse(page.exception)
        self.assertEqual(len(page.chat_message), 1)
        self.assertEqual(page.chat_message[0].markdown[0].value, get_mentor("relationships").welcome)
        self.assertEqual(page.number_input[0].value, 7)
        self.assertEqual(mocked_reply.call_count, 1)
        page.chat_input[0].set_value("I want to prepare a conversation.").run()
        self.assertEqual(mocked_reply.call_args.kwargs["mentor_id"], "relationships")
        self.assertNotIn("private career context", str(mocked_reply.call_args.args[0]))

    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"})
    @patch("agent.reply", side_effect=ChatError("Please retry later."))
    def test_switching_after_failure_does_not_retry_the_old_request(self, mocked_reply):
        page = AppTest.from_file(str(APP)).run()
        page.chat_input[0].set_value("A concern.").run()
        self.assertTrue(page.error)
        page.selectbox(key="mentor_choice").set_value("habits").run()
        self.assertFalse(page.exception)
        self.assertFalse(page.error)
        self.assertEqual(mocked_reply.call_count, 1)
        self.assertFalse(page.chat_input[0].disabled)

    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": ""})
    @patch("agent.reply", return_value="Let's explore your goal.")
    def test_password_entry_enables_session_and_never_enters_transcript(self, mocked_reply):
        page = AppTest.from_file(str(APP)).run()
        self.assertTrue(page.chat_input[0].disabled)
        page.text_input(key="connection_key").set_value("test-session-credential")
        next(button for button in page.button if button.label == "Use for this session").click().run()
        self.assertFalse(page.exception)
        self.assertFalse(page.chat_input[0].disabled)
        self.assertEqual(page.text_input(key="connection_key").value, "")
        page.chat_input[0].set_value("I would like a manageable learning goal.").run()
        self.assertEqual(mocked_reply.call_args.kwargs["api_key"], "test-session-credential")
        self.assertNotIn("test-session-credential", str(mocked_reply.call_args.args[0]))
        next(button for button in page.button if button.label == "Forget session key").click().run()
        self.assertFalse(page.exception)
        self.assertTrue(page.chat_input[0].disabled)

    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"})
    def test_new_conversation_keeps_the_selected_mentor(self):
        page = AppTest.from_file(str(APP)).run()
        page.selectbox(key="mentor_choice").set_value("learning").run()
        next(button for button in page.button if button.label == "New Conversation").click().run()
        self.assertFalse(page.exception)
        self.assertEqual(page.selectbox(key="mentor_choice").value, "learning")
        self.assertEqual(page.chat_message[0].markdown[0].value, get_mentor("learning").welcome)


if __name__ == "__main__":
    unittest.main()
