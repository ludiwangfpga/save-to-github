Run this command:

```
python ~/.claude/scripts/save.py --batch 2>/dev/null
```

Handle the output based on these markers:

## NOT_A_GIT_REPO
Current directory is not a git repo. Use `AskUserQuestion` (single select):
1. label: **Initialize** — description: "Create a new git repo here". If selected: run `git init 2>/dev/null`, then re-run `python ~/.claude/scripts/save.py --batch 2>/dev/null` and continue handling.
2. label: **Cancel** — description: "Abort". If selected: output "Cancelled." and STOP.

## NO_REMOTE
Git repo exists but no remote configured. Use `AskUserQuestion` to ask for a GitHub URL (provide "Cancel" as an option, user types URL via Other). If user provides a URL, run `git remote add origin <url> 2>/dev/null`, then re-run `python ~/.claude/scripts/save.py --batch 2>/dev/null` and continue handling. If Cancel: output "Cancelled." and STOP.

## PENDING_DELETE
Lines after `PENDING_DELETE:` are filenames. Use `AskUserQuestion` with `multiSelect: true` to ask which files to delete from GitHub. Include a "Keep all" option. After selection, map chosen files to `--delete` and the rest to `--keep`, then re-run:
```
python ~/.claude/scripts/save.py --batch --delete file1 --keep file2 2>/dev/null
```

## READY_TO_PUSH
Files are staged (not yet committed). Parse the COMMIT, REMOTE, BRANCH, FILES info. Use `AskUserQuestion` (single select) with these exact option labels in this exact order:
1. label: **Push** — description: "Commit and push to GitHub"
2. label: **Cancel** — description: "Unstage and abort". If selected: run `git reset 2>/dev/null` to unstage, output "Cancelled." and STOP. No more tools, no more text.
3. label: **Change remote** — description: "Change repository URL before pushing". If selected: use `AskUserQuestion` to ask for new URL, then run `python ~/.claude/scripts/save.py --set-remote <url> 2>/dev/null`. Check the output — if it contains `NEW_REMOTE:`, handle it as described below. Otherwise run `python ~/.claude/scripts/save.py --confirm 2>/dev/null`.

If user picks Push:
```
python ~/.claude/scripts/save.py --confirm 2>/dev/null
```

## NEW_REMOTE
The new URL is a different or empty repo with no common history. Use `AskUserQuestion` (single select):
1. label: **Create** — description: "Force push all local code to this new repo"
2. label: **Cancel** — description: "Keep current remote and abort". If selected: output "Cancelled." and STOP.

If user picks Create, run:
```
python ~/.claude/scripts/save.py --force-push-new-remote <url> 2>/dev/null
```
The script auto-handles dependencies: installs gh CLI if missing, opens login popup if not authenticated, creates the repo, and pushes. If output contains `SETUP_FAILED:`, show the error and STOP. If successful, also run `python ~/.claude/scripts/save.py --confirm 2>/dev/null` to push any staged changes.

## No markers (nothing to sync)
Use `AskUserQuestion` (single select):
1. label: **Manage files** — description: "View and delete files on GitHub"
2. label: **Change remote** — description: "Change repository URL". If selected: use `AskUserQuestion` to ask for new URL (provide "Keep current" and "Cancel" as options, user types URL via Other). Then run `python ~/.claude/scripts/save.py --set-remote <url> 2>/dev/null`. If output contains `NEW_REMOTE:`, handle via the NEW_REMOTE section above. Otherwise show "Remote updated." and STOP.
3. label: **Done** — description: "Nothing to do". If selected: output "Nothing to sync." and STOP.

If user picks **Manage files**, run:
```
python ~/.claude/scripts/save.py --manage 2>/dev/null
```
The output contains `TRACKED_FILES:` followed by filenames. Use `AskUserQuestion` with `multiSelect: true` to let the user select files to remove from GitHub. Include a "Cancel" option.

If user selects files (not Cancel), run:
```
python ~/.claude/scripts/save.py --remove file1 file2 2>/dev/null
```
Show the result. If user picks Cancel: output "Cancelled." and STOP.

Keep responses short throughout.
