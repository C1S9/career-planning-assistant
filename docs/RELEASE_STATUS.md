# Current release

**v0.4.0 is available for Windows x64.** It was published on October 23, 2026, and adds permission controls and an activity view to the existing mentor conversations and action plans.

[Download v0.4.0](https://github.com/C1S9/career-planning-assistant/releases/tag/v0.4.0) · [Windows quick start](WINDOWS_QUICKSTART.md) · [Release notes](releases/v0.4.0.md)

## Which file to download

| File | What it is for |
| --- | --- |
| `LifeDirectionAgent-v0.4.0-windows-x64.zip` | The app, including its Python runtime. Extract the whole folder and open `LifeDirectionAgent.exe`. |
| `SHA256SUMS.txt` | The ZIP's checksum, if you want to verify your download. |
| `BUILD_REPORT.json` | Build details, source file hashes, and the packaged app's self-test results. |

The app runs on your computer and opens in your browser. Search and generated replies need an internet connection, your own DeepSeek API key, and available API balance. The Windows executable is unsigned.

## Checks completed for this release

- 88 automated tests passed without using paid API calls. The [GitHub check run](https://github.com/C1S9/career-planning-assistant/actions/runs/39929771650) also passed.
- A live test using fictional background information completed a chat reply and a three-day plan. Each used one search and one model call; its permission was revoked afterward.
- The packaged app passed checks for startup, its local page, bundled skills, plan validation, and permission enforcement with local test callbacks.
- The release's 17 runtime source files matched the published source at commit `778835e3da90619425189f23e477d452bcf19c98`.
- The 22 staged source changes and all 2,173 ZIP members were checked for the configured local API key and private file paths, with no findings.
- The uploaded release files matched their local SHA-256 checksums.

These checks describe this release. They do not guarantee the quality or personal suitability of every generated suggestion. Later documentation commits may appear after the release commit without changing the v0.4.0 executable.

## Updating from an older version

Download and extract the new package into a separate folder, then open its executable. Keep the included `_internal` folder beside it. There is no automatic updater, and a new app session does not restore an earlier conversation.

Earlier releases remain available on the [Releases page](https://github.com/C1S9/career-planning-assistant/releases).
