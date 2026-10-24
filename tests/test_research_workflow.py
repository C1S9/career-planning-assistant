"""Prove that retrieval, source identities, and privacy constrain real requests."""

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from agent import ChatError, generate_plan, reply
from evidence_fixtures import no_evidence, ready_evidence
from plan_fixtures import plan_data
from references import ReferenceError, validate_references
from search_topics import REGIONS, search_topic


class ResearchWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.messages = [{"role": "user", "content": "My name is PRIVATE_NAME, private@example.net. I work in retail and want to change careers."}]

    @patch("agent._complete", return_value="Compare your transferable skills with options [S1].")
    @patch("agent.retrieve_evidence", return_value=ready_evidence())
    def test_search_precedes_answer_and_private_text_never_enters_query(self, research, complete):
        events = []
        research.side_effect = lambda *a, **kw: events.append("search") or ready_evidence()
        complete.side_effect = lambda *a, **kw: events.append("answer") or "Compare options [S1]."
        records = []
        reply(self.messages, api_key="synthetic-key", on_evidence=records.append)
        self.assertEqual(events, ["search", "answer"])
        query = research.call_args.args[0]
        self.assertNotIn("PRIVATE", query)
        self.assertNotIn("@", query)
        self.assertIn("career change", query)
        instruction = complete.call_args.args[0][0]["content"]
        self.assertIn(ready_evidence().sources[0].excerpt, instruction)
        self.assertEqual(len(records), 1)

    @patch("agent._complete")
    @patch("agent.retrieve_evidence", return_value=no_evidence())
    def test_failure_only_clarifies_and_never_generates_advice_or_plan(self, research, complete):
        answer = reply(self.messages, api_key="synthetic-key")
        self.assertIn("could not retrieve", answer)
        with self.assertRaisesRegex(ChatError, "not generated"):
            generate_plan(self.messages, duration_days=3, api_key="synthetic-key")
        complete.assert_not_called()

    @patch("agent._complete")
    @patch("agent.retrieve_evidence", return_value=ready_evidence())
    def test_plan_correction_reuses_one_retrieval(self, research, complete):
        plan = plan_data()
        cited = plan_data()
        cited["tasks"][0]["reason"] += " [S1]"
        complete.side_effect = [json.dumps(plan), json.dumps(cited)]
        generate_plan(self.messages, duration_days=3, api_key="synthetic-key")
        self.assertEqual(research.call_count, 1)
        self.assertEqual(complete.call_count, 2)

    @patch("agent._complete", return_value="Try this fake resource [S99].")
    @patch("agent.retrieve_evidence", return_value=ready_evidence())
    def test_invented_reference_is_not_displayable(self, research, complete):
        with self.assertRaisesRegex(ChatError, "source-reference"):
            reply(self.messages, api_key="synthetic-key")

    @patch("agent._complete")
    @patch("agent.retrieve_evidence")
    def test_invalid_input_and_region_never_search(self, research, complete):
        with self.assertRaises(ChatError):
            reply(self.messages, api_key="synthetic-key", source_region="private custom location")
        with self.assertRaises(ChatError):
            generate_plan(self.messages, duration_days=3, api_key=" ")
        research.assert_not_called()
        complete.assert_not_called()

    def test_urls_and_source_ids_must_match_actual_retrieval(self):
        bundle = ready_evidence()
        validate_references("Compare options [S1].", bundle)
        for text in ("No citation.", "Unknown [S999]", "[S1] https://invented.invalid/advice",
                     "[S1] [click](javascript:alert(1))", "[S1] [click](//evil.invalid)"):
            with self.subTest(text=text), self.assertRaises(ReferenceError):
                validate_references(text, bundle)

    def test_finite_queries_support_chinese_and_explicit_regions(self):
        messages = [{"role": "user", "content": "私人名字，上海，公司A，我想转行。"}]
        self.assertEqual(search_topic(messages, "career"), "career change transferable skills")
        self.assertNotIn("Shanghai", search_topic(messages, "career"))
        for region in REGIONS:
            self.assertLessEqual(len(search_topic(messages, "career", region)), 90)


@patch("streamlit.secrets", {})
class ResearchPageTests(unittest.TestCase):
    @patch.dict(os.environ, {"DEEPSEEK_API_KEY": "synthetic-key"})
    @patch("agent._complete", return_value="Compare your skills and options [S1].")
    @patch("agent.retrieve_evidence", return_value=ready_evidence())
    def test_actual_request_displays_real_sources_and_reruns_do_not_search(self, research, complete):
        app = Path(__file__).resolve().parents[1] / "app.py"
        page = AppTest.from_file(str(app), default_timeout=10).run()
        page.chat_input[0].set_value("I want to compare career options.").run()
        self.assertFalse(page.exception)
        self.assertTrue(any(x.label == "Sources consulted" for x in page.expander))
        self.assertTrue(any("Identify skills" in x.value for x in page.text))
        record = page.session_state.messages[-1]["evidence"]
        self.assertEqual(record["sources"][0]["url"], ready_evidence().sources[0].url)
        page.run()
        page.selectbox(key="profile_city").set_value("shanghai")
        next(button for button in page.button if button.label == "Save profile").click().run()
        self.assertEqual(research.call_count, 1)
        self.assertEqual(complete.call_count, 1)


if __name__ == "__main__":
    unittest.main()
