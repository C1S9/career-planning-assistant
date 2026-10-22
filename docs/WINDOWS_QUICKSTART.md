# Life Direction Agent — Windows Quick Start

Version 0.2.0 · Windows x64 · Portable application

## Open the app

1. Download `LifeDirectionAgent-v0.2.0-windows-x64.zip` from the GitHub Release.
2. Extract the entire ZIP to a folder you can write to. Do not run it from inside the ZIP.
3. Double-click `LifeDirectionAgent.exe`. Keep its `_internal` folder beside it.
4. The launcher opens the app in your default browser. Its server listens only on `127.0.0.1`.
5. Keep the small launcher window open while using the app. Select **Quit** to stop it.

You do not install Python, Node.js, Streamlit, or a separate server. Internet access and authorized DeepSeek API access are still required for generated replies. This is a local app, not an offline language model or a hosted service.

## Connect to DeepSeek

Open **Connection** in the sidebar, paste your own DeepSeek API key into the password field, and select **Use for this session**. The pasted key stays in this browser session; the app does not save it to disk. Set it again after starting a new browser session. Existing private environment settings can also supply credentials.

No owner's key or prepaid model access is included in the release. API charges belong to the account whose key you use. **Forget session key** removes a pasted session key; a separately configured environment or local setting can still apply.

## Choose a mentor

- **Career & work:** career exploration, work decisions, and job-search preparation.
- **Life direction:** priorities, values, and manageable experiments.
- **Learning & skills:** practice routines and learning goals.
- **Habits & focus:** sustainable routines and reducing friction.
- **Communication & relationships:** clearer conversations and boundaries.

Changing mentors starts a fresh conversation. **New Conversation** resets the current mentor's thread. Conversations are session-only; there is no account or persistent chat database.

## Make a checked action plan

Describe your situation, then open **Create a task plan**, choose a period from 1 to 365 days, and select **Create checked plan**. The app checks 3–8 tasks, required fields, and schedule bounds before adding its checked label. This label does not certify personal suitability or promise outcomes.

Open the top-right app menu and select **Light**, **Dark**, or **System**.

## Troubleshooting

- Keep the exe and `_internal` together. Re-extract the complete ZIP if a file is missing.
- The launcher may take a few moments to start. Select **Open app** if the browser did not open automatically.
- App startup logs are under `%LOCALAPPDATA%\LifeDirectionAgent\desktop.log`. Avoid sharing personal conversation text or credentials in reports.
- A network, quota, or credential error is shown in the app; use the explicit retry action after resolving it.
- The executable is not digitally signed. Windows may display a publisher or SmartScreen notice. Obtain it from the project release and compare the ZIP's SHA-256 with the published checksum.

The release does not submit a Devpost entry or install a background updater. Future versions are published as new GitHub Releases.
