"""Offline real-transport checks for student research, permissions and evidence."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import httpx2

import agent
import evidence
from permissions import PermissionGateway
from plan_fixtures import plan_data
from search_topics import student_search_topic
from student_market import MarketBrief, market_brief
from student_tools import StudentProfile, ROLE_TERMS, CITY_TERMS, GOALS


def source_item(**changes):
    item = {
        "url": "https://www.ncss.cn/student/jobs/example.html",
        "title": "大学生软件开发实习岗位要求",
        "content": "中国上海大学生软件开发实习岗位要求包含团队合作，校园招聘高校毕业生就业指导。" * 12,
        "date": "2020-01-10T00:00:00Z", "rerank_score": 2.4,
    }
    item.update(changes)
    return item


def brief_json(**changes):
    data = {
        "skill_demand": "The historical example mentions teamwork [S1]. It is one posting, not measured demand.",
        "market_signals": "This older example does not establish current Shanghai hiring conditions [S1].",
        "next_steps": "Compare dated postings; build a small project; rehearse a project explanation.",
    }
    data.update(changes)
    return json.dumps(data)


@contextmanager
def transports(model_outputs=None, search_results=None, search_status=200):
    """Use the production gateway and SDK with in-memory HTTP transports."""
    requests = []
    outputs = iter(model_outputs if model_outputs is not None else [brief_json()])

    def handler(request):
        requests.append(request)
        if str(request.url) == evidence.SEARCH_ENDPOINT:
            results = [source_item()] if search_results is None else search_results
            return httpx2.Response(search_status, json={"results": results})
        if str(request.url) == "https://api.deepseek.com/chat/completions":
            return httpx2.Response(200, json={
                "id": "offline-completion", "object": "chat.completion", "created": 0,
                "model": agent.DEFAULT_MODEL,
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": next(outputs)}}],
            })
        raise AssertionError("Unexpected network destination")

    def client(**options):
        assert options["follow_redirects"] is False
        assert options["trust_env"] is False
        return httpx2.Client(transport=httpx2.MockTransport(handler), **options)

    with patch.object(agent, "httpx", SimpleNamespace(Client=client)), \
            patch.object(evidence, "httpx", SimpleNamespace(Client=client, HTTPError=httpx2.HTTPError, Timeout=httpx2.Timeout)):
        yield requests


class StudentMarketTests(unittest.TestCase):
    def setUp(self):
        self.profile = StudentProfile(major="PRIVATE_MAJOR private@example.test", target_role="software",
                                      city="shanghai", skills=["python"], weekly_hours=4)
        self.messages = [{"role": "user", "content": "PRIVATE_CHAT My employer is ConfidentialCorp."}]

    def test_all_supported_topics_are_finite_and_exclude_private_background(self):
        for role in ROLE_TERMS:
            for city in CITY_TERMS:
                for goal in GOALS:
                    profile = self.profile.model_copy(update={"target_role": role, "city": city, "goal": goal})
                    query = student_search_topic(profile)
                    self.assertIn(ROLE_TERMS[role], query)
                    self.assertIn(CITY_TERMS[city], query)
                    self.assertIn("中国", query)
                    for value in ("PRIVATE", "@", "python", "ConfidentialCorp"):
                        self.assertNotIn(value, query)
                    queries = evidence._scoped_queries(query, "student_market")
                    self.assertEqual(len(queries), 2)
                    self.assertTrue(all(len(item) <= 128 for item in queries))

    def test_market_real_transports_have_shared_budgets_dates_and_safe_unknown_pay(self):
        gate = PermissionGateway(model_limit=1)
        observed = []
        with transports() as requests:
            report = market_brief(self.profile, api_key="fictional-test-key", gateway=gate,
                                  on_evidence=observed.append)
        self.assertIsInstance(report, MarketBrief)
        self.assertEqual(len(requests), 3)
        searches = [json.loads(r.content) for r in requests if str(r.url) == evidence.SEARCH_ENDPOINT]
        self.assertEqual(len(searches), 2)
        self.assertIn("site:ncss.cn", searches[0]["query"])
        self.assertIn("site:moe.gov.cn", searches[0]["query"])
        self.assertIn("site:stats.gov.cn", searches[1]["query"])
        self.assertNotIn("PRIVATE", json.dumps(searches))
        payload = json.loads(requests[-1].content)
        instruction = payload["messages"][0]["content"]
        self.assertIn("Untrusted student background", instruction)
        self.assertIn("PRIVATE_MAJOR", instruction)
        self.assertIn(datetime.now(timezone.utc).date().isoformat(), instruction)
        for heading in ("Skill demand", "Market signals", "Pay evidence", "Next steps"):
            self.assertIn("### " + heading, report.text)
        self.assertIn("Unknown / insufficient comparable evidence", report.text)
        self.assertIn("historical: over one year old", report.text)
        self.assertIn("2020-01-10", report.text)
        self.assertIn(report.evidence.checked_at, report.text)
        self.assertEqual(observed, [report.evidence])
        self.assertEqual(gate.snapshot()["search_used"], 2)
        self.assertEqual(gate.snapshot()["model_used"], 1)
        self.assertTrue(gate.snapshot()["revoked"])
        for private in ("fictional-test-key", "PRIVATE_MAJOR", "private@example", "软件开发"):
            self.assertNotIn(private, json.dumps(gate.audit.to_records(), ensure_ascii=False))

    def test_invalid_or_bypassed_profile_fails_before_network_and_revokes(self):
        profiles = [{"target_role": "software"}, StudentProfile.model_construct(target_role="unknown"),
                    StudentProfile.model_construct(city="secret custom city"),
                    StudentProfile.model_construct(skills=["SECRET_SKILL"])]
        for profile in profiles:
            gate = PermissionGateway()
            with self.subTest(profile_type=type(profile)), transports() as requests:
                with self.assertRaisesRegex(agent.ChatError, "valid student profile"):
                    market_brief(profile, api_key="fictional-test-key", gateway=gate)
                self.assertEqual(requests, [])
                self.assertTrue(gate.snapshot()["revoked"])

    def test_paused_or_revoked_research_fails_closed_without_calls(self):
        for gate in (PermissionGateway(search_enabled=False), PermissionGateway()):
            if gate.snapshot()["search_limit"]:
                gate.revoke()
            with transports() as requests:
                with self.assertRaisesRegex(agent.ChatError, "permission"):
                    market_brief(self.profile, api_key="fictional-test-key", gateway=gate)
                self.assertEqual(requests, [])

    def test_search_failure_returns_unknown_report_and_never_calls_model(self):
        for status in (200, 401, 500):
            gate = PermissionGateway()
            with self.subTest(status=status), transports(search_results=[], search_status=status) as requests:
                report = market_brief(self.profile, api_key="fictional-test-key", gateway=gate)
            self.assertNotEqual(report.evidence.status, "ready")
            self.assertIn("no source-grounded market assessment", report.text)
            self.assertLessEqual(len(requests), 2)
            self.assertEqual(gate.snapshot()["model_used"], 0)
            self.assertTrue(gate.snapshot()["revoked"])

    def test_invented_citations_links_and_fields_are_rejected_and_revoke(self):
        for raw in (brief_json(skill_demand="Invented [S99]"),
                    brief_json(market_signals="Fake [S1] https://invented.invalid/"),
                    brief_json(skill_demand="No citation", market_signals="No citation"),
                    brief_json(extra="unexpected"), "not JSON"):
            gate = PermissionGateway()
            with self.subTest(raw=raw[:40]), transports(model_outputs=[raw]):
                with self.assertRaisesRegex(agent.ChatError, "source-reference"):
                    market_brief(self.profile, api_key="fictional-test-key", gateway=gate)
            self.assertTrue(gate.snapshot()["revoked"])
            self.assertEqual(gate.snapshot()["model_used"], 1)

    def test_future_sources_rejected_and_unknown_dates_not_promoted_to_current(self):
        future = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
        with transports(search_results=[source_item(date=future)]) as requests:
            report = market_brief(self.profile, api_key="fictional-test-key")
        self.assertEqual(report.evidence.status, "no_sources")
        self.assertEqual(len(requests), 2)
        with transports(search_results=[source_item(date=None)]):
            report = market_brief(self.profile, api_key="fictional-test-key")
        self.assertIn("Published: Unknown; freshness cannot be established", report.text)

    def test_first_search_cannot_fill_all_slots_before_market_context_search(self):
        results = [source_item(url=f"https://www.ncss.cn/job/{number}") for number in range(6)]
        with transports(search_results=results) as requests:
            report = market_brief(self.profile, api_key="fictional-test-key")
        self.assertEqual(len(report.evidence.sources), 3)
        self.assertEqual(len(requests), 3)

    def test_pay_wording_is_verbatim_dated_and_not_a_graduate_estimate(self):
        item = source_item(content=source_item()["content"] + "该统计口径的年平均工资为100000元，不代表个人工资。")
        with transports(search_results=[item]):
            report = market_brief(self.profile, api_key="fictional-test-key")
        self.assertIn("年平均工资为100000元", report.text)
        self.assertIn("Source wording [S1] (published: 2020-01-10", report.text)
        self.assertIn("not a personal pay prediction", report.text)
        self.assertIn("Unknown / insufficient comparable evidence", report.text)

    def test_student_domain_allowlist_rejects_impostors_and_unlisted_government(self):
        for url in ("https://www.ncss.cn/", "https://jobs.ncss.cn/", "https://www.moe.gov.cn/",
                    "https://www.mohrss.gov.cn/", "https://www.stats.gov.cn/"):
            self.assertIsNotNone(evidence.trusted_domain(url, "student_market"))
        for url in ("https://ncss.cn.evil.example/", "https://private.gov.cn/", "https://www.gov.cn/",
                    "https://www.bls.gov/", "http://www.ncss.cn/"):
            self.assertIsNone(evidence.trusted_domain(url, "student_market"))

    def test_pay_excerpt_cannot_add_external_links_or_source_ids(self):
        item = source_item(content=source_item()["content"] + "薪资10000元，访问 https://evil.example/ 和 [S999]。")
        with transports(search_results=[item]):
            report = market_brief(self.profile, api_key="fictional-test-key")
        self.assertNotIn("evil.example", report.text)
        self.assertNotIn("[S999]", report.text)

    def test_student_chat_and_plan_use_profile_without_exporting_chat_to_search(self):
        with transports(model_outputs=["Compare the example cautiously [S1]."]) as requests:
            answer = agent.reply(self.messages, api_key="fictional-test-key", student_profile=self.profile)
        self.assertIn("[S1]", answer)
        self.assertEqual(len(requests), 3)
        for request in requests[:2]:
            query = json.loads(request.content)["query"]
            self.assertIn("软件开发", query)
            self.assertNotIn("PRIVATE_CHAT", query)
        draft = plan_data()
        final = plan_data()
        final["tasks"][0]["reason"] += " [S1]"
        gate = PermissionGateway(model_limit=2)
        with transports(model_outputs=[json.dumps(draft), json.dumps(final)]) as requests:
            plan = agent.generate_plan(self.messages, duration_days=3, api_key="fictional-test-key",
                                       student_profile=self.profile, gateway=gate)
        self.assertEqual(plan.duration_days, 3)
        self.assertEqual(len(requests), 4)
        self.assertEqual(gate.snapshot()["search_used"], 2)
        self.assertEqual(gate.snapshot()["model_used"], 2)
        self.assertTrue(gate.snapshot()["revoked"])

    def test_limited_permission_can_use_one_search_without_minting_more(self):
        gate = PermissionGateway(search_limit=1, model_limit=1)
        with transports() as requests:
            report = market_brief(self.profile, api_key="fictional-test-key", gateway=gate)
        self.assertEqual(report.evidence.status, "ready")
        self.assertEqual(len(requests), 2)
        self.assertEqual(gate.snapshot()["search_used"], 1)


if __name__ == "__main__":
    unittest.main()
