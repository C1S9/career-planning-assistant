# Evidence and coaching skills

Version 0.3.0 adds an actual retrieval step before advice. It does not turn the model into a certified adviser or prove that every generated sentence is true.

## Request flow

1. Validate the submitted conversation and selected mentor.
2. Convert recognized concerns into a fixed, general search topic. Only predefined topic phrases and an optional selected country enter the search query. Names, emails, employers, exact ages, and raw conversation text do not enter it. The full conversation still reaches DeepSeek's chat service, as before.
3. Use DeepSeek's authenticated Search API at `POST https://api.deepseek.com/v1/tools/search`, with `need_content: true`. Search uses the same privately supplied key as chat. The app does not independently fetch result URLs.
4. Search at most twice within a shared retrieval budget. Prefer named primary publishers from the mentor's domain registry. Accept only strict HTTPS URLs, sufficient provider relevance scores, real page content, and excerpts containing topic terms. Reject invented-looking host variants, absent content, unrelated excerpts, malformed dates, and implausible future dates. A provider score is a filter, not proof of truth.
5. Load the evidence skill and selected mentor workflow. Load the planning skill only for an explicit checked-plan request. Pass source excerpts as untrusted external data, not instructions.
6. Generate the answer using the current evidence. Require source markers such as `[S1]` and reject source identifiers or links absent from this retrieval. A failed chat reference check stops the answer; a failed plan reference or schedule check allows one correction using the same evidence.
7. Display actual links, original excerpts, search topic, retrieval timestamp, and the publication date reported by the search provider in **Sources consulted**. Source records belong to the application, not model-generated prose.

If retrieval has no suitable results or is unavailable, chat returns a fixed clarification notice without generating advice. A checked plan is not generated. Ordinary page reruns, region selection, theme changes, and mentor selection do not trigger retrieval. An explicit retry creates a new request.

## Practical skills used at runtime

| Skill | Applied when | Purpose |
| --- | --- | --- |
| `evidence-informed-coaching` | Every advice request | Check claim support and applicability, distinguish facts from interpretation, cite honestly, preserve the person's choices |
| `mentor-decision-workflow` | Every advice request | Load only the selected mentor's career, direction, learning, habits, or communication workflow |
| `realistic-action-planning` | Explicit checked-plan requests | Use actual constraints, manageable actions, relative days, observable completion criteria, and a review point |

These are English instruction files in `skills/*/SKILL.md`. `coaching_skills.py` loads them into the actual model request. They do not install tools or grant a model independent internet access. `evidence.py` performs the real network operation. Required skills missing or malformed cause a failure rather than a silent downgrade.

## What remains uncertain

The domain registry identifies recognized publishers, not an infallible source of truth. The app does not prove factual entailment, independently verify search metadata or page contents, assess study quality automatically, or certify individual suitability. Retrieved documents may be old, incomplete, or about a different jurisdiction. A credible source about technology jobs is not a reason to recommend technology to someone with unspecified interests.

Queries use a small English/Chinese topic vocabulary to protect privacy. Very specific occupations, examinations, local laws, and other countries may not be covered well. The country selector scopes or prioritizes relevant searches; it does not determine which rules apply to the person. If coverage is insufficient, the mentor should ask a clarification rather than invent local facts. Health, legal, and financial topics remain general coaching.

Search introduces latency and may incur additional provider charges. One interaction uses at most two Search API requests and one chat completion; an explicit checked plan may use two chat completions after a failed check. Connection or account errors are not hidden model retries. No search result URLs receive the API key; authenticated HTTP requests go only to the fixed DeepSeek endpoint, with redirects disabled.

## Learning map

- `search_topics.py`: a finite query vocabulary protects private text.
- `evidence.py`: HTTP boundary, trusted publishers, bounded source selection, and honest retrieval states.
- `references.py`: source identity and link checks; semantic truth remains outside this check.
- `coaching_skills.py` and `skills/`: runtime instruction loading and progressive mentor selection.
- `agent.py`: retrieval-before-generation and failure handling for both chat and plans.
- `app.py`: source records and optional source-region selection.
- `tests/test_evidence.py`, `test_research_workflow.py`, and `test_skills.py`: failure, privacy, reference, and runtime-loading checks.

Implementation references checked on 2026-10-23: [DeepSeek Search & Fetch](https://api-docs.deepseek.com/guides/search/), [HTTPX2 package](https://pypi.org/project/httpx2/). Provider behavior and billing can change; consult their current documentation.
