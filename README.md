# 🚀 save-to-github-skill

One-command GitHub sync for Claude Code. Type `/save!` and your code flies to GitHub.

## 🔑 First-Time Setup

On first use, a GitHub login window pops up automatically. Copy the one-time code, press Enter to open your browser, and authorize. Easy peasy 🍋

![GitHub Login](images/7febc35289f43c962cc555b6326dd8f5.png)

You only need to do this once. After that, it's all autopilot ✈️

## ✨ Features

- 🟢 **One-click sync** — auto add, commit, and push
- 🗑️ **Smart delete handling** — asks once per deleted file, remembers your choice forever
- ✅ **Push confirmation** — Push / Cancel / Change remote before anything leaves your machine
- 📂 **Manage remote files** — view and cherry-pick files to remove from GitHub
- 🔀 **Change remote** — switch target repo anytime, mid-flight
- 🆕 **Auto-create repos** — repo doesn't exist? No worries, we'll make one
- ⚙️ **Auto-setup** — installs gh CLI and opens login on first use (Windows)
- 🔒 **Sensitive file protection** — .env, credentials, keys? Skipped automatically
- 📦 **No git repo? No problem** — asks to initialize one if not found

## 📸 Screenshots

### Change Remote
![Change Remote](images/ca8ab92ef51f1c3ae125337b44b4a781.png)

### Manage Files
![Manage Files](images/5ebfafe8ab21d218fa25191409cc688b.png)

## 📥 Install

```bash
git clone https://github.com/ludiwangfpga/save-to-github.git
cd save-to-github
python install.py
```

Done! 🎉 The skill files are copied to `~/.claude/` and work globally across all projects.

## 📋 Requirements

- Python 3.8+
- Git
- Claude Code CLI or Desktop

Optional (auto-installed on first use):
- [GitHub CLI](https://cli.github.com/) — needed only for creating new repos

## 🎮 Usage

In any Claude Code conversation, just type:

```
/save!
```

That's it. Seriously. 😎

### When changes exist

1. Detects new/modified/deleted files
2. For deleted files: asks which to remove from GitHub (remembers choices)
3. Shows **Push** / **Cancel** / **Change remote** selector
4. Commits and pushes 💨

### When nothing to sync

Shows options to:
- **Manage files** — select and remove files from GitHub
- **Change remote** — switch to a different repository
- **Done** — exit

### When not in a git repo

Shows options to:
- **Initialize** — create a new git repo right here
- **Cancel** — abort

## 🗂️ File Structure

```
commands/save!.md    — Claude Code slash command definition
scripts/save.py      — Main Python script (git operations)
scripts/gh_login.bat — GitHub CLI login helper (Windows)
install.py           — Installer
```

## 🗑️ Uninstall

```bash
rm ~/.claude/commands/save!.md
rm ~/.claude/scripts/save.py
rm ~/.claude/scripts/gh_login.bat
```

---

Made with ☕ and Claude Code
