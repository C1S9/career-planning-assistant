# Version 0.2.0 — Verified Release Status

Release: [https://github.com/C1S9/career-planning-assistant/releases/tag/v0.2.0](https://github.com/C1S9/career-planning-assistant/releases/tag/v0.2.0)

Source commit: `9e90e72df9c2375280a6c06416dfe254f08cf906` · Tag: `v0.2.0`

## Download

Download `LifeDirectionAgent-v0.2.0-windows-x64.zip` from the release assets, extract the entire ZIP, and open `LifeDirectionAgent.exe`. Keep `_internal` beside it. The local app opens in the default browser. Use your own DeepSeek key in **Connection**; no Python installation or manual server deployment is required.

Archive size: 98,150,174 bytes.

SHA-256: `44f05a3775de09e09ac69aeb181a2d0ab3ed54412dd7e1158d724780721f725c`

## Confirmed Evidence

- Twenty-nine provider-independent application tests passed locally and in [GitHub Actions](https://github.com/C1S9/career-planning-assistant/actions/runs/39782805448).
- The tagged [Windows build workflow](https://github.com/C1S9/career-planning-assistant/actions/runs/39783627198) completed successfully, including its own frozen executable smoke check.
- A separate live learning-mentor call using fictional spreadsheet-learning context returned three tasks inside the selected three-day period, with fields and schedule checked by the actual parser.
- The local Windows package's isolated smoke test passed native launcher initialization, plan validation, localhost health, frontend JavaScript retrieval, and app-script execution with external Python removed from PATH and zero provider calls.
- All nine source-file SHA-256 values in `BUILD_MANIFEST.json` match the source commit named above.
- Browser checks covered the mentor selector, light and dark appearances, and the actual packaged app's viewer toolbar.
- The actual ZIP's 2,165 members were scanned for the configured local key and private file paths, with no findings. Git history was checked separately.
- GitHub's asset digests and byte sizes match the uploaded ZIP, checksum file, and build report. Release status is published, with the tag pointing to the verified source.

## Practical Limits

Windows x64 only. The executable is unsigned and has not been tested on every Windows configuration. Model replies require internet and authorized DeepSeek API access. Session-only chat and pasted credentials are not a persistent account service. One real plan check does not certify every mentor's advice quality. No hosted backend, background updater, application license grant, or Devpost submission was added.

See [Windows quick start](WINDOWS_QUICKSTART.md), [release notes](releases/v0.2.0.md), and the [offline app map](../devpost/app-map.html).
