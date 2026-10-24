---
doc: prd
status: draft
---

# Career Planning Assistant — Product Requirements

## Current product requirements — v0.5.0

**Audience:** mainland China students and recent graduates seeking internships, graduate roles, or career exploration. English interface and generated guidance remain the project convention.

**Primary journey:** save a study profile, choose Career chat / Market brief / Job tools, investigate a role, compare a real posting, track the next application action, and download an actionable plan.

| Capability | Required behavior |
| --- | --- |
| Student profile | Validate study stage, role, city, goal, selected skills, optional major, and 1–40 preparation hours per week. Apply only on explicit save. Changed context starts a fresh conversation and clears stale research/comparison. |
| Market brief | Use bounded role/city/goal topic terms and mainland China primary sources. Distinguish source observations from suggestions, show dates and coverage limits, and keep missing pay evidence unknown. |
| Job-description tool | Compare up to 12,000 characters against supported skill aliases and self-reported profile skills. Show original excerpts and practice ideas. No ATS score, skill certification, or hiring prediction. |
| Application tracker | Add records, update status/notes, remove records, export CSV, and atomically replace from valid CSV. Maximum 200 records and 3 MB per import; no tracker contents sent to DeepSeek. |
| Action plan | Retain checked 1–365-day plans with 3–8 tasks and download Markdown with the associated source record. |
| Failure and privacy | Keep local tools available without a key. Display research gaps and safe errors. Preserve current tracker records on failed import. State session-only retention and per-request charges. |

A complete profile is helpful but not a prerequisite to ordinary conversation. Study-stage choices do not establish an employer's graduation-year eligibility. A salary or deadline needs a relevant current source; an official portal link alone is not verification.

Existing source panels, optional mentors, retries, permission controls, and offline packaging remain. This implementation increment does not mark the historical draft agreement approved.

## Historical product record


A DeepSeek-powered conversation that helps a person uncertain about their employment future work toward an actionable task plan.

## Decision Status

Learner-confirmed: chat interaction, DeepSeek API, employment and future direction, task-based output, flexible duration, education, age, and work context, and English project content. Detailed behavior below is a proposed implementation agreement awaiting review. Source: `scope.md > Confirmed Direction`.

## The Core Journey

1. Open the page and see a short welcome question with an empty message composer.
2. Describe an employment concern and send it.
3. See the submitted message and a visible waiting indicator, followed by a genuine DeepSeek reply.
4. Continue a conversation. The assistant asks one relevant question at a time, learns education and work context and optionally age, and asks how long the plan should cover. It does not repeat facts already supplied or invent missing facts.
5. Request a plan when ready. If the planning period or essential background is missing, the assistant clarifies it rather than claiming to have a personalized plan.
6. Receive conversational guidance, or expand **Create a task plan**, select **Plan length (days)**, and use **Create checked plan**. Checked plans are validated before appearing in the same thread, where the person can discuss them.
7. Start a new conversation when desired. A new conversation does not inherit the previous session's messages.

Source: `scope.md > The Core Loop` and `What "Working" Looks Like`.

## Screens and Layout

One page with a title and short purpose statement, a message history with visually distinct user and assistant messages, and a composer. A **New Conversation** control resets the active thread. The page includes a compact **Create a task plan** section with an explicit duration selection and **Create checked plan** action. Results appear as assistant messages; separate form and results pages are unnecessary.

## Look and Feel

Confirmed: English interface copy and generated descriptions. User-entered text may contain other languages. Suggested: light background, dark text, readable typography, restrained accents, and comfortable spacing. These visual details remain proposals.

## Features and Behavior

### Conversation and Context

Each successful reply uses the current conversation history. Retain the conversation in the current application session. Do not promise durable restoration after closing or refreshing the session.

- Sending a message adds it once and requests one reply; ordinary page reruns do not call the provider again.
- Display a waiting state while work is pending and block duplicate submissions.
- A follow-up referring to an earlier stated education or work detail should receive a relevant answer without asking for the same detail again.
- **New Conversation** restores the initial welcome and clears prior user content from subsequent requests.

Source: `scope.md > The Core Loop`.

### Guided Career Consultation

Use a supportive, practical tone and one focused question at a time. Learn relevant education, age context if volunteered, work situation, concerns, and preferred planning period through conversation. Accept no prior work experience and a preference not to disclose age. Use known context instead of requiring a questionnaire to be completed.

Do not infer career suitability from age alone, fabricate qualifications, or claim to have checked current vacancies. If the user wants a plan before enough context exists, identify the missing information or label any provisional assumptions.

Source: `scope.md > Who It's For` and `The Unique Kernel`.

### Actionable Task Plan

Proposed plan: a brief summary, explicit assumptions, and 3–8 ordered tasks. Each task states an action, start and end days, why it matters, and observable completion evidence. The proposed duration range is 1–365 days.

- The first task starts on day 1.
- All tasks fit the requested period: `1 <= start_day <= end_day <= duration_days`.
- A seven-day plan contains no task scheduled after day 7.
- A longer plan may use milestones rather than a task for every day.
- Task content visibly reflects the person's education, work situation, or stated concern.

The checked-plan action saves the selected duration with its request, asks for JSON, validates required fields and timing, and permits at most one correction request for a structural failure. Only a successfully validated result receives the **Task fields and schedule checked** label. Ordinary conversational text has no such label. Editing the duration alone does not request a plan; a failed plan is not displayed as checked, and explicit retry retains the original selected duration.

The control uses the current conversation as background, is disabled until a user message exists, and is disabled while a reply is pending. Missing background is labeled as an assumption rather than invented. Schedule validation does not certify practicality, employment outcomes, or the truth of career claims.

Source: `scope.md > What "Working" Looks Like` and `The POC Boundary`.

## States and Boundaries

| State | Expected behavior |
| --- | --- |
| Welcome | Show purpose, a starter question, and a composer |
| Waiting | Show progress and prevent repeated sends |
| Successful reply | Display and retain one assistant message |
| Failed reply | Retain the user's message, show a clear error and an explicit retry option; do not append an error as model advice |
| Missing setup | Explain that model access needs configuration before the conversation can be sent |
| Invalid input | Reject empty messages and proposed messages over 4,000 characters without a provider request |
| Session limit | Before exceeding the proposed 40 submitted user turns or 60,000 conversation characters, ask the person to begin a new conversation; do not silently remove essential context |
| New conversation | Clear prior user context and return to the welcome state |

No shared chat history or persistent personal database is proposed. Explain before the first sent message that the conversation is sent to DeepSeek. Do not record full chats or keys in application logs.

## Product Decisions

The learner explicitly selected DeepSeek and a chat format after reviewing the earlier direction. This supersedes the earlier background-form proposal and provider recommendation. Career focus, task output, duration flexibility, background categories, and English content remain unchanged.

Proposed for review: limits, visual direction, retry interaction, and task schema. No final brand name has been chosen.

## What We're Building

One conversational path from employment uncertainty through background clarification to a practical plan, using a genuine model connection and an explicit new-conversation control.

## Deferred From the POC

Accounts, persistent history, reminders, job-board integration, uploads, and automatic execution. These have not been requested and are not needed to demonstrate the core conversation.

## Acceptance Demonstration

Use fictional information. State a degree and work history, answer a follow-up, then refer back to that background and inspect whether context is used. Ask for a seven-day task plan and then a ninety-day revision. Verify schedule bounds. Start a new conversation and verify prior facts are absent. Simulate a provider failure separately and confirm retry does not duplicate the user's message.

These are future checks, not completed testing or learner personal information.

## Open Questions

Live ordinary-chat use and a contextual revision have been reported by the learner. The learner also reported that the live checked-plan test succeeded and indicated that the chat functionality is sufficient. Before treating the full plan as approved: review proposed limits, task validation, and appearance. Before publication: the learner chooses the final name and writes submission fields in their own words.


## Version 0.2.0 — Mentor and Desktop Journey

The learner requested the expansion recorded in `scope.md > Version 0.2.0 — Authorized Expansion`.

1. Extract the portable Windows ZIP and open the exe, or run the source checkout.
2. The native launcher starts a local server and opens the default browser. Closing the launcher stops the owned process.
3. Choose one of five mentor presets from the sidebar. Display its purpose and tailored greeting. A change resets previous conversation, pending reply, and selected plan duration without making an API call.
4. Use an existing private setting or enter a DeepSeek key through a password field. A pasted key lasts only for this session; it is not persisted or bundled.
5. Converse with the chosen mentor, then create a checked action plan using that same mentor and the saved period.
6. Switch between native light and dark appearances from Settings. Settings, rerenders, or mentor changes alone do not authorize a model request.

The main canvas remains a readable conversation. Mentor, connection, and plan controls are in the sidebar. Application labels, prompts, comments, help, and release documentation remain English. The packaged app requires neither Python installation nor a user-managed deployment, but still requires internet and API access. The release ZIP includes all support files; moving only the exe is unsupported.
