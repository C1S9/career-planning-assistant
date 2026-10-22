# Life Direction Agent

**Version 0.2.0** · English coaching conversations · DeepSeek · Windows portable app

A conversational app with five mentor presets and explicit, independently checked action plans. Choose the area you want to work on, explain your situation, and turn the conversation into manageable next steps.

## Windows: download and run

Open the [v0.2.0 release](https://github.com/C1S9/career-planning-assistant/releases/tag/v0.2.0), download `LifeDirectionAgent-v0.2.0-windows-x64.zip`, extract the entire folder, and double-click `LifeDirectionAgent.exe`. Keep `_internal` beside the exe. The launcher opens the app in your default browser; **Quit** stops its local server.

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

Open **Connection**, paste a key into the password field, and select **Use for this session**. The pasted key stays in the browser session and is not saved to disk. **Forget session key** removes that session override. Environment variables or optional private Streamlit settings can still provide credentials.

For source runs, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and configure the real key locally, or use private process environment variables `DEEPSEEK_API_KEY` and optional `DEEPSEEK_MODEL`. Environment settings override the local file; a pasted session key overrides both. Real settings, backup secret files, local environments, and `devpost/learner-profile.md` are excluded from Git and desktop packaging.

The compatible Python client contacts [DeepSeek](https://api-docs.deepseek.com/) at `https://api.deepseek.com`. The default model is `deepseek-flash`; model access and API balance belong to the account whose key is used.

## Create a checked action plan

1. Describe your situation and constraints in the chat.
2. Open **Create a task plan**, select **Plan length (days)** from 1 to 365, and select **Create checked plan**.
3. The result must have 3–8 tasks, required text fields, a day-1 start, ordered start days, and dates inside the saved selection.
4. A passing result is marked **Task fields and schedule checked**. The label does not certify personal suitability, current opportunities, or outcomes.

The selected mentor and current conversation reach the JSON request. A structural failure permits one correction, for at most two provider calls per click. Provider connection/account errors and incomplete output stop immediately. Explicit retry preserves the original user turn and duration; unrelated page reruns and theme changes do not authorize another request. Ordinary chat has no validation label.

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

The build uses PyInstaller 6.22.3 and an explicit public-file allowlist. It bundles Streamlit's frontend, the application modules, the Python runtime, native launcher resources, and dependency notices. Its isolated smoke test removes external Python from PATH, checks the launcher, field/schedule validation, local server, frontend asset, and app-script execution without a paid API call. Results and SHA-256 are in `release/`; generated packages are not committed to Git.

GitHub Actions runs application checks on pushes and pull requests. A matching `v*` tag builds and tests a Windows package and publishes a new Release; an existing release is left unchanged. Manual workflow runs produce build artifacts. No filesystem watcher or background updater automatically commits unrelated local work.

## Code and learning references

- `mentors.py`: five immutable presets and role-specific context.
- `prompts.py`: shared rules plus selected-mentor instructions.
- `app.py`: sidebar controls, session-only credentials, conversation state, explicit requests and retry.
- `agent.py`: DeepSeek boundary and bounded structured-plan correction.
- `models.py`: task fields, schedule checks, and readable output. The internal `CareerPlan` type is retained for compatibility; the visible output is now an action plan for any mentor.
- `desktop.py`: native launcher and a loopback-only Streamlit server using the public `st.App.run` API.
- `packaging/` and `scripts/build_windows.py`: reproducible Windows packaging and smoke checks.
- [Learning guide](docs/LEARNING_GUIDE.md), [offline app map](devpost/app-map.html), and [release notes](docs/releases/v0.2.0.md).

## Evidence and remaining work

Twenty-nine provider-independent checks passed for the updated app. Separately, one live learning-mentor request using fictional spreadsheet-learning context returned a three-day, three-task plan that passed the real field and schedule validator. This single live check does not certify every mentor's advice quality. Earlier learner-reported chat and checked-plan successes belong to the initial demo.

The Windows package passed its isolated bundled smoke check. See the release build report for the final artifact details. This is a locally running application with a public source repository; a hosted service, background updater, completed demo video, and Devpost submission are not included.

Messages are sent to DeepSeek. History is kept only in the browser session, without an application chat database, and may be lost when the connection ends. The app does not write complete chats or keys to its own logs. Never include keys or personal conversations in screenshots or bug reports.
