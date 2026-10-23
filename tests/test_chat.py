"""Provider-independent checks for the chat boundary."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from openai import APIConnectionError, APIStatusError

from agent import BASE_URL, ChatError, MAX_HISTORY_CHARS, reply, validate_history
from prompts import SYSTEM_PROMPT
from evidence_fixtures import ready_evidence


def result(content="What would you like to change about your work? [S1]", finish="stop"):
    return SimpleNamespace(
        choices=[SimpleNamespace(finish_reason=finish, message=SimpleNamespace(content=content))]
    )


class ChatBoundaryTests(unittest.TestCase):
    def setUp(self):
        research = patch("agent.retrieve_evidence", return_value=ready_evidence())
        research.start()
        self.addCleanup(research.stop)
        self.messages = [
            {"role": "user", "content": "I studied business."},
            {"role": "assistant", "content": "What work have you done?"},
            {"role": "user", "content": "Two years in retail."},
        ]

    @patch("agent.OpenAI")
    def test_prior_context_and_instructions_reach_deepseek(self, factory):
        client = factory.return_value.__enter__.return_value
        client.chat.completions.create.return_value = result()
        answer = reply(self.messages, api_key="test-key")
        kwargs = client.chat.completions.create.call_args.kwargs
        self.assertTrue(kwargs["messages"][0]["content"].startswith(SYSTEM_PROMPT))
        self.assertEqual(kwargs["messages"][1:], self.messages)
        self.assertEqual(factory.call_args.kwargs["base_url"], BASE_URL)
        self.assertEqual(factory.call_args.kwargs["max_retries"], 0)
        self.assertTrue(answer)
        self.assertEqual(len(self.messages), 3)

    @patch("agent.OpenAI")
    def test_invalid_input_never_contacts_provider(self, factory):
        for content in (" ", "x" * 4_001):
            with self.subTest(length=len(content)), self.assertRaises(ChatError):
                reply([{"role": "user", "content": content}], api_key="test-key")
        factory.assert_not_called()

    def test_conversation_limits_are_explicit(self):
        with self.assertRaises(ChatError):
            validate_history([{"role": "user", "content": "hello"}] * 41)
        with self.assertRaises(ChatError):
            validate_history([
                {"role": "assistant", "content": "x" * MAX_HISTORY_CHARS},
                {"role": "user", "content": "hello"},
            ])

    @patch("agent.OpenAI")
    def test_empty_or_incomplete_reply_is_not_success(self, factory):
        client = factory.return_value.__enter__.return_value
        for response in (result(" "), result("partial", "length"), SimpleNamespace(choices=[])):
            with self.subTest(response=response), self.assertRaises(ChatError):
                client.chat.completions.create.return_value = response
                reply(self.messages, api_key="test-key")

    @patch("agent.OpenAI")
    def test_connection_failure_is_safe_and_not_retried(self, factory):
        client = factory.return_value.__enter__.return_value
        client.chat.completions.create.side_effect = APIConnectionError(request=Mock())
        with self.assertRaisesRegex(ChatError, "Could not reach"):
            reply(self.messages, api_key="secret-test-value")
        self.assertEqual(client.chat.completions.create.call_count, 1)

    @patch("agent.OpenAI")
    def test_provider_body_is_not_exposed(self, factory):
        client = factory.return_value.__enter__.return_value
        response = Mock(status_code=401, headers={})
        client.chat.completions.create.side_effect = APIStatusError(
            "private server content", response=response, body={"secret": "private-value"}
        )
        with self.assertRaises(ChatError) as caught:
            reply(self.messages, api_key="test-key")
        self.assertIn("access was denied", str(caught.exception))
        self.assertNotIn("private", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
