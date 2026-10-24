---
doc: scope
status: draft
---

# Career Planning Assistant

## Current scope — v0.5.0

The user selected **mainland China students and recent graduates** as the audience, with internships and campus recruitment as the employment context. The app now centers on a student profile, role-and-city market research, practical skill preparation, application organization, and a downloadable action plan. The browser title is Graduate Career Workbench; the existing Windows launcher name is retained.

The current loop is: save student context, investigate a target role, inspect source evidence, compare skill mentions in a job description, record applications, and discuss a plan. The profile is optional background for conversation; a student can start with an uncertain direction. Additional mentor styles are optional support.

Included tools are bounded profile validation, cited market briefs, a local keyword comparison with portfolio practice ideas, session-only application records with CSV import/export, and Markdown advice downloads. Online work uses the existing DeepSeek connection and permission gateway. Local tools do not require paid calls.

Excluded from this increment: automatic applications or recruiter messages, a representative salary database, an ATS or hiring-probability score, persistent accounts, cloud synchronization, hosted service access, and guaranteed job outcomes. A published release, paid API access, formal document approval, and Devpost submission must each be evidenced separately.

The earlier sections below are retained as development history. Where they describe a broad audience or defer job tools, this v0.5.0 scope update takes precedence. Their historical approval statuses are unchanged.

## Historical scope record


Working title. A conversational AI assistant, powered by DeepSeek, that helps people uncertain about their employment future develop practical next steps.

## Confirmed Direction

The learner wants life guidance focused on employment and future direction, delivered through a chat interface with DeepSeek as the backend API. The desired outcome is an actionable task list. Planning periods can be short or long. Education, age, and work situation provide background. All authored project content must use English.

The learner requested planning documents first and then hands-on guidance to build a runnable agent. The conversation format and DeepSeek provider are explicit learner choices. Other detailed recommendations remain draft proposals.

## The Unique Kernel

A guided career conversation becomes a task plan: the assistant learns about the person's situation, helps clarify uncertainty, and turns the discussion into a sequence of actions for the requested period. Personal background should influence practical suggestions without pretending to predict the person's future.

## Who It's For

Someone uncertain about their future employment direction who wants to discuss the problem and leave with a concrete next action. A narrower audience has not been chosen.

## The Core Loop

The person describes a concern in chat. The assistant asks a focused follow-up about relevant background or goals, using earlier answers instead of repeating questions. Once sufficient context and a planning period are available, it offers a task plan. The person can discuss a task or request a revision in the same conversation.

## Inspiration & Identity

Use a familiar message history and text composer. Interface text, system instructions, and generated descriptions use English. No brand name or visual reference has been approved. A readable, calm single-page layout is a suggested starting point.

## Why This Matters to the Learner

The learner wants to help people who feel lost and learn how to build a working AI agent with step-by-step guidance.

## What "Working" Looks Like

Proposed demo: a fictional user describes employment uncertainty, answers a follow-up, and receives a task plan. Asking a follow-up about one task should demonstrate that earlier context is retained. A revised planning period should produce an appropriately revised plan.

A real DeepSeek reply is necessary to prove the core connection. A local greeting or test fixture is not evidence that the API works. A task plan supports exploration; it does not guarantee employment.

## The POC Boundary

One local chat page, one conversation per browser session, real DeepSeek replies, conversational background gathering, and task planning. Build the live conversational connection before adding structured plan checks.

Proposed initial planning limits: 1–365 days and 3–8 tasks, each with a concrete action, timing, relevance, and completion criterion. These numerical limits are recommendations awaiting review.

## Later

Persistent histories, accounts, reminders, external job-board tools, and autonomous execution are not required for this proposed first version. None has been requested.

## Explicitly Cut

The earlier proposed mandatory background form is superseded by the learner's chat requirement. DeepSeek replaces the earlier proposed model provider. No learner-requested outcome has been removed.

## Review Notes

Confirmed choices: chat interface, DeepSeek API, career uncertainty, actionable tasks, variable plan length, background categories, English project content, and guided learning.

Pending: working name, visual details, numerical limits, exact model, and final validation behavior. Keep this file in draft until the full scope is reviewed; implementation milestones must not be confused with formal document approval.

## Submission Context

The public repository must contain the working project and `scope.md`, `prd.md`, and `spec.md`. The submission also needs a description and a public demonstration video under three minutes. Planning documents alone do not complete the submission. Source: [Official rules, section 4](https://learn-ai-basics.devpost.com/rules).


## Checked-Plan Implementation Update

The current implementation retains the confirmed chat format and adds an explicit duration selection and checked-plan action in the same page. It uses the existing conversation as context and validates the returned plan against the saved selection. The learner has demonstrated ordinary multi-turn chat with seven-day and three-day outputs; the learner has now reported a successful live checked-plan test, without supplying its full generated output for independent review. This implementation update does not mark all draft recommendations approved.


## Version 0.2.0 — Authorized Expansion

The learner explicitly requested mentor presets for different life-consultation needs, a simpler practical interface, Git synchronization, a new version, and a Windows executable release that does not require users to deploy the app. This updates the earlier career-only PoC boundary. The initial presets are career and work, life direction, learning and skills, habits and focus, and communication and relationships. They use the same DeepSeek API with distinct instructions; they are not newly trained models.

The release boundary is one browser chat UI and a portable Windows launcher that starts a loopback-only server. Users extract a ZIP and run an exe without installing Python. Internet access and the user's authorized DeepSeek API key remain necessary. No shared owner's key, hosted backend, offline model, persistent database, account system, or background updater is added.

Mentor changes start a fresh conversation. Checked action plans retain the existing 1–365-day, 3–8-task validation rules. Native light/dark themes and sidebar controls simplify the visible flow. This records the new authorized work without retroactively inventing approval of every earlier draft recommendation.
