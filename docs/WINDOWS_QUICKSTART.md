# Graduate Career Workbench — Windows quick start

Version 0.5.0 · Windows x64 · Launcher name: Life Direction Agent

The portable package runs locally and includes Python. The profile, job-description comparison, and application tracker work without an API key. Market research, chat, and generated plans require an internet connection and your own DeepSeek API key with available balance.

## 1. Open the package

1. Obtain the built `LifeDirectionAgent-v0.5.0-windows-x64.zip` and its checksum from the delivery accompanying this version. Use the [Releases page](https://github.com/C1S9/career-planning-assistant/releases) for published packages and [release status](RELEASE_STATUS.md) for version details.
2. Choose **Extract All** and extract the entire folder into a writable location, such as Documents.
3. Double-click `LifeDirectionAgent.exe`. Keep `_internal` beside it and do not launch from inside the ZIP.
4. Wait for the control window to report the app is ready. Select **Open app** if the browser does not open automatically.

The launcher retains the earlier Life Direction Agent name; the browser shows the graduate career workbench. Keep the launcher open while using the app. The server listens on `127.0.0.1`.

The executable is unsigned. If Windows shows a publisher notice, verify the package's source and compare its SHA-256 with the accompanying `SHA256SUMS.txt`.

## 2. Try the local job tools

Save a profile under **Your student profile**. Choose a mainland China target role and city, your study stage, goal, practised skills, and weekly preparation hours.

Open **Job tools**. Paste a job description and select **Compare skills** to inspect skill mentions and practice ideas. Add a target role to **Track applications**, then download its CSV. No model request is needed for these actions.

Changing and saving a profile starts a fresh chat and clears its prior brief and comparison. Application records remain in the current session.

## 3. Connect for advice

1. Open **Connection** in the sidebar.
2. Paste your own key into **DeepSeek API key**.
3. Leave **Model** as shown unless your account requires another model.
4. Select **Use for this session**.

No key or prepaid balance is included. Online calls use your account and may incur API charges. The pasted key stays in session memory; **Forget session key** removes it. Separately configured local credentials may still apply.

## 4. Research, discuss, and plan

Open **Market brief** for sourced role research. Read source dates and coverage, and confirm deadlines and eligibility on employer pages. Limited or missing evidence is shown as such; the app does not estimate pay from national averages.

Open **Career chat** to discuss your priorities. Your saved profile is sent as context. After a reply, use **Create a task plan** in the sidebar, choose 1–365 days, and select **Create checked plan**. Download the resulting Markdown if you want to keep it.

The app checks task fields, scheduling, and source references. These checks do not guarantee accurate advice or a job outcome. Additional mentor styles remain available.

## 5. Keep records and stop

Use **Download application CSV** before closing or refreshing. The tracker supports up to 200 records. Next time, import that CSV and select **Replace records with CSV**; a valid import replaces the current list. Imports accept files up to 3 MB.

Download plans and briefs you want to retain. The app stores no persistent conversation or application database.

Select **Quit** or close the launcher when finished. Closing only the browser tab leaves the local server running.

## If something gets stuck

- **The app will not open:** fully extract the ZIP and keep `_internal` beside the executable. Quit and reopen after a startup timeout.
- **A reply fails:** check the connection, key, model access, and balance, then use **Retry Reply** if offered. Retrying may incur another charge.
- **Online requests are paused:** enable **Allow online requests** under **Permissions** when ready. Local tools remain available.
- **No useful sources:** inspect the evidence status and use the official portals directly. An empty or blocked search is not evidence of an empty job market.
- **A CSV fails to import:** start with the app's exported header, preserve IDs, use valid dates/statuses and HTTPS links, and stay within 200 records and 3 MB. Existing records remain unchanged on validation failure.
- **The plan action is unavailable:** connect your account, share your situation, and resolve any pending reply first.

Startup logs are at `%LOCALAPPDATA%\LifeDirectionAgent\desktop.log`. Remove keys and personal details before sharing an error report.

Read the [student career guide](STUDENT_CAREER_GUIDE.md) for a fuller walkthrough and the [permissions guide](PERMISSIONS.md) for request controls.
