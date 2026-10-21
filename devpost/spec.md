---
doc: spec
status: draft
---

# Career Planning Assistant — Technical Specification

Updated for the learner's explicit DeepSeek and conversational-interface choices. Other recommendations remain draft. The environment has been verified locally as Python 3.15.0 with Streamlit 1.66.0; the current implementation passed 22 provider-independent checks. The learner reported successful ordinary chat, a contextual revision, and a checked-plan test; the full checked-plan output was not supplied for independent review.

## How This Works, In Plain Language

Python runs a chat page on the learner's computer. When a person sends a message, the program sends the conversation to DeepSeek and displays its reply. The program keeps earlier messages during the current session so that follow-up questions can refer to what was already discussed.

The assistant's instructions guide the conversation toward useful career tasks. The explicit checked-plan action now checks the structure and timing of generated plans. It may request one correction before accepting a plan. Ordinary conversation remains available, and human review is still necessary for usefulness and career suitability.

## The Core Journey Through the System

`Chat composer -> pending user message -> DeepSeek conversation request -> checked response -> displayed assistant message`.

Keep the system instructions separate from the visible transcript. On failure, retain the pending user turn for explicit retry without appending the same user text again. Page reruns without an explicit send or retry must never create a model request.

Implements `prd.md > Conversation and Context`, `Guided Career Consultation`, and `States and Boundaries`.

## Stack

| Component | Choice and status | Documentation |
| --- | --- | --- |
| Runtime | Python 3.15.0, verified in the project environment | [Python](https://docs.python.org/3/) |
| Interface | Streamlit 1.66.0, installed and verified; chat controls recommended for the confirmed chat requirement | [Chat tutorial](https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps) |
| Provider | DeepSeek, explicitly selected by the learner | [First API call](https://api-docs.deepseek.com/) |
| Client | OpenAI Python SDK, recommended because DeepSeek officially documents this integration; version 3.35.1 installed and imported successfully | [Package](https://pypi.org/project/openai/), [Source](https://github.com/openai/openai-python) |
| Later validation | Pydantic models and schedule checks, proposed for the task-plan milestone | [Pydantic](https://docs.pydantic.dev/latest/concepts/models/) |

The client package name does not determine the service: configure it explicitly for DeepSeek. Record exact tested dependency versions after installation. No orchestration framework is needed for the first conversational connection.

## Where It Runs and How Someone Tries It

Local Windows process, opened at `http://localhost:8501`. The learner has created `.venv` and installed Streamlit. The API client import is verified and the first chat application files now exist. The learner has opened the page, configured model access privately, and reported successful live use.

Startup for the current chat page:

```powershell
Set-Location -LiteralPath 'D:\layerdesign'
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address localhost --server.port 8501
```

Configure `DEEPSEEK_API_KEY` privately in the local process environment or in `.streamlit/secrets.toml`, using the provided placeholder-only `.streamlit/secrets.toml.example`. Environment values take precedence. The real secrets file is ignored by Git. Use optional `DEEPSEEK_MODEL` to select an available model. Never request a real key in chat or display it in output. A credentials template may contain placeholders only. The learner reported successful ordinary-chat use; the learner has also reported a successful live JSON plan test.

Local recording and a public repository can support the submission; hosting is optional. See [competition rules](https://learn-ai-basics.devpost.com/rules).

## Look and Feel

Implements `prd.md > Look and Feel`: English interface, readable chat messages, and a simple single-page layout. Suggested light styling remains unapproved. Use the built-in chat components before introducing custom CSS or another frontend.

## Components

### Chat Page — `app.py`

Use `st.chat_message`, `st.chat_input`, and per-session message storage. Own the welcome state, message rendering, waiting indicator, explicit retry, and **New Conversation** action. Track a pending turn separately from successful replies so an unrelated rerun cannot resend it. Keep sessions independent and avoid global caching of user conversations.

Implements `prd.md > Conversation and Context` and `States and Boundaries`.

### DeepSeek Conversation — `agent.py`

Expose a narrow `reply(messages)` operation that returns a nonempty assistant reply or a typed application error. Configure the endpoint and credentials here, assemble the system message plus current history, and validate the response before the page appends it.

Proposed first version: one non-streaming request per explicit send, a 60-second timeout, and SDK automatic retries disabled. On authentication, billing, rate-limit, timeout, malformed-output, or incomplete-output failure, return a clear mapped error without printing the raw response, request payload, or key. Retry is a user action.

Implements `prd.md > Guided Career Consultation` and `States and Boundaries`.

### Career Instructions — `prompts.py`

English instructions: guide employment-related reflection, ask one relevant question at a time, reuse known context, and gather education, work situation, age if the person chooses to share it, and a planning period. Preserve user ownership of career decisions. Produce actionable tasks when enough information exists; expose assumptions and do not promise employment or invent live vacancy research.

Implements `prd.md > Guided Career Consultation` and `Actionable Task Plan`.

### Checked Task Plan — models.py and agent.generate_plan

The explicit UI action records a user-selected duration from 1 to 365 days and appends one visible plan request to the existing conversation. `generate_plan` requests a JSON object using DeepSeek's `response_format={"type": "json_object"}`. The system instructions include the required JSON schema and an example, plus the exact selected period. Source: [DeepSeek JSON output](https://api-docs.deepseek.com/guides/json_mode/).

`models.py` defines strict `Task` and `CareerPlan` contracts using the installed Pydantic 2.14.1. The parser requires a summary, assumptions, a duration, and 3-8 tasks with nonempty action, reason, and completion fields. Day values must be actual integers. Tasks start on or after day 1, end on or after their starts, fit the duration, and appear in nondecreasing start-day order; the first task starts on day 1. The returned duration must equal the saved selection. Parallel tasks are permitted.

Only a JSON/schema/schedule failure triggers one regeneration with fixed validation feedback. At most two provider calls occur for one checked-plan attempt. Authentication, connection, timeout, and incomplete-output errors stop immediately. Feedback contains safe rule categories, never raw invalid output or exception input values. A second invalid result becomes a safe application error; no invalid plan is shown.

The page renders a validated plan into readable Markdown and records a `schedule_checked` boolean with the assistant message. Only that application-owned metadata controls the validation label. API requests transmit only message roles and content; they do not transmit the UI marker. Retry preserves the original request kind and selected period, and a new conversation clears them.

Implements `prd.md > Actionable Task Plan` and `States and Boundaries`. Human review remains necessary for task usefulness and factual career claims.

## Data Model

| Data | Shape and lifetime |
| --- | --- |
| Visible message | Role `user` or `assistant`, text content; current session only |
| Pending turn | Submitted user text, request status, and safe error category; cleared on success or new conversation |
| Model request | System instruction plus complete active conversation history; transient network request |
| Configuration | Key and model identifier from the local environment or private Streamlit secrets; never included in messages |
| Validated plan | Structured tasks with checked timing; formatted into the active conversation with application-owned schedule_checked metadata |
| Pending plan settings | Request kind and selected duration saved with the pending user turn; stable across retry and cleared by a new conversation |

Proposed guards: trim and reject empty messages, cap one user message at 4,000 characters, and stop before exceeding 40 submitted user turns or 60,000 total transcript characters. Show a new-conversation prompt instead of silently discarding context. These limits bound growth but are not provider token-limit guarantees.

No persistent chat database or full-message application logging is proposed. Refreshing or closing a session may lose its history. Conversations sent to DeepSeek are subject to that provider's policies.

## External Services and Dependencies

DeepSeek: `POST https://api.deepseek.com/chat/completions`, authenticated with a DeepSeek bearer key. The documented SDK call is `client.chat.completions.create`, using `base_url="https://api.deepseek.com"`, a model name, `messages`, and `stream=False`; read `choices[0].message.content`. Source: [First API call](https://api-docs.deepseek.com/).

The endpoint is stateless for conversation context: resend prior messages with each turn. Source: [Multi-round conversation](https://api-docs.deepseek.com/guides/multi_round_chat/).

The current first-call guide lists `deepseek-flash` and `deepseek-v4-pro`. Recommend a configurable `deepseek-flash` default, subject to account verification. Do not assume older model aliases still work. The first chat implementation uses the documented non-thinking setting: `extra_body={"thinking": {"type": "disabled"}}`. Source: [Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/).

Actual account access, available quota, pricing, and latency have not been verified. No live API request has been made in this planning pass.

## File Structure

The first chat milestone implements app.py, agent.py, prompts.py, requirements.txt, README.md, configuration templates, and tests. The checked-plan milestone also implements models.py and its provider-independent tests:

```text
layerdesign/
  app.py                 # Chat UI and session state
  agent.py               # DeepSeek request and error handling
  prompts.py             # English career-consultation instructions
  models.py              # Strict task-plan schema, schedule checks, and formatting
  requirements.txt       # Verified dependencies
  README.md              # Setup and current milestone limitations
  devpost/
    scope.md
    prd.md
    spec.md
    learner-profile.md   # Local context, excluded from Git
```

Preserve installed skills. Extend `.gitignore` to cover `.venv/`, Python caches, and any local credential files before publishing; preserve the existing learner-profile and credential rules.

## Important Failure Modes

- Missing or invalid credentials: explain setup or authentication failure without exposing the key.
- Timeout, unavailable model, billing, or rate limit: retain the pending turn and allow explicit retry; do not create a fake reply.
- Empty or incomplete output: do not append it as a successful answer.
- Ordinary Streamlit rerun: render history without another provider call.
- New conversation: clear transcript and pending state so no old content enters the next request.

## Verification Plan

1. Verify the installed SDK imports in the project environment.
2. Use simulated provider responses to check history assembly, empty-output handling, failure mapping, and no duplicate user message on retry.
3. Run the page and check greeting, composer, message rendering, new conversation, and missing-configuration behavior.
4. After private configuration, obtain a genuine DeepSeek reply and a follow-up that uses earlier context. Record user-observed results; fixtures are not live evidence.
5. At the later planning milestone, test seven-day and ninety-day task plans, invalid schedules, and bounded correction.

## Guided Build Sequence

1. Verify the API client installation.
2. Create and open the chat page, explaining the visible messages and session history.
3. Configure DeepSeek privately and prove one real multi-turn conversation.
4. Add validated actionable plans to the working conversation.
5. Review, refine, and prepare reproducible setup, public repository, and demonstration video.

Pause for actual learner output or hands-on feedback at each useful step. Do not infer success from sending a command.

## Decisions and Open Issues

Confirmed: DeepSeek backend, chat interface, Windows, beginner-level coding guidance, and English project content. Verified: Python 3.15.0 and Streamlit 1.66.0.

The learner shared successful ordinary chat and a contextual three-day revision. The learner has also reported a successful checked-plan test and indicated that chat functionality is sufficient. Formal agreement on unreviewed draft details and final naming have not been separately recorded. SDK installation is verified. Chat configuration also includes a light theme and a placeholder-only private setup example. Formal document approval remains pending; continued setup does not silently mark all draft recommendations approved.

The learner's explicit provider and chat choices replace the earlier form-first and provider proposals. The initial chat application and simulated-response checks are implemented. The learner has since provided ordinary-chat output and a contextual revision. The learner has since reported successful live use of the JSON plan operation; no full output was supplied for independent content review.

## First Chat Milestone Evidence
Nine provider-independent checks passed for the initial chat code. They exercised safe API handling, conversation limits, page setup, history, reset, and retry. No real DeepSeek request was made. The learner must still open the browser page and then verify a real conversation after private configuration. See checklist.md for unfinished milestones.


## Checked-Plan Verification Evidence

Twenty-two provider-independent tests passed in the development copy. They cover the chat regression cases, plan field and duration rules, bounded correction, absence of correction on provider connection failure, the actual selected period reaching the plan call, no extra request when changing a widget, correct UI labeling, and stable retry behavior. These checks simulate provider replies and do not prove the live JSON operation or career-advice quality. Pydantic 2.14.1 was already installed and has been pinned as a direct dependency.

The learner's shared live three-day revision retained the fictional business-degree and retail background and reduced the tasks to days 1, 2, and 3. That completes the reported contextual-chat check, not the new checked-plan check. No real API key was read or changed for this implementation.

## Reported Checked-Plan Result

The learner reported that the three-day checked-plan test succeeded. The full generated plan was not supplied for independent content review. The learner then indicated that the chat functionality is sufficient; no additional chat feature was requested. Automated coverage remains distinct from learner-reported live evidence.
