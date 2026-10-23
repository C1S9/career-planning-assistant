# Life Direction Agent — Windows Quick Start

Version 0.4.0 · Windows x64

You need an internet connection, your own DeepSeek API key, and available API balance. Replies and source searches use your account and may incur charges. No separate Python installation is needed.

## 1. Download and open

1. Open the [v0.4.0 release](https://github.com/C1S9/career-planning-assistant/releases/tag/v0.4.0). Under **Assets**, download `LifeDirectionAgent-v0.4.0-windows-x64.zip`, rather than a **Source code** archive.
2. Right-click the ZIP and choose **Extract All**. Extract the whole folder somewhere writable, such as Documents.
3. Open that folder and double-click `LifeDirectionAgent.exe`. Keep `_internal` beside it. Do not run the app from inside the ZIP.
4. Wait for the launcher to say the app is ready. If your browser does not open automatically, select **Open app**.

Keep the launcher window open. The app runs on your computer at `127.0.0.1`; generated replies still need internet access.

## 2. Connect your DeepSeek account

1. In the browser, open **Connection** in the left sidebar.
2. Paste your key into **DeepSeek API key**. Leave **Model** as shown unless your account requires another model.
3. Select **Use for this session**.

No key or prepaid access is included. Check your available API balance in your DeepSeek account.

The pasted key stays in session memory and is not saved to disk. **Forget session key** removes it; separately configured local credentials can still apply. Enter it again in a new session. Your conversation is sent to DeepSeek for replies.

## 3. Start a conversation

Use **Choose your mentor** in the sidebar to pick an area: **Career & work**, **Life direction**, **Learning & skills**, **Habits & focus**, or **Communication & relationships**.

Describe your situation, what feels uncertain, and the time you have available. For example, with **Career & work**:

> I work in retail and want to explore a different career. I can spend two evenings a week on this. How could I start comparing a few options?

Send it using the box at the bottom of the page. The app searches primary sources before offering advice. Open **Sources consulted** below a reply for links and excerpts. Optionally choose a **Source region** under **Sources and skills** before your next message.

Changing mentors or selecting **New Conversation** clears the chat. History lasts only for the current session; copy anything you want to keep.

## 4. Turn the conversation into a plan

1. Share your situation and wait for the reply.
2. Open **Create a task plan** in the sidebar.
3. Set **Plan length (days)** from 1 to 365. Seven days is the starting value.
4. Select **Create checked plan**.

A successful plan has 3–8 tasks. **Task fields and schedule checked** means its required fields and dates passed the app's checks. Source references are checked against retrieved results. The label does not guarantee accurate advice or a plan that fits your situation.

## 5. Adjust the app

- **Appearance:** open the top-right app menu and choose **Light**, **Dark**, or **System**.
- **Online access:** under **Permissions**, clear **Allow online requests** to pause new calls once processed. Calls already in progress may finish.
- **Request limits:** under **Permissions**, reduce **Search calls per request** or **Model calls per plan** from 2 to 1. One model call leaves no allowance to correct a failed plan. These count attempts, not spending.
- **Activity:** **Recent activity** shows request counts and events. **New Conversation** clears this in-memory history.

For more detail, see the [permissions guide](https://github.com/C1S9/career-planning-assistant/blob/main/docs/PERMISSIONS.md).

## If something gets stuck

- **The app will not open:** fully extract the ZIP and keep `_internal` beside the EXE. If startup times out, select **Quit** and reopen the EXE.
- **Windows shows a publisher or SmartScreen notice:** this release is unsigned. Confirm the download came from the project's release page and compare its SHA-256 with `SHA256SUMS.txt` there.
- **A reply fails:** follow the error message. Check your connection, key, model access, and balance; wait if the service is busy. Then select **Retry Reply**. It retries your existing message or plan and may incur another charge.
- **Online requests are paused:** enable **Allow online requests** under **Permissions**, then select **Retry Reply** if shown.
- **No suitable sources were found:** if chat asks for more context, clarify your concern and check the source region. For a failed plan, select **Retry Reply** later or **New Conversation** to start again.
- **The plan button is unavailable:** enter your key, share your situation, and wait for a reply. Resolve any failed reply first.

Startup logs: `%LOCALAPPDATA%\LifeDirectionAgent\desktop.log`. To [report a problem](https://github.com/C1S9/career-planning-assistant/issues), describe what you clicked and the error shown. Remove keys and personal details from anything you share.

## When you are finished

Copy anything you want to keep, then select **Quit** or close the launcher window. Closing only the browser tab leaves the app running. Next time, open `LifeDirectionAgent.exe` again.
