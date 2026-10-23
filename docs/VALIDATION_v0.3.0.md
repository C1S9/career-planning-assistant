# Version 0.3.0 validation record

Checked on 2026-10-23.

- 57 offline application tests passed, including provider failures, retrieval boundaries, topic privacy, citation identities, UI source rendering, mentor isolation, required skill loading, and plan fields/schedules.
- All three runtime SKILL.md files passed the official skill-creator format validator. Its YAML dependency was installed only in a separate maintainer tooling directory.
- Live DeepSeek search and chat with fictional business/retail context returned a cited reply referencing three retrieved primary-source pages.
- A separate live checked-plan request returned three tasks inside the selected three-day period and passed actual source-reference and schedule validation.
- A China-topic search returned usable page content from Chinese government domains.
- The live test used no real personal case. These results demonstrate the tested request paths, not universal advice quality or factual entailment.

For the exact Windows offline self-test, consult BUILD_REPORT.json distributed with the release. It checks bundled skills, source URL filtering, launcher initialization, localhost health, frontend assets, and application execution with external Python removed from PATH. No paid requests occur in that packaged check.
