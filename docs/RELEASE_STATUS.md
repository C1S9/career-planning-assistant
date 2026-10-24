# Release status

The current source version is **v0.5.0**, the Graduate Career Workbench for mainland China internships and campus recruitment.

The [v0.5.0 notes](releases/v0.5.0.md) describe the student workflow. Published downloads are available from the [Releases page](https://github.com/C1S9/career-planning-assistant/releases). For a delivered portable package, inspect its accompanying BUILD_REPORT.json and SHA256SUMS.txt for build checks and the archive checksum.

## Windows package

| File | Purpose |
| --- | --- |
| `LifeDirectionAgent-v0.5.0-windows-x64.zip` | Portable app and included runtime. Extract the full folder before opening `LifeDirectionAgent.exe`. |
| `SHA256SUMS.txt` | Checksum for the built ZIP. |
| `BUILD_REPORT.json` | Build details, source hashes, and packaged-app self-test results. |

The Windows executable name remains unchanged. The package is unsigned. Online source searches and DeepSeek advice require the user's own key and available balance; local profile, comparison, and tracker tools do not.

Use the [Windows quick start](WINDOWS_QUICKSTART.md) and [student career guide](STUDENT_CAREER_GUIDE.md) for this version.

## Validation recorded on October 24, 2026

- 129 automated tests passed, including student context, real request boundaries with simulated HTTP, CSV edge cases, and Streamlit interaction tests.
- Live DeepSeek checks using fictional student details returned a sourced market brief, a career reply, and a checked three-day plan. Each used two searches and one model completion; all permissions closed afterward.
- The live sources were individual NCSS postings with unknown publication years. The brief identified those limits; this check does not establish live vacancy availability or representative market conditions.
- Playwright browser checks covered desktop and narrow layouts and the local bilingual skill comparison. The tracker uses its explicit, schema-preserving CSV download instead of generic table exports.
- The Windows x64 package passed its isolated self-test with external Python removed from PATH, including the launcher, server, app page, source filters, permissions, profile, skill comparison, CSV round trip, and advice export.
- All 20 runtime source hashes match the build manifest. The actual ZIP was scanned for the locally configured key and private filenames; no matches were found.

The package remains unsigned, and its offline self-test makes no paid API calls. Test fixtures and the live smoke checks use fictional data. API keys, personal profiles, tracker records, and generated build folders are excluded from the public source update.

## Earlier published release record

The prior project record identifies [v0.4.0](https://github.com/C1S9/career-planning-assistant/releases/tag/v0.4.0) as published on October 23, 2026. Its reported 88 automated tests, live chat/plan check, build verification, and asset checks belong to that version. They are not evidence for v0.5.0.

Earlier release details remain in the [v0.4.0 notes](releases/v0.4.0.md). Updating the source does not change an already published executable.
