# API Key and Git Protection Check

## Current Result

The demo was published to the [private GitHub repository](https://github.com/C1S9/career-planning-assistant) on branch `main`. The initial uploaded snapshot, `8106f8acf888e462187e0bd040fdf702e43d05c5`, was verified against the local commit and all 20 tracked file paths. Before publication, its exact staging area was checked for the configured local key and unintended private files. Documentation updates receive the same staging checks before publication.

The private DeepSeek setting remains in the local `.streamlit/secrets.toml` file. Its contents were not printed, copied into deliverables, or staged.

## Evidence

- The actual Git staging area was inspected, rather than relying only on `.gitignore` text.
- All 20 staged files were compared in memory against the configured local API key and checked for long `sk-` key literals. No matches were found. The checker reports file paths and result categories, never credential values.
- A separate local text scan inspected 49 project files and reported no matching key in shareable text.
- Git confirmed exclusion of `.streamlit/secrets.toml`, `devpost/learner-profile.md`, local environment files, the Python environment, and installed learning-tool directories.
- `.streamlit/secrets.toml.example` contains a placeholder only and is eligible for publication.
- The staged changes passed `git diff --cached --check`.
- All 22 automated application tests passed with simulated provider responses. These checks do not spend API credit or establish live provider availability.

## Rules to Keep

Keep real credentials in the ignored settings file or private process environment. Review the actual staged changes before every commit. Do not force-add a private file, paste a key into source code, or publish terminal output containing a key.

Installed learning tools remain local; `skills-lock.json` records their sources. The source, tests, requirements, English planning documents, and learning guide form the demo snapshot.

This targeted check covers the current staging area and matching local text. It does not audit other repositories, external uploads, arbitrary credential formats, or future changes. Ignore rules do not remove an already committed credential; see the [official Git ignore documentation](https://git-scm.com/docs/gitignore).

## Publication Verification

The normal Git transport was reset by the network, so the reviewed snapshot was published through the authenticated GitHub API. The remote file-tree hash matched the reviewed local tree. The remote commit was reconstructed and hash-verified locally, and the remote branch and tracked-file list were checked again. No remote history was force-updated. The original unpublished local commit remains on `demo-before-api-upload`. Credentials were used in memory and were never written to these documents or printed.


## Owner-Authorized Public Visibility

The owner authorized making [https://github.com/C1S9/career-planning-assistant](https://github.com/C1S9/career-planning-assistant) public. Before the change, the history check covered seven locally reachable commits and 31 unique blobs, with no configured-key, common long-token, or private-path findings. The remote had 21 tracked files and matched local `main`.

GitHub confirmed `private: false`. An unauthenticated raw README request succeeded and matched its expected Git blob hash. Anonymous REST API requests were rate limited, so public-file access was checked separately. The private settings and learner profile remain ignored and absent from the reviewed repository history. Later documentation updates are scanned before publication. No key value is printed in this report.
