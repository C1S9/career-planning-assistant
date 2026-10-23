"""Exercise real provider transports without contacting a network service."""

import json
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import httpx2

import agent
import evidence
from permissions import AuditTrail, PermissionDenied, PermissionGateway


class PermissionTransportTests(unittest.TestCase):
    def test_real_sdk_does_not_follow_redirects_or_inherit_proxy_settings(self):
        """A provider redirect cannot create an unchecked additional request."""
        for status in (302, 307, 308):
            with self.subTest(status=status):
                requests, clients = [], []

                def handler(request):
                    requests.append(request)
                    return httpx2.Response(
                        status,
                        headers={"location": "https://attacker.example/collect"},
                        json={"error": "private-provider-response"},
                    )

                def client_factory(**options):
                    self.assertIs(options["follow_redirects"], False)
                    self.assertIs(options["trust_env"], False)
                    client = httpx2.Client(
                        transport=httpx2.MockTransport(handler), **options,
                    )
                    clients.append(client)
                    return client

                # Replace the application alias, not the HTTPX2 class: the real
                # SDK must still validate and execute its real HTTP client.
                gate = PermissionGateway()
                with patch.object(agent, "httpx", SimpleNamespace(Client=client_factory)):
                    with self.assertRaises(agent.ChatError) as caught:
                        agent._complete(
                            [{"role": "user", "content": "A fictional career question."}],
                            api_key="fictional-test-key", model=agent.DEFAULT_MODEL,
                            gateway=gate,
                        )
                self.assertEqual(len(requests), 1)
                self.assertEqual(str(requests[0].url), "https://api.deepseek.com/chat/completions")
                self.assertEqual(requests[0].method, "POST")
                self.assertTrue(clients[0].is_closed)
                self.assertEqual(gate.snapshot()["model_used"], 1)
                self.assertNotIn("private-provider-response", str(caught.exception))
                self.assertNotIn("fictional-test-key", json.dumps(gate.audit.to_records()))
                self.assertNotIn("attacker.example", json.dumps(gate.audit.to_records()))
                self.assertIn("failed", {event["status"] for event in gate.audit.to_records()})

    def test_completion_denied_before_client_creation(self):
        for reason in ("no_model_permission", "revoked", "closed", "expired"):
            with self.subTest(reason=reason):
                gate = PermissionGateway(model_limit=0 if reason == "no_model_permission" else 1)
                if reason == "revoked":
                    gate.revoke()
                elif reason == "closed":
                    gate.close()
                # Change the permission clock without sleeping or making an
                # in-flight request. The original TTL remains immutable.
                clock = time.monotonic() + 601 if reason == "expired" else time.monotonic()
                with patch("permissions.monotonic", return_value=clock):
                    with patch.object(agent, "OpenAI") as provider:
                        with self.assertRaises(PermissionDenied):
                            agent._complete(
                                [{"role": "user", "content": "A fictional question."}],
                                api_key="fictional-test-key", model=agent.DEFAULT_MODEL,
                                gateway=gate,
                            )
                        provider.assert_not_called()

    def test_search_denied_before_client_creation(self):
        gate = PermissionGateway(search_enabled=False)
        with patch.object(evidence, "httpx", SimpleNamespace(Client=Mock())) as network:
            with self.assertRaises(PermissionDenied):
                evidence._search("career planning", "fictional-test-key", time.monotonic() + 10, gate)
            network.Client.assert_not_called()

    def test_search_requires_gateway_even_for_fixed_endpoint(self):
        with patch.object(evidence, "httpx", SimpleNamespace(Client=Mock())) as network:
            with self.assertRaises(PermissionDenied):
                evidence._search("career planning", "fictional-test-key", time.monotonic() + 10)
            network.Client.assert_not_called()

    def test_permission_denial_does_not_log_private_inputs(self):
        trail = AuditTrail()
        gate = PermissionGateway(audit=trail)
        operation = Mock()
        with self.assertRaises(PermissionDenied):
            gate.run(
                "tool-containing-a-private-key", resource="https://attacker.example/private-resume",
                data_class="personal-information", operation=operation,
            )
        operation.assert_not_called()
        encoded = json.dumps(trail.to_records())
        for private_value in ("private-key", "attacker.example", "private-resume", "personal-information"):
            self.assertNotIn(private_value, encoded)


if __name__ == "__main__":
    unittest.main()
