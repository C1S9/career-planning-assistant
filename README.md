# Life Direction Agent

**Version 0.4.0** · English coaching conversations · DeepSeek · Windows portable app

A conversational app with five mentor presets, live primary-source retrieval before advice, three runtime coaching skills, checked action plans, and a program-enforced permission gateway. Choose the area you want to work on, explain your situation, and turn the conversation into manageable next steps.

## Windows: download and run

Open the [v0.4.0 release](https://github.com/C1S9/career-planning-assistant/releases/tag/v0.4.0), download `LifeDirectionAgent-v0.4.0-windows-x64.zip`, extract the entire folder, and double-click `LifeDirectionAgent.exe`. Keep `_internal` beside the exe. The launcher opens the app in your default browser; **Quit** stops its local server.

You do not install Python, Node.js, or Streamlit, and you do not deploy a server. Internet access and your own authorized DeepSeek API key are still required for model replies. No owner's key or prepaid API access is included. See [Windows quick start](docs/WINDOWS_QUICKSTART.md) for connection, launch, and troubleshooting instructions.

The executable is unsigned. Release files include a ZIP checksum, build report, and third-party dependency notices. Application license selection remains separate and pending.

## Choose a mentor

| Mentor | Focus |
| --- | --- |
| Career & work | Career exploration, transferable skills, and work decisions |
| Life direction | Values, priorities, options, and small experiments |
| Learning & skills | Learning goals, deliberate practice, and study routines |
| Habits & focus | Sustainable routines, task initiation, and reducing friction |
| Communication & relationships | Clearer conversations, boundaries, and ordinary disagreements |

Changing mentors starts a fresh conversation, so prior context is not silently shared across mentor modes. **New Conversation** resets the current thread. The page keeps the chat canvas simple, with mentor, connection, and plan controls in the sidebar. Select **Light**, **Dark**, or **System** in the top-right app menu.

These are prompt presets using the same DeepSeek backend, not separately trained models or licensed professionals. They provide general coaching; the person retains ownership of decisions.

## Connect privately

Open **Connection**, paste a key into the password field, and select **Use for this session**. The pasted key stays in Python memory associated with this browser session and is not saved to disk. **Forget session key** removes that session override. Environment variables or optional private Streamlit settings can still provide credentials.

For source runs, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and configure the real key locally, or use private process environment variables `DEEPSEEK_API_KEY` and optional `DEEPSEEK_MODEL`. Environment settings override the local file; a pasted session key overrides both. Real settings, backup secret files, local environments, and `devpost/learner-profile.md` are excluded from Git and desktop packaging.

The compatible Python client contacts [DeepSeek](https://api-docs.deepseek.com/) at `https://api.deepseek.com`. The default model is `deepseek-flash`; model access and API balance belong to the account whose key is used.

## Consult sources before advice

Every advice request searches through DeepSeek using a fixed general topic, filters for relevant primary-source page content, and checks that source identifiers and links match actual results. Open **Sources consulted** below a reply to see real links, excerpts, the search topic, retrieval time, and publication dates reported by search. **Sources and skills** offers an optional country selection. If retrieval fails, the app clarifies instead of generating ungrounded advice, and does not create a checked plan. Search may add API charges.

The application loads `evidence-informed-coaching`, the selected section of `mentor-decision-workflow`, and, for plans, `realistic-action-planning`. These files actually reach model instructions; Python performs the network search. See [Evidence and skills](docs/EVIDENCE_AND_SKILLS.md) for the flow, privacy choices, coverage limits, and learning map. Source identity checks are not automatic fact-checking.

## Permissions before execution

Every explicit send, plan, or retry creates a new request permission. The application checks the registered tool, fixed DeepSeek destination, declared data category, remaining call count, and expiry before starting a network operation. Search receives a general public topic; model completion receives conversation context. The grant lasts at most ten minutes and is revoked when the request finishes, including on error.

Research can use only search. Writing and planning can use only model completion. These are Python capability scopes inside the existing workflow, not additional independently reasoning agents. Delegated scopes share their ancestors' remaining budgets, so creating more scopes does not increase authority. An ordinary chat permits at most two search starts and one completion; a checked plan permits at most two search starts and two completions, including its correction. Failed starts that reach the transport still consume their reservation. Limits count application transport starts, not money or tokens.

Open **Permissions** to allow or pause online requests and lower the search or plan-completion allowance. **Recent activity** shows request counts and audit events. Pausing prevents new starts after the setting is processed; a transport already in progress may finish and incur provider charges. Audit events contain fixed metadata rather than keys, chat text, search queries, source excerpts, or raw errors. Up to 200 events are kept for the current conversation; a new conversation clears them. They are memory-only, not a durable or tamper-proof security log.

There are no registered email, file-upload, payment, permanent-deletion, or permission-administration tools. User text, pages, and skills cannot grant those tools. The gateway is an application boundary around the two implemented transports; it is not a Windows sandbox and cannot confine arbitrary Python code, plugins, or the whole process. See [Permissions and execution boundaries](docs/PERMISSIONS.md) for exact checks, delegation, audit behavior, and learning examples.

## Create a checked action plan

1. Describe your situation and constraints in the chat.
2. Open **Create a task plan**, select **Plan length (days)** from 1 to 365, and select **Create checked plan**.
3. The result must have 3–8 tasks, required text fields, a day-1 start, ordered start days, and dates inside the saved selection.
4. A passing result is marked **Task fields and schedule checked**. The label does not certify personal suitability, current opportunities, or outcomes.

The selected mentor and current conversation reach the JSON request. A field, schedule, or source-reference failure permits one correction, for at most two model calls per plan click. Retrieval adds at most two Search API requests and is shared across a plan correction. Provider connection/account errors and incomplete output stop immediately. Explicit retry preserves the original user turn and duration; unrelated page reruns and theme changes do not authorize another request. Ordinary chat has no validation label.

## Run from source on Windows

Verified development environment: Python 3.15.0, Streamlit 1.66.0, OpenAI-compatible client 3.35.1, and Pydantic 2.14.1.

```powershell
git clone https://github.com/C1S9/career-planning-assistant.git
Set-Location -LiteralPath '.\career-planning-assistant'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address localhost
```

If your checkout is already at `D:\layerdesign`, open that folder and reuse its `.venv` instead of cloning again. Open the local address shown in the terminal. Stop the source server with Ctrl+C.

## Verify and package

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe scripts/build_windows.py
```

The build uses PyInstaller 6.22.3 and an explicit public-file allowlist. It bundles Streamlit's frontend, the application modules including `permissions.py`, the Python runtime, native launcher resources, and dependency notices. Its isolated smoke test removes external Python from PATH and checks the launcher, permission budget/revocation/paused-network denials with local callbacks, field/schedule validation, local server, frontend asset, and app-script execution without a paid API call. Results and SHA-256 are in `release/`; generated packages are not committed to Git.

GitHub Actions runs application checks on pushes and pull requests. A matching `v*` tag builds and tests a Windows package and publishes a new Release; an existing release is left unchanged. Manual workflow runs produce build artifacts. No filesystem watcher or background updater automatically commits unrelated local work.

## Code and learning references

- `mentors.py`: five immutable presets and role-specific context.
- `prompts.py`: shared rules plus selected-mentor instructions.
- `app.py`: sidebar controls, session-only credentials, conversation state, explicit requests and retry.
- `agent.py`: DeepSeek boundary and bounded structured-plan correction.
- `permissions.py`: request capabilities, fixed destinations, delegated budgets, revocation, and metadata-only audit events.
- `models.py`: task fields, schedule checks, and readable output. The internal `CareerPlan` type is retained for compatibility; the visible output is now an action plan for any mentor.
- `desktop.py`: native launcher and a loopback-only Streamlit server using the public `st.App.run` API.
- `packaging/` and `scripts/build_windows.py`: reproducible Windows packaging and smoke checks.
- [Learning guide](docs/LEARNING_GUIDE.md), [permissions guide](docs/PERMISSIONS.md), [offline app map](devpost/app-map.html), and [release notes](docs/releases/v0.4.0.md).

## Evidence and remaining work

Eighty-eight provider-independent checks passed for v0.4.0, covering the existing application and permission behavior. A live fictional-context chat and three-day checked plan each completed with one search and one model call, and both request grants were revoked afterward. The desktop permission probe also passed using only local callbacks. See the current CI run and release build report for completed packaged checks. None of these checks certifies every mentor's advice quality.

The Windows build runs an isolated bundled smoke check before producing its release ZIP. See the release build report for the final artifact details. This is a locally running application with a public source repository; a hosted service, background updater, completed demo video, and Devpost submission are not included.

Messages are sent to DeepSeek. History and audit events are kept in Python memory associated with the browser session, without an application chat database, and may be lost when the connection ends. The app does not write complete chats or keys to its own logs. Never include keys or personal conversations in screenshots or bug reports.
