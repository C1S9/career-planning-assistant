# Career Planning Assistant

A local conversational prototype for discussing career uncertainty and practical next steps, using the DeepSeek API.

## Learn While Building

Read [the step-by-step learning guide](docs/LEARNING_GUIDE.md) for the completed setup process, a walkthrough of one message, explanations of the annotated code, private API configuration, and checks for the first genuine reply. Code comments and project documentation use English; conversational teaching may continue in Chinese.

## Current Milestone

The chat interface, model-call code, and an explicit checked-plan action are implemented. Ordinary chat supports consultation. Plans generated through **Create checked plan** are validated for required fields, task count, and timing before display, with at most one correction request.

The learner reported successful live use and shared both a seven-day plan and its three-day revision, preserving the fictional background. The learner also reported successful live use of the checked-plan action; its full output was not supplied for independent content review. Automated checks use simulated provider replies. The initial greeting is local text, not proof of a successful API call. See `devpost/checklist.md` for evidence and unfinished checkpoints.

## Setup on Windows

Verified environment: Python 3.15.0, Streamlit 1.66.0, and OpenAI Python client 3.35.1. The client is configured to contact DeepSeek.

```powershell
Set-Location -LiteralPath 'D:\layerdesign'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If `.venv` already exists and the dependencies are installed, use that environment.

## Configure DeepSeek Privately

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and replace the placeholder key locally. Never post your real key in a conversation or screenshot. Alternatively, configure `DEEPSEEK_API_KEY` and optional `DEEPSEEK_MODEL` in the local process environment; environment settings take precedence.

The default model is `deepseek-flash`, as listed in the current [DeepSeek API guide](https://api-docs.deepseek.com/). An account with API access and available usage balance is required for real replies. Check actual availability in your own account.

## Run

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address localhost --server.port 8501
```

Open `http://localhost:8501`. Without credentials, the page shows the welcome and setup state. With credentials, send a fictional career concern, then a follow-up that refers to earlier context. **New Conversation** clears the active history. Stop the local server with Ctrl+C.

## How the Files Fit Together

- `app.py`: chat page, per-session history, explicit retry, and reset.
- `agent.py`: DeepSeek request, conversation limits, response checks, and safe errors.
- `prompts.py`: English career-consultation instructions.
- `models.py`: strict task fields, plan duration, schedule validation, and checked-plan formatting.
- `.streamlit/config.toml`: light theme and local app settings.
- `devpost/`: scope, product requirements, technical specification, and build tracking.

One explicit send makes one non-streaming request. SDK automatic retries are disabled. A failed reply preserves the user's message and can be retried explicitly without duplicating the message. Ordinary page reruns do not resend it. Full conversation history is sent with each turn; see [DeepSeek multi-round conversation](https://api-docs.deepseek.com/guides/multi_round_chat/).

## Create a Checked Task Plan

1. Share a career concern and relevant background in the chat.
2. Expand **Create a task plan** and choose **Plan length (days)**, from 1 to 365.
3. Select **Create checked plan**. The chosen period is saved with the request; changing a widget alone does not call the model.
4. A successful result is marked **Task fields and schedule checked**. It contains 3–8 tasks, starts on day 1, and stays inside the selected period.

This action requests JSON from DeepSeek, parses it into Pydantic models, and compares its duration against the actual selection. A structural or schedule failure permits one regeneration with validation feedback, for at most two requests per click. Connection errors, incomplete replies, and account errors stop immediately. Failed plans are not displayed as checked; explicit retry keeps the original requested period and user turn.

The label does not certify job availability, career suitability, or whether a person will complete the tasks. Ordinary conversational text has no checked-plan label. See [DeepSeek JSON output](https://api-docs.deepseek.com/guides/json_mode/) for the provider format.

## Verify Without a Paid API Request

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

These tests use simulated provider responses. They do not prove live credentials, account balance, model availability, or career-advice quality.

Chat history is session-only and may be lost when the browser connection ends. Submitted messages are sent to DeepSeek; session-only storage does not make the model request local. The app does not write full conversations to its own logs.

## Project Status

The demo is stored in the [private GitHub repository](https://github.com/C1S9/career-planning-assistant). Publication was verified against the local commit and all 20 tracked file paths. Planning documents remain drafts for review. License selection, the final demo video, and Devpost submission remain pending. The learner has reported a successful live checked-plan test.

## Protect API Keys from Git
Keep real credentials only in the ignored local settings file or a private environment variable. Secret-file backups and local environment variants are ignored; example files must contain placeholders only. Review the actual staged changes before every commit and never force-add private settings. See [the targeted local Git protection check](docs/API_KEY_GIT_CHECK.md) for the verified scope and limitations.

## Code Reference

Open [the offline app map](devpost/app-map.html) in a browser for a three-stop reference route from the plan button through the DeepSeek request to schedule validation. It is a technical reference, not a completed hands-on exercise or submission description.
