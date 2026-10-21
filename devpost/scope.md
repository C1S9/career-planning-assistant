---
doc: scope
status: draft
---

# Career Planning Assistant

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
