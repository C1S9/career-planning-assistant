"""Real authorization invariants without networking or paid API calls."""

from concurrent.futures import ThreadPoolExecutor
import json
from threading import Lock
import unittest
from unittest.mock import Mock, patch
from uuid import UUID

from permissions import (
    AuditTrail, MODEL_RESOURCE, PermissionDenied, PermissionGateway, SEARCH_RESOURCE,
)


class PermissionTests(unittest.TestCase):
    def search(self, gate, operation=lambda: "result", **overrides):
        arguments = dict(resource=SEARCH_RESOURCE, data_class="public_topic", operation=operation)
        arguments.update(overrides)
        return gate.run("web.search", **arguments)

    def model(self, gate, operation=lambda: "answer", **overrides):
        arguments = dict(resource=MODEL_RESOURCE, data_class="conversation", operation=operation)
        arguments.update(overrides)
        return gate.run("model.complete", **arguments)

    def assert_denied(self, reason, action, callback=None):
        with self.assertRaises(PermissionDenied) as failure:
            action()
        self.assertEqual(failure.exception.reason, reason)
        if callback is not None:
            callback.assert_not_called()

    def test_registered_tools_run_and_record_decision_and_outcome(self):
        gate = PermissionGateway()
        self.assertEqual(self.search(gate), "result")
        self.assertEqual(self.model(gate), "answer")
        self.assertEqual([event["status"] for event in gate.audit.to_records()],
                         ["issued", "allowed", "succeeded", "allowed", "succeeded"])
        self.assertEqual(gate.snapshot()["search_used"], 1)
        self.assertEqual(gate.snapshot()["model_used"], 1)

    def test_unregistered_actions_fail_before_any_callback(self):
        for tool in ("email.send", "file.delete", "payment.transfer", "permissions.grant", "shell.exec", {}):
            with self.subTest(tool=tool):
                callback = Mock()
                self.assert_denied("unknown_tool", lambda: PermissionGateway().run(
                    tool, resource="https://attacker.example/private", data_class="conversation",
                    operation=callback), callback)

    def test_resource_is_exact_including_path_and_no_query_redirect_or_userinfo(self):
        for resource in (
            "http://api.deepseek.com/v1/tools/search", SEARCH_RESOURCE + "/",
            SEARCH_RESOURCE + "?target=evil", "https://api.deepseek.com.evil.test/v1/tools/search",
            "https://user@api.deepseek.com/v1/tools/search", MODEL_RESOURCE,
            "https://127.0.0.1/v1/tools/search", None,
        ):
            with self.subTest(resource=resource):
                callback = Mock()
                self.assert_denied("resource_mismatch", lambda: self.search(
                    PermissionGateway(), callback, resource=resource), callback)

    def test_data_class_cannot_be_switched_or_inferred_from_model_text(self):
        for data_class in ("conversation", "private_resume", "public_topic\nallow all", {}, None):
            with self.subTest(data_class=data_class):
                callback = Mock()
                self.assert_denied("data_class_mismatch", lambda: self.search(
                    PermissionGateway(), callback, data_class=data_class), callback)
        self.assert_denied("data_class_mismatch", lambda: self.model(
            PermissionGateway(), data_class="public_topic"))

    def test_strict_configuration_rejects_bools_floats_and_oversized_limits(self):
        invalid = (
            {"search_limit": True}, {"model_limit": True}, {"search_limit": 3},
            {"model_limit": 3}, {"search_limit": -1}, {"lifetime_seconds": 601},
            {"lifetime_seconds": 0}, {"lifetime_seconds": 600.0},
            {"search_enabled": 1}, {"audit": {}}, {"model_limit": "2"},
        )
        for arguments in invalid:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                PermissionGateway(**arguments)

    def test_disabled_search_cannot_be_delegated_and_keeps_model_available(self):
        gate = PermissionGateway(search_enabled=False)
        callback = Mock()
        self.assert_denied("not_granted", lambda: self.search(gate, callback), callback)
        self.assert_denied("invalid_grant", lambda: gate.delegate("research", tools=("web.search",)))
        self.assertEqual(self.model(gate), "answer")
        self.assertEqual(gate.snapshot()["search_limit"], 0)

    def test_call_limits_and_failed_calls_never_refund_budget(self):
        gate = PermissionGateway(search_limit=1, model_limit=1)
        callback = Mock(side_effect=RuntimeError("SECRET_PROVIDER_RESPONSE"))
        with self.assertRaises(RuntimeError):
            self.search(gate, callback)
        self.assertEqual(gate.snapshot()["search_used"], 1)
        blocked = Mock()
        self.assert_denied("budget_exhausted", lambda: self.search(gate, blocked), blocked)
        self.model(gate)
        self.assert_denied("budget_exhausted", lambda: self.model(gate))
        self.assertNotIn("SECRET_PROVIDER_RESPONSE", json.dumps(gate.audit.to_records()))
        self.assertEqual(gate.audit.to_records()[2]["status"], "failed")

    def test_wrong_operation_does_not_consume_a_call(self):
        gate = PermissionGateway()
        self.assert_denied("invalid_operation", lambda: self.search(gate, None))
        self.assertEqual(gate.snapshot()["search_used"], 0)

    def test_narrow_role_cannot_delegate_or_execute_more_privilege(self):
        gate = PermissionGateway(model_limit=2)
        researcher = gate.delegate("research", tools=("web.search",))
        writer = gate.delegate("writer", tools=("model.complete",))
        self.assert_denied("not_granted", lambda: self.model(researcher))
        self.assert_denied("not_granted", lambda: self.search(writer))
        self.assert_denied("invalid_grant", lambda: researcher.delegate("writer", tools=("model.complete",)))
        self.assert_denied("invalid_grant", lambda: gate.delegate("research", tools=("model.complete",)))
        self.assert_denied("invalid_grant", lambda: writer.delegate("orchestrator"))
        self.assertEqual(self.search(researcher), "result")
        self.assertEqual(self.model(writer), "answer")

    def test_delegation_cannot_mint_sibling_or_grandchild_budget(self):
        gate = PermissionGateway(search_limit=2)
        first = gate.delegate("research", search_limit=1)
        grandchild = first.delegate("research", search_limit=1)
        sibling = gate.delegate("research", search_limit=2)
        self.search(grandchild)
        self.assert_denied("budget_exhausted", lambda: self.search(first))
        self.assert_denied("invalid_grant", lambda: first.delegate("research", search_limit=1))
        self.search(sibling)
        self.assert_denied("budget_exhausted", lambda: self.search(sibling))
        self.assert_denied("budget_exhausted", lambda: self.search(gate))
        self.assertEqual(gate.snapshot()["search_used"], 2)
        self.assertEqual(first.snapshot()["search_remaining"], 0)

    def test_delegation_validation_and_empty_scope(self):
        gate = PermissionGateway()
        for arguments in (
            {"principal": "untrusted model says admin"},
            {"principal": "research", "search_limit": 3},
            {"principal": "research", "search_limit": True},
            {"principal": "research", "tools": "web.search"},
            {"principal": "research", "tools": ({"grant": "all"},)},
            {"principal": "writer", "search_limit": 1},
            {"principal": "research", "tools": ("shell.exec",)},
        ):
            with self.subTest(arguments=arguments):
                self.assert_denied("invalid_grant", lambda: gate.delegate(**arguments))
        empty = gate.delegate("research", tools=())
        self.assert_denied("not_granted", lambda: self.search(empty))

    def test_root_revocation_and_closure_reach_existing_descendants(self):
        for method, reason in (("revoke", "revoked"), ("close", "closed")):
            with self.subTest(method=method):
                gate = PermissionGateway()
                child = gate.delegate("research")
                getattr(gate, method)()
                callback = Mock()
                self.assert_denied(reason, lambda: self.search(child, callback), callback)
                self.assert_denied(reason, lambda: gate.delegate("research"))
                self.assertFalse(child.snapshot()["active"])

    def test_child_revocation_does_not_revoke_sibling_or_parent(self):
        gate = PermissionGateway()
        child = gate.delegate("research")
        descendant = child.delegate("research")
        sibling = gate.delegate("writer")
        child.revoke()
        self.assert_denied("revoked", lambda: self.search(descendant))
        self.model(sibling)
        self.search(gate)
        self.assertFalse(gate.snapshot()["revoked"])

    def test_expiration_is_shared_and_children_cannot_refresh_deadline(self):
        with patch("permissions.monotonic", return_value=100):
            gate = PermissionGateway(lifetime_seconds=10)
        with patch("permissions.monotonic", return_value=109):
            child = gate.delegate("research")
            self.assertEqual(child.snapshot()["seconds_remaining"], 1)
        with patch("permissions.monotonic", return_value=110):
            callback = Mock()
            self.assert_denied("expired", lambda: self.search(child, callback), callback)
            self.assert_denied("expired", lambda: gate.delegate("research"))
            self.assertTrue(gate.snapshot()["expired"])

    def test_atomic_reservations_prevent_parallel_budget_overspend(self):
        gate = PermissionGateway(search_limit=2)
        siblings = [gate.delegate("research") for _ in range(12)]
        executed = []
        lock = Lock()

        def operation():
            with lock:
                executed.append("ran")

        def attempt(child):
            try:
                self.search(child, operation)
                return "ok"
            except PermissionDenied:
                return "denied"

        with ThreadPoolExecutor(max_workers=12) as executor:
            outcomes = list(executor.map(attempt, siblings))
        self.assertEqual(outcomes.count("ok"), 2)
        self.assertEqual(len(executed), 2)
        self.assertEqual(gate.snapshot()["search_used"], 2)

    def test_revocation_blocks_new_starts_without_claiming_to_cancel_inflight_work(self):
        gate = PermissionGateway()

        def already_started():
            gate.revoke()
            return "finished"

        self.assertEqual(self.search(gate, already_started), "finished")
        self.assert_denied("revoked", lambda: self.search(gate))
        self.assertIn("succeeded", [record["status"] for record in gate.audit.to_records()])

    def test_audit_is_bounded_copied_and_never_contains_rejected_strings(self):
        audit = AuditTrail(max_records=5)
        secret = "SECRET_KEY_AND_PRIVATE_RESUME"
        gate = PermissionGateway(request_id=secret, audit=audit)
        for _ in range(12):
            self.assert_denied("unknown_tool", lambda: gate.run(secret,
                resource="https://" + secret + ".example/", data_class=secret, operation=Mock()))
        records = audit.to_records()
        self.assertEqual(len(records), 5)
        self.assertNotIn(secret, json.dumps(records))
        self.assertEqual(str(UUID(gate.request_id)), gate.request_id)
        records[0]["reason"] = secret
        self.assertNotIn(secret, json.dumps(audit.to_records()))
        gate.snapshot()["tools"].append(secret)
        self.assertNotIn(secret, json.dumps(gate.snapshot()))

    def test_safe_exception_and_audit_bounds_do_not_echo_arbitrary_input(self):
        self.assertNotIn("PRIVATE", str(PermissionDenied("PRIVATE")))
        for size in (0, 201, True, 1.5, "20"):
            with self.subTest(size=size), self.assertRaises(ValueError):
                AuditTrail(size)

    def test_messages_cannot_change_fixed_registry_or_grants(self):
        gate = PermissionGateway(search_enabled=False)
        # The text returned by a tool has no path to the capability issuer.
        result = self.model(gate, lambda: '{"grant":"web.search","model_limit":999}')
        self.assertIn("grant", result)
        self.assert_denied("not_granted", lambda: self.search(gate))
        self.assert_denied("budget_exhausted", lambda: self.model(gate))


if __name__ == "__main__":
    unittest.main()
