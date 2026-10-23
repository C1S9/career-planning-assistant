# Keep your API key private

The app needs your DeepSeek API key to send requests. Treat it like a password: enter it in the app or keep it in local settings, and leave it out of source code, screenshots, and issue reports.

## Use a key for one session

Open **Connection**, paste your key into **DeepSeek API key**, and choose **Use for this session**. The app keeps that pasted key in session memory instead of saving it to a file. **Forget session key** removes the pasted key; a key supplied through local settings or an environment variable may still apply.

## Use local settings when running from source

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, then edit the copy locally. The example contains a placeholder; the real settings file is ignored by Git. You can also supply `DEEPSEEK_API_KEY` through a private process environment.

The connection uses this order: a pasted session key, then the environment variable, then the local settings file.

## Before committing or sharing files

Run these commands from the project folder:

```powershell
git check-ignore .streamlit/secrets.toml
git status --short
git diff --cached --name-only
```

The first command should show `.streamlit/secrets.toml`. Review the staged filenames before committing. Inspect the actual changes locally as well, but avoid copying output that might contain a key into a chat or bug report.

The repository's ignore rules cover real Streamlit settings, `.env` files, local Python environments, learner profiles, and installed learning-tool folders. Placeholder examples can be shared. Do not use `git add -f` to include a private settings file.

An ignore rule only keeps untracked files out of normal Git additions. It cannot remove a secret that was already committed. If a key is exposed, revoke it through the provider, create a replacement, and address the affected history or shared copy. Deleting the key from the latest file alone does not make the old key private again.

## What has been checked

For v0.4.0, the actual staged source changes and the generated Windows ZIP were checked for the configured local key and private file paths. Neither check found them. The package is assembled from an explicit list of public files; it does not include a user's settings file or prepaid API access. See the [release record](RELEASE_STATUS.md) for the checked version and artifacts.

This repository is public, so anyone can read the files committed here. Keep local settings and personal notes out of it.

These checks cover the files and key used in that release. Future changes still need review. Git's behavior is explained in the [official ignore documentation](https://git-scm.com/docs/gitignore).
