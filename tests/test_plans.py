"""Check schedule rules and correction limits without contacting DeepSeek."""

from copy import deepcopy
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from openai import APIConnectionError

from agent import ChatError, generate_plan
from models import PlanValidationError, format_plan, parse_plan
from plan_fixtures import plan_data


def completion(data):
    raw = data if isinstance(data, str) else json.dumps(data)
    return SimpleNamespace(choices=[
        SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=raw))
    ])


class PlanRulesTests(unittest.TestCase):
    def test_supported_periods_are_valid(self):
        for days in (1, 3, 7, 90, 365):
            with self.subTest(days=days):
                plan = parse_plan(json.dumps(plan_data(days)), expected_days=days)
                self.assertEqual(plan.duration_days, days)
                self.assertIn(f"{days}-day action plan", format_plan(plan))

    def test_invalid_task_counts_are_rejected(self):
        for count in (0, 2, 9):
            data = plan_data()
            data["tasks"] = [deepcopy(data["tasks"][0]) for _ in range(count)]
            with self.subTest(count=count), self.assertRaises(PlanValidationError):
                parse_plan(json.dumps(data), expected_days=3)

    def test_days_must_be_ordered_and_within_period(self):
        cases = [
            ("zero", 0, 1), ("reversed", 2, 1), ("outside", 3, 4),
            ("string", "2", 2), ("boolean", True, 2),
        ]
        for name, start, end in cases:
            data = plan_data()
            data["tasks"][1].update(start_day=start, end_day=end)
            with self.subTest(name=name), self.assertRaises(PlanValidationError):
                parse_plan(json.dumps(data), expected_days=3)

    def test_day_one_and_sorted_start_days_are_required(self):
        data = plan_data()
        data["tasks"][0].update(start_day=2, end_day=2)
        with self.assertRaises(PlanValidationError):
            parse_plan(json.dumps(data), expected_days=3)
        data = plan_data()
        data["tasks"][1], data["tasks"][2] = data["tasks"][2], data["tasks"][1]
        with self.assertRaises(PlanValidationError):
            parse_plan(json.dumps(data), expected_days=3)

    def test_model_cannot_substitute_its_own_period(self):
        with self.assertRaises(PlanValidationError):
            parse_plan(json.dumps(plan_data(7)), expected_days=3)

    def test_required_fields_and_json_are_checked_without_echoing_values(self):
        data = plan_data()
        data["tasks"][0]["action"] = "   "
        with self.assertRaises(PlanValidationError):
            parse_plan(json.dumps(data), expected_days=3)
        data = plan_data()
        del data["tasks"][0]["completion_criterion"]
        with self.assertRaises(PlanValidationError):
            parse_plan(json.dumps(data), expected_days=3)
        with self.assertRaises(PlanValidationError) as caught:
            parse_plan("PRIVATE-INVALID-OUTPUT", expected_days=3)
        self.assertNotIn("PRIVATE", str(caught.exception))


class PlanWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.messages = [{"role": "user", "content": "I studied business, work in retail, and want a short plan."}]

    @patch("agent.OpenAI")
    def test_valid_plan_takes_one_request_with_history_and_json_mode(self, factory):
        client = factory.return_value.__enter__.return_value
        client.chat.completions.create.return_value = completion(plan_data())
        plan = generate_plan(self.messages, duration_days=3, api_key="test-key")
        self.assertEqual(plan.duration_days, 3)
        self.assertEqual(client.chat.completions.create.call_count, 1)
        args = client.chat.completions.create.call_args.kwargs
        self.assertEqual(args["response_format"], {"type": "json_object"})
        self.assertEqual(args["messages"][1:], self.messages)

    @patch("agent.OpenAI")
    def test_invalid_schedule_is_regenerated_once(self, factory):
        bad = plan_data()
        bad["tasks"][2]["end_day"] = 8
        client = factory.return_value.__enter__.return_value
        client.chat.completions.create.side_effect = [completion(bad), completion(plan_data())]
        plan = generate_plan(self.messages, duration_days=3, api_key="test-key")
        self.assertEqual(plan.duration_days, 3)
        self.assertEqual(client.chat.completions.create.call_count, 2)
        second = client.chat.completions.create.call_args.kwargs["messages"][0]["content"]
        self.assertIn("previous attempt failed validation", second)

    @patch("agent.OpenAI")
    def test_two_invalid_plans_stop_with_safe_failure(self, factory):
        client = factory.return_value.__enter__.return_value
        client.chat.completions.create.return_value = completion("PRIVATE-BROKEN-OUTPUT")
        with self.assertRaises(ChatError) as caught:
            generate_plan(self.messages, duration_days=3, api_key="test-key")
        self.assertEqual(client.chat.completions.create.call_count, 2)
        self.assertNotIn("PRIVATE", str(caught.exception))

    @patch("agent.OpenAI")
    def test_connection_failure_does_not_trigger_correction(self, factory):
        client = factory.return_value.__enter__.return_value
        client.chat.completions.create.side_effect = APIConnectionError(request=Mock())
        with self.assertRaises(ChatError):
            generate_plan(self.messages, duration_days=3, api_key="test-key")
        self.assertEqual(client.chat.completions.create.call_count, 1)

    @patch("agent.OpenAI")
    def test_invalid_selected_period_never_calls_provider(self, factory):
        for days in (0, 366, True, 3.0):
            with self.subTest(days=days), self.assertRaises(ChatError):
                generate_plan(self.messages, duration_days=days, api_key="test-key")
        factory.assert_not_called()
