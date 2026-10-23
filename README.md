# Life Direction Agent

Talk through a career move, a learning goal, a difficult conversation, or a next step you haven't quite figured out. Life Direction Agent offers five mentor styles to help you explore your options and turn a conversation into a manageable action plan.

**v0.4.0 · English conversations · Windows portable app · Powered by DeepSeek**

## Get started on Windows

You'll need an internet connection and **your own DeepSeek API key with available balance**. Model replies and source searches use your account and may incur API charges; the download does not include prepaid access.

1. Open the [v0.4.0 release](https://github.com/C1S9/career-planning-assistant/releases/tag/v0.4.0) and download `LifeDirectionAgent-v0.4.0-windows-x64.zip`.
2. Extract the entire ZIP, keeping the `_internal` folder beside `LifeDirectionAgent.exe`.
3. Double-click `LifeDirectionAgent.exe`. The launcher opens the app in your browser; keep the launcher open while you use it, then select **Quit** to stop it.
4. In the app's sidebar, open **Connection**, paste your key, and select **Use for this session**.

Python and the other dependencies are included in the download. The executable is unsigned, so Windows may show a publisher warning. The [Windows quick start](docs/WINDOWS_QUICKSTART.md) covers checksums, connection setup, and troubleshooting.

## Start with what's on your mind

Choose **Career & work** and try a message like this:

> I'm thinking about leaving retail, but I'm not sure what kind of work would suit me. I enjoy helping people and organizing things. I can spend about three hours a week exploring options, and I need to keep earning while I do it. Can you help me work out a first step?

Share as much context as you're comfortable with: what you want to change, what you've tried, and the time or other constraints that matter. You can ask follow-up questions and discuss suggested tasks before deciding what to do.

## Choose a mentor

| Mentor | A useful place to start |
| --- | --- |
| **Career & work** | Exploring a career move, preparing a job search, or weighing a work decision |
| **Life direction** | Clarifying priorities, comparing options, or trying a small experiment |
| **Learning & skills** | Setting a learning goal and finding a practice routine that fits your life |
| **Habits & focus** | Getting started on tasks, reducing friction, or building a sustainable routine |
| **Communication & relationships** | Preparing a conversation, setting a boundary, or working through a disagreement |

Each mentor uses a different set of coaching instructions with the same DeepSeek backend. Switching mentors starts a fresh conversation. **New Conversation** clears the current one.

## Turn the conversation into a plan

After sharing your situation, open **Create a task plan** in the sidebar, choose **Plan length (days)** from 1 to 365, and select **Create checked plan**.

A plan contains 3–8 tasks, each with an action, timing, a reason, and a way to tell when it's done. The app checks required fields, day order, the selected time period, and source references. If those checks pass, it displays **Task fields and schedule checked**. This checks the plan's structure; you'll still need to judge whether its advice fits your circumstances.

## What happens when you send

1. Your send, plan, or retry authorizes a limited request to DeepSeek.
2. The app searches for primary sources using a predefined general topic and your optional **Source region**, rather than copying your message into the search query.
3. It sends your conversation, the selected mentor's instructions, and retrieved excerpts to the model, then checks source identifiers and links before displaying the reply.

Open **Sources consulted** below a reply to inspect the links and excerpts. If suitable sources aren't available, the app returns a clarification notice and won't generate a checked plan. Source checks confirm references match the retrieved material; they don't verify every claim.

Use **Permissions** to pause online requests or lower call limits, and **Recent activity** to see request counts. Call limits aren't a spending cap, and pausing can't recall a call already in progress. The [permissions guide](docs/PERMISSIONS.md) explains the details.

## Privacy and limits

- The app runs locally, while DeepSeek processes your conversation to generate replies.
- A key pasted into **Connection** stays in session memory and isn't saved to disk. **Forget session key** removes it; any separately configured local credentials still apply.
- Chat history and activity records live in memory for the browser session, with no application chat database. Save anything you want to keep before ending the session, and leave keys and personal conversations out of public bug reports.
- The mentors provide general coaching, not professional medical, legal, or financial advice. Retrieved sources and checked schedules don't guarantee accuracy, suitability, or outcomes.

## Run or develop from source

The development setup has been checked with Python 3.15.0. Direct dependencies are pinned in [requirements.txt](requirements.txt).

```powershell
git clone https://github.com/C1S9/career-planning-assistant.git
Set-Location -LiteralPath '.\career-planning-assistant'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address localhost
```

Open the local address shown in the terminal and enter your key through **Connection**. Stop the server with Ctrl+C. You can also configure `DEEPSEEK_API_KEY` and optional `DEEPSEEK_MODEL` through environment variables or a local `.streamlit/secrets.toml` copied from the example file. Keep real credentials out of Git.

To run the tests and build the Windows package:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe scripts/build_windows.py
```

The tests use simulated provider responses, so they don't spend API credit. The Windows build includes an offline smoke check and produces a ZIP, checksum, and build report in `release/`.

## Explore the project

- [Documentation index](docs/README.md) — find the right guide and distinguish current docs from older records.
- [Learning guide](docs/LEARNING_GUIDE.md) — follow a message through the code and learn how the pieces fit together.
- [Evidence and coaching skills](docs/EVIDENCE_AND_SKILLS.md) — how sources are selected and coaching instructions are loaded.
- [Permissions and execution boundaries](docs/PERMISSIONS.md) — how requests, call budgets, and activity records work.
- [v0.4.0 release notes](docs/releases/v0.4.0.md) and [changelog](CHANGELOG.md) — what changed between versions.
