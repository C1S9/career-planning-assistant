# Graduate Career Workbench

A practical career assistant for students and recent graduates pursuing **mainland China internships and campus recruitment**. Build a profile, investigate a role, compare a job description with your experience, keep an application list, and turn the next steps into a downloadable plan.

**v0.5.0 · English interface and replies · Local Windows app · DeepSeek for online advice**

The Windows launcher and executable retain the name **Life Direction Agent** for compatibility. This source version introduces the graduate workbench; see [release status](docs/RELEASE_STATUS.md) for the distinction between this version and published downloads.

## Start with one role

1. Open the app and save a student profile with your study stage, target role and city, practised skills, and available time.
2. Use the market brief to research that role through mainland China primary sources. Inspect the dates, excerpts, and links before acting.
3. Paste a job description into the local comparison tool and compare its skill mentions with your saved profile. Use missing **mentions** to decide what to investigate or practise.
4. Add promising roles to the application tracker, record a next action, and export your CSV before ending the session.
5. Discuss your priorities in chat, create a checked plan for 1–365 days, and download it as Markdown.

A complete profile is useful but ordinary conversation remains available. The [student career guide](docs/STUDENT_CAREER_GUIDE.md) walks through an example and explains the tools.

## Local tools and online advice

| Feature | What it does | Connection needed |
| --- | --- | --- |
| Student profile | Keeps structured context for your current session | No |
| Job-description comparison | Finds supported skill keywords and compares them with your self-reported profile skills | No |
| Application tracker | Validates entries and imports/exports CSV | No |
| Market brief | Uses primary-source search and DeepSeek to discuss a role and market questions | Yes |
| Conversation and checked plan | Uses your conversation, saved profile, and retrieved source excerpts | Yes |
| Plan download | Saves the displayed checked plan as Markdown | No new request |

The comparison is a keyword aid, not an ATS score, competency assessment, or probability of getting hired. A portal link does not prove a vacancy is still open. Salary information is left unknown when the retrieved material does not support a relevant figure.

## Run on Windows

For a portable package, extract the whole `LifeDirectionAgent-v0.5.0-windows-x64.zip` folder and open `LifeDirectionAgent.exe`, keeping `_internal` beside it. The launcher opens a local browser page; keep it open while using the app and select **Quit** when finished. Python is included in a built portable package.

Published downloads are listed on the [Releases page](https://github.com/C1S9/career-planning-assistant/releases). The [Windows quick start](docs/WINDOWS_QUICKSTART.md) covers connection setup and troubleshooting.

To use online advice, enter **your own DeepSeek API key with available balance** under **Connection**, then select **Use for this session**. Source searches and model replies may incur API charges. The package includes no prepaid access.

## Sources, permissions, and limits

Mainland China research prioritizes the National College Student Employment Service Platform (NCSS/24365), the education and human resources ministries, and the National Bureau of Statistics. The app uses explicit trusted domains, scoped topic queries, and source links and excerpts that you can inspect. Official career-entry links remain available when a site requires a browser or login.

Research uses a general topic derived from bounded role and city choices; it does not copy your freeform profile, pasted job description, or application tracker into a search query. Saved profile context is sent to DeepSeek when you request advice. Chat text you send is also sent to the provider.

**Task fields and schedule checked** means the plan passed structural and scheduling checks and its source references match retrieved material. It does not establish that every statement is accurate or that the advice suits you. No source evidence means no fabricated checked plan.

Use **Permissions** to pause online requests or reduce per-request call limits. Call counts are not a spending cap, and an in-flight request can finish after a pause. [Read the permissions guide](docs/PERMISSIONS.md).

## Keep your work

Profiles, comparisons, applications, chat history, and activity records live in the current app session. The app has no accounts or application database. Export your tracker and plan before closing; a new browser session does not restore them automatically. CSV imports and downloads are deliberate local file actions, not cloud synchronization.

A pasted API key stays in session memory. **Forget session key** removes it; separately configured local credentials can still apply. Avoid putting contact details, identity numbers, confidential application records, or credentials into public examples.

## Develop from source

Direct dependencies remain pinned in [requirements.txt](requirements.txt). The new local tools reuse Pydantic and the Python standard library; no additional framework is required.

```powershell
git clone https://github.com/C1S9/career-planning-assistant.git
Set-Location -LiteralPath '.\career-planning-assistant'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address localhost
```

Enter your key in the app, or set `DEEPSEEK_API_KEY` and optional `DEEPSEEK_MODEL` privately. Never commit actual credentials. Stop the source server with Ctrl+C.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe scripts/build_windows.py
```

Automated unit tests use simulated provider responses. The build runs an offline packaged-app check and writes a ZIP, checksum, and report to `release/`. See [release status](docs/RELEASE_STATUS.md) for validation results and the generated build report for package checks.

## Explore the project

- [Student career guide](docs/STUDENT_CAREER_GUIDE.md): profile, market research, skill comparison, applications, and plans.
- [Source and tool research](docs/STUDENT_CAREER_RESEARCH.md): primary sources, access limits, and dependency choices.
- [Documentation index](docs/README.md): current guides and historical records.
- [Learning guide](docs/LEARNING_GUIDE.md): the earlier conversation architecture.
- [v0.5.0 notes](docs/releases/v0.5.0.md) and [changelog](CHANGELOG.md): version changes.
