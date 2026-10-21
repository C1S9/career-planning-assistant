---
doc: checklist
status: draft
---

# Build Checklist

Build mode: learn, matching the learner's request for hands-on, step-by-step guidance.

The learner explicitly selected chat and DeepSeek. Full planning-document and build-order approval remain pending; this record does not silently approve unreviewed recommendations. Environment verified: Python 3.15.0, Streamlit 1.66.0, OpenAI client 3.35.1. The initial demo snapshot was published to the private GitHub repository and verified at `8106f8acf888e462187e0bd040fdf702e43d05c5`; formal planning approval remains pending.

## Slices

- [ ] **1. Discuss a career concern with a real DeepSeek reply**
  Becomes usable: A local chat that accepts a message and answers with retained conversation context.
  Why now: Proves the chosen provider and conversation flow before adding detailed task-plan machinery.
  PRD ref: `prd.md > Conversation and Context`, `prd.md > Guided Career Consultation`
  Spec ref: `spec.md > Chat Page — app.py`, `spec.md > DeepSeek Conversation — agent.py`
  Build: Create the chat page, session history, private key configuration, DeepSeek request, explicit retry, and new-conversation action.
  Verify (mechanical): Run provider-independent tests and Streamlit UI checks. After private setup, obtain a real reply and a contextual follow-up.
  Learner check: Open the page, configure the key privately, discuss a fictional career concern, ask a follow-up, and report what happened.
  Commit: `Add DeepSeek career conversation`

- [ ] **2. Leave the conversation with a checked task plan**
  Becomes usable: A concrete short or long plan with independently checked task fields and schedule bounds.
  Why now: Builds the project-specific outcome on a working conversation.
  PRD ref: `prd.md > Actionable Task Plan`
  Spec ref: `spec.md > Checked Task Plan — models.py and agent.generate_plan`
  Build: Review remaining product limits, verify DeepSeek structured output, and add plan validation with bounded correction.
  Verify (mechanical): Check seven-day and ninety-day plans, invalid schedules, and a failed correction path.
  Learner check: Request a plan, inspect the next action, revise its period, and report whether it is useful.
  Commit: `Add validated career task plans`

## Hands-on Checkpoints

- [x] Early usable chat opened and explored by the learner — the learner reported success and shared a generated plan
- [x] A real reply reported and shared by the learner
- [x] A contextual follow-up verified in the same conversation — the learner shared a three-day revision retaining the earlier fictional background
- [ ] Final task-plan journey explored and feedback completed

## Final Review

- [ ] Final review complete — agreed feedback resolved and learner confirms readiness

## Code Tour and App Map

- [ ] Guided route through one real message and reply completed
- [ ] Optional edit and transfer reflection addressed
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown

Activity and evidence: Environment imports verified; application checks and learner feedback are tracked below as they occur.
Route and stops: Planned route is `app.py` -> `agent.reply` -> `prompts.SYSTEM_PROMPT`.
Edit outcome: Not yet offered.
Reflection: Not yet offered.
Activity mode: Planned live app and editor.

## Current Verification Evidence

- Nine provider-independent tests passed using Python 3.15.0, Streamlit 1.66.0, and OpenAI client 3.35.1.
- Checks cover context assembly, input and conversation bounds, empty and incomplete output, safe provider errors, page welcome and setup state, reruns without extra calls, conversation reset, and retry without a duplicate user turn.
- All model replies in the automated checks were simulated. Separately, the learner reported successful live use and shared a seven-day plan. No key value is displayed or stored in this public record.
- The learner has supplied the multi-turn follow-up. The first Git publication checkpoint is complete. Formal plan approval remains pending, so slice 1 stays unchecked.

## Revisions

- The learner selected a conversational DeepSeek backend, replacing the earlier form-first provider proposal. Structured task validation remains a later milestone.
- Added an explicit checked-plan action with a selected duration so the program can compare model output against a known user-controlled period. Ordinary chat stays available. This supersedes the earlier later-milestone note; live use of the new action remains to be verified.

## Learning Documentation Update
Added docs/LEARNING_GUIDE.md and explanatory English comments to app.py, agent.py, and prompts.py at the learner's request. Verified that executable Python structure is unchanged after excluding docstrings, and reran the same nine provider-independent tests successfully. A placeholder-only private settings file is prepared when absent; no real key is inspected. A live reply has since been reported by the learner; contextual follow-up and the guided code-tour activity remain pending.

## First Learner-Reported Live Result
The learner shared the response to the fictional business-degree and retail-experience scenario: three tasks scheduled on days 1-2, 3-5, and 6-7. Manual review confirmed three tasks, a day-1 start, and no schedule beyond day 7. Each task included an action, relevance, and completion evidence, with provisional assumptions stated. This is learner-supplied live-result evidence, not an independently executed network test or software plan validation. Next, revise the same conversation to a three-day period and check retained context.

## Contextual Revision and Checked-Plan Implementation

The learner supplied the follow-up result: the same three task themes were reduced to days 1, 2, and 3, retaining the fictional business-degree and retail background. Outreach completion was narrowed to sending a message. This verifies the reported live conversational revision; it is distinct from the new structured-plan operation.

The checked-plan implementation passed 22 provider-independent tests, including period bounds at 1 and 365 days, three-day and ninety-day plans, task counts, field checks, mismatched periods, bounded correction, no correction on connection failure, and UI retry without duplicate user messages. The learner has now reported a successful live checked-plan test; no full output was supplied for independent review. No real key was read or changed for this feature.

The learner completed the requested three-day checked-plan test and reported success. A follow-up request for usability feedback received the response that chat functionality is sufficient. The draft planning records and remaining learning-wrap-up status are not silently marked approved or completed.

## Private Demo Publication

The learner requested publication and selected a private repository. The initial demo snapshot was uploaded to [https://github.com/C1S9/career-planning-assistant](https://github.com/C1S9/career-planning-assistant) and verified at `8106f8acf888e462187e0bd040fdf702e43d05c5` against the local commit, the exact file-tree hash, and all 20 tracked file paths. The actual staging area was checked for the configured key before committing; private settings and the learner profile were excluded. Normal Git transport failed, so an authenticated GitHub API fallback completed the upload without forcing remote history. Documentation was then updated to reflect this checkpoint. The publication does not close the pending live checked-plan result, formal planning review, code tour, or Devpost submission.

## Learner-Reported Checked-Plan Success

The learner reported that the three-day checked-plan test succeeded. The full generated plan was not supplied for independent content review. The learner then indicated that the chat functionality is sufficient; no additional chat feature was requested. This records the observed success report, without claiming an agent-run live call, a complete advice-quality audit, or blanket approval of all draft recommendations.

The offline `devpost/app-map.html` is prepared as a reference route against source commit `34c700c5e6021a581038b2faa24fa612cff53e25`. Paths and source anchors were checked. The learner requested proceeding with the existing chat, so no extra feature or compulsory hands-on exercise was added. An interactive tour, optional edit, and personal reflection were not performed; the map must not be described as evidence that they were. Public visibility, license approval, video recording, and Devpost submission remain pending.


## Public Repository Checkpoint

The owner explicitly requested public visibility. [https://github.com/C1S9/career-planning-assistant](https://github.com/C1S9/career-planning-assistant) is now public. GitHub's authenticated repository metadata confirmed the visibility change, and an unauthenticated read of the raw README matched the reviewed Git blob hash. The anonymous REST API quota was exhausted, so the raw-file access check supplied the separate anonymous-access evidence.

Before changing visibility, all seven locally reachable commits and 31 historical blobs were scanned for the configured API key, common long credential patterns, and private file paths, with no findings. The local and remote `main` commit and all 21 file paths matched. Subsequent documentation changes receive their own staging and history checks. These are targeted checks, not proof against every possible credential format.

No application behavior or license was changed. License selection, the learner-created demo video and submission answers, and Devpost submission remain unfinished.
