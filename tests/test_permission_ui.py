"""Permission controls exercised through the real Streamlit request flow."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import httpx2
from streamlit.testing.v1 import AppTest

import agent
import evidence
from permissions import MODEL_RESOURCE, PermissionGateway, SEARCH_RESOURCE
from plan_fixtures import plan_data


APP = Path(__file__).resolve().parents[1] / "app.py"
CHAT_ANSWER = "Compare your transferable skills and career options [S1]."


@contextmanager
def offline_provider(*answers, source_count=1):
    """Keep real search parsing and SDK calls; replace only HTTP transport."""
    requests = []
    remaining_answers = iter(answers or (CHAT_ANSWER,))

    def respond(request):
        endpoint = str(request.url)
        payload = json.loads(request.content)
        requests.append((endpoint, payload))
        if endpoint == SEARCH_RESOURCE:
            return httpx2.Response(200, json={"results": [{
                "title": "Graduate internships and campus recruitment skills",
                "url": f"https://www.ncss.cn/student/example-{index}.html",
                "content": (
                    "China graduate campus recruitment internships skills employment market. "
                    "大学生 校园招聘 实习 应届生 毕业生 就业 技能 岗位 招聘 市场 行情。"
                    "Career change guidance recommends identifying transferable skills, "
                    "comparing career options and writing a skills assessment. Learning "
                    "about work tasks can help plan a practical career exploration."
                ),
                "rerank_score": 2,
                "date": None,
            } for index in range(source_count)]})
        if endpoint == MODEL_RESOURCE:
            return httpx2.Response(200, json={
                "id": "offline-completion", "object": "chat.completion", "created": 0,
                "model": "deepseek-flash",
                "choices": [{"index": 0, "finish_reason": "stop", "message": {
                    "role": "assistant", "content": next(remaining_answers),
                }}],
            })
        raise AssertionError("Unexpected network destination in an offline UI test.")

    def client_factory(**options):
        return httpx2.Client(transport=httpx2.MockTransport(respond), **options)

    with patch.object(agent, "httpx", SimpleNamespace(Client=client_factory)):
        with patch.object(evidence, "httpx", SimpleNamespace(
            Client=client_factory, Timeout=httpx2.Timeout, HTTPError=httpx2.HTTPError,
        )):
            yield requests


@patch("streamlit.secrets", {})
@patch.dict(os.environ, {"DEEPSEEK_API_KEY": "fictional-offline-key"})
class PermissionPageTests(unittest.TestCase):
    def page(self):
        page = AppTest.from_file(str(APP), default_timeout=15).run()
        self.assertFalse(page.exception)
        return page

    def button(self, page, label):
        return next(button for button in page.button if button.label == label)

    def test_control_reruns_never_authorize_work_and_ui_closes_mocked_reply_scope(self):
        issued = []

        def respond(messages, **options):
            gate = options["gateway"]
            self.assertIsInstance(gate, PermissionGateway)
            self.assertTrue(gate.snapshot()["active"])
            issued.append(gate)
            return "A fictional coaching reply."

        with patch("agent.reply", side_effect=respond) as reply:
            page = self.page()
            page.number_input(key="permission_search_limit").set_value(1).run()
            page.number_input(key="permission_model_limit").set_value(1).run()
            page.checkbox(key="permission_online").set_value(False).run()
            page.checkbox(key="permission_online").set_value(True).run()
            reply.assert_not_called()
            self.assertEqual(page.session_state.permission_audit.to_records(), [])
            page.chat_input[0].set_value("I want to explore a career change.").run()
            self.assertFalse(page.exception)
            self.assertEqual(reply.call_count, 1)
            self.assertTrue(issued[0].snapshot()["closed"])
            self.assertIsNone(page.session_state.current_permission)
            self.assertEqual(page.session_state.last_permission["search_limit"], 1)
            page.run()
            page.number_input(key="permission_search_limit").set_value(2).run()
            self.assertEqual(reply.call_count, 1)
            self.assertEqual(len(page.chat_message), 3)

    def test_pause_denies_before_transport_and_only_explicit_retry_gets_new_authority(self):
        with offline_provider(CHAT_ANSWER, source_count=3) as requests:
            page = self.page()
            page.checkbox(key="permission_online").set_value(False).run()
            page.chat_input[0].set_value("I want to explore a career change.").run()
            self.assertFalse(page.exception)
            self.assertTrue(page.error)
            self.assertEqual(requests, [])
            denied = dict(page.session_state.last_permission)
            self.assertTrue(denied["closed"])
            self.assertTrue(denied["revoked"])
            self.assertEqual(denied["search_used"], 0)
            self.assertEqual(denied["model_used"], 0)
            self.assertIn("denied", {row["status"] for row in page.session_state.permission_audit.to_records()})

            page.checkbox(key="permission_online").set_value(True).run()
            page.run()
            self.assertEqual(requests, [])
            self.assertTrue(page.chat_input[0].disabled)
            self.button(page, "Retry Reply").click().run()
            self.assertFalse(page.exception)
            self.assertFalse(page.error)
            self.assertEqual([endpoint for endpoint, _ in requests], [SEARCH_RESOURCE, SEARCH_RESOURCE, MODEL_RESOURCE])
            completed = page.session_state.last_permission
            self.assertNotEqual(completed["request_id"], denied["request_id"])
            self.assertTrue(completed["closed"])
            self.assertTrue(completed["revoked"])
            self.assertEqual(sum(message["role"] == "user" for message in page.session_state.messages), 1)

    def test_selected_limits_bound_actual_plan_correction_and_retry_creates_new_budget(self):
        valid_plan = plan_data()
        valid_plan["summary"] += " [S1]"
        with offline_provider(CHAT_ANSWER, "{}", json.dumps(valid_plan)) as requests:
            page = self.page()
            page.number_input(key="permission_search_limit").set_value(1).run()
            page.number_input(key="permission_model_limit").set_value(1).run()
            page.chat_input[0].set_value("I have retail experience and want a career change.").run()
            self.assertFalse(page.error)
            self.assertEqual(len(requests), 2)
            page.number_input(key="plan_duration").set_value(3).run()
            self.button(page, "Create checked plan").click().run()
            self.assertFalse(page.exception)
            self.assertTrue(page.error)
            failed = dict(page.session_state.last_permission)
            self.assertEqual((failed["search_used"], failed["search_limit"]), (1, 1))
            self.assertEqual((failed["model_used"], failed["model_limit"]), (1, 1))
            self.assertTrue(failed["closed"])
            # The invalid JSON requests a correction, but its second model
            # transport cannot start with the user's one-call authorization.
            self.assertEqual([endpoint for endpoint, _ in requests].count(MODEL_RESOURCE), 2)
            self.assertFalse(any(message.get("schedule_checked") for message in page.session_state.messages))
            page.run()
            self.assertEqual(len(requests), 4)
            self.button(page, "Retry Reply").click().run()
            self.assertFalse(page.exception)
            self.assertFalse(page.error)
            self.assertNotEqual(page.session_state.last_permission["request_id"], failed["request_id"])
            self.assertTrue(page.session_state.messages[-1]["schedule_checked"])
            self.assertEqual([endpoint for endpoint, _ in requests].count(MODEL_RESOURCE), 3)

    def test_new_conversation_clears_audit_and_preserves_permission_preferences(self):
        with offline_provider(CHAT_ANSWER, source_count=3) as requests:
            page = self.page()
            page.number_input(key="permission_search_limit").set_value(1).run()
            page.chat_input[0].set_value("I want to explore a career change.").run()
            self.assertFalse(page.exception)
            old_audit = page.session_state.permission_audit
            self.assertTrue(old_audit.to_records())
            self.button(page, "New Conversation").click().run()
            self.assertFalse(page.exception)
            self.assertEqual(page.session_state.permission_audit.to_records(), [])
            self.assertIsNot(page.session_state.permission_audit, old_audit)
            self.assertIsNone(page.session_state.last_permission)
            self.assertIsNone(page.session_state.current_permission)
            self.assertEqual(page.number_input(key="permission_search_limit").value, 1)
            self.assertEqual(len(page.chat_message), 1)
            self.assertEqual(len(requests), 2)


if __name__ == "__main__":
    unittest.main()
