# Permission design review

Reviewed against the Life Direction Agent v0.4.0 implementation on 2026-10-23.

## Purpose and scope

The permission layer mediates the application's two existing network actions: a
public-topic search sent to DeepSeek and a conversation sent to DeepSeek's model.
It does not add email, purchases, arbitrary file access, shell execution, or job
applications. Those actions remain unavailable even if a conversation, webpage,
skill, or model response requests them.

The intended boundary is between untrusted natural-language data and trusted
application tool code. It is not an operating-system sandbox. Someone who can
modify or execute arbitrary Python in this process can bypass an application
module, read process memory, or make their own network calls. A compromised
dependency, hostile local administrator, or malicious transport is outside this
boundary. The application must not describe this release as prompt-injection
proof, an enterprise authorization service, or a complete implementation of CaMeL.

## Research and dependency decision

CaMeL places policy checks outside the language model and tracks control and data
flows. This project adopts the narrower principle that model-generated text cannot
grant tool authority. Its data-class labels are application metadata, not a
general-purpose taint-tracking system. CaMeL's published benchmark results and
formal claims do not transfer to this application. The authors also describe the
reference code as a research artifact rather than a maintained product.
[Paper](https://arxiv.org/abs/2503.18813),
[reference implementation](https://github.com/google-research/camel-prompt-injection).

OWASP recommends reducing agent functionality and downstream permissions to the
minimum needed, using granular tools, and independently controlling high-impact
operations. Keeping the current tool registry small is an intentional design
choice: a future operation should be added explicitly, with an appropriate
resource scope and tests, rather than routed through a generic shell or URL-fetch
tool. [OWASP Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/).

Existing policy engines were considered. Cedar separates authorization policies
from business logic; Casbin supports multiple access-control models and a Python
implementation. Either may become useful for multiple users, organizations,
persisted grants, or a larger resource model. Neither supplies this application's
request lifecycle, HTTP mediation, redaction, or shared call accounting by itself.
For two fixed tools and one local user, a small, tested in-process gateway avoids
another runtime dependency. This is a project-specific engineering choice, not a
claim that custom authorization is generally preferable.
[Cedar documentation](https://docs.cedarpolicy.com/),
[Casbin documentation](https://casbin.apache.org/docs/overview/).

## Required enforcement properties

| Boundary | Expected behavior |
| --- | --- |
| Default denial | Unknown tools, actors, resource URLs, and data classes do not reach a transport. |
| Resource scope | Only the exact configured DeepSeek search and completion endpoints are accepted. |
| Delegation | Research receives search authority; writing receives model authority. A child cannot add authority. |
| Shared accounting | Delegated handles share their request's budget, expiry, and revocation state. Creating a handle does not replenish calls. |
| Failure accounting | An attempted permitted network operation consumes a call even if it fails. |
| Lifecycle | A completed or failed request revokes its grant. A retry creates a new explicit request. |
| Network behavior | Both transports disable redirects and environment-proxy inheritance. |
| Audit minimization | Records contain controlled operation metadata and outcomes, not keys, conversation text, search results, or provider error bodies. |
| Human interaction | Sending a message authorizes its bounded existing workflow; ordinary page reruns create no additional requests. |

Search authority allows only a public topic selected by trusted application code.
The finite vocabulary in `search_topics.py` is what prevents raw personal text
from entering searches. A `public_topic` label alone does not prove that arbitrary
text is public. The model endpoint intentionally receives the conversation, as
described in the interface; this permission layer does not make it local-only.

## Transport review

The installed OpenAI-compatible SDK, version 3.35.1, defaults its internally
created HTTP clients to following redirects. `agent.py` therefore supplies an
explicit HTTPX2 client with `follow_redirects=False` and `trust_env=False`.
`evidence.py` applies the same settings to search. Application limits must remain
at the actual transport boundaries, not only in the interface or prompt.

This matters because a redirected request may leave the exact resource originally
checked by the gateway. Disabling redirects also prevents transparent additional
HTTP calls from escaping request accounting. Disabling environment proxies avoids
silently routing requests through proxy settings inherited from the launch
environment; it can require users of mandatory corporate proxies to configure a
different, explicitly reviewed transport in a future release. The settings were
checked against the installed HTTPX2 source, rather than assumed from the older
HTTPX package. [HTTPX2 project](https://github.com/pydantic/httpx2).

Provider and permission failures must use fixed, user-safe messages. Raw exception
strings, rejected payloads, and arbitrary attempted URLs must not become audit
fields. A denial reason can explain the category without repeating potentially
private attacker-controlled input.

## Adversarial verification matrix

| Test | Required observation |
| --- | --- |
| Allowed chat or checked plan | Search and model calls complete within their limits; a plan correction shares the original budget. |
| Disabled search, disabled conversation, or paused network | Denial occurs before the relevant HTTP client is opened. |
| Unknown tool or unapproved endpoint | The operation callback is never executed. |
| Research attempts model authority | Delegation or execution is denied. |
| Multiple children attempt to exhaust separate budgets | They consume the same parent budget; no budget reset occurs. |
| Revoked or expired request handle | Further network actions are denied. |
| Authorized operation raises an exception | The call remains consumed, and private error text is absent from audit output. |
| Provider returns an HTTP redirect | Exactly one outbound request occurs; the redirect target is never contacted. |
| Page text requests a new tool or a larger grant | Text may influence a model response, but cannot modify the tool registry or permissions. |
| Ordinary interface rerun | No extra provider request is made. |
| New conversation or changed mentor | Pending authority is invalidated; old results cannot enter the new conversation. |

These tests establish behavior for the exercised implementation and attack cases.
They do not establish that every possible prompt injection is harmless or that
source-supported coaching is factually correct. Source applicability and advice
quality remain separate concerns.

The independent review ran the 24 offline tests in `test_permissions.py` and
`test_permission_transports.py` successfully. The transport tests used the actual
installed SDK with an in-memory HTTP transport, including HTTP 302, 307, and 308
responses. They made no paid provider calls. Static integration review confirmed
that both network operations are mediated, ordinary interface reruns do not issue
new grants, and request cleanup closes the grant on both success and failure.
The full release validation report records additional integration and UI checks.

## Limits to communicate

- Request limits count attempts, not money. The permission layer does not enforce
  a currency budget or guarantee provider billing behavior.
- Expiry and revocation prevent subsequent calls. They do not recall data already
  sent to a provider or guarantee cancellation of an HTTP request already running.
- Session audit records are for local visibility. They are not tamper-evident,
  persistent compliance records or an externally authenticated identity system.
- The research and writing roles are application roles with restricted handles;
  they are not separate models, isolated operating-system processes, or independent
  human reviewers.
- A future high-impact tool needs a concrete approval protocol tied to its exact
  target and payload. A generic approval flag is not sufficient.

