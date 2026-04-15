#!/usr/bin/env python3
"""
Git save script - auto commit and push to GitHub.
Tracks deleted files and asks user only on first deletion.
Auto-installs gh CLI and opens login popup when needed.

Usage:
  python save.py --batch                 # non-interactive mode for Claude
  python save.py --delete f1 --keep f2   # resolve pending deletions
  python save.py --confirm               # confirm and push after staging
  python save.py --set-remote <url>      # change remote origin URL
  python save.py --manage                # list tracked files
  python save.py --remove f1 f2          # remove files from repo
  python save.py --force-push-new-remote <url>  # push to new repo
"""

import subprocess
import json
import os
import sys
from datetime import datetime
from pathlib import Path

DELETED_RECORD = Path.home() / ".claude" / "save_deleted_record.json"


def find_gh():
    """Find gh CLI executable path."""
    import shutil
    gh = shutil.which("gh")
    if gh:
        return gh
    for p in [
        r"C:\Program Files\GitHub CLI\gh.exe",
        r"C:\Program Files (x86)\GitHub CLI\gh.exe",
        "/usr/bin/gh",
        "/usr/local/bin/gh",
    ]:
        if os.path.isfile(p):
            return p
    return None


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def load_deleted_record():
    if DELETED_RECORD.exists():
        with open(DELETED_RECORD, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_deleted_record(record):
    with open(DELETED_RECORD, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


def parse_args():
    delete_files = []
    keep_files = []
    remove_files = []
    batch = False
    confirm = False
    manage = False
    set_remote = None
    mode = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--delete":
            mode = "delete"
        elif arg == "--keep":
            mode = "keep"
        elif arg == "--remove":
            mode = "remove"
        elif arg == "--batch":
            batch = True
        elif arg == "--confirm":
            confirm = True
        elif arg == "--manage":
            manage = True
        elif arg == "--set-remote" and i + 1 < len(args):
            i += 1
            set_remote = args[i]
        elif mode == "delete":
            delete_files.append(arg)
        elif mode == "keep":
            keep_files.append(arg)
        elif mode == "remove":
            remove_files.append(arg)
        i += 1
    return delete_files, keep_files, remove_files, batch, confirm, manage, set_remote


def get_status():
    out, _, _ = run(["git", "status", "--porcelain"])
    if not out:
        return [], [], []

    added_or_modified = []
    deleted = []
    untracked = []

    for line in out.split("\n"):
        if not line:
            continue
        x, y = line[0], line[1]
        filepath = line[3:]

        if line.startswith("??"):
            untracked.append(filepath)
        elif x == "D" or y == "D":
            deleted.append(filepath)
        else:
            added_or_modified.append(filepath)

    return added_or_modified, deleted, untracked


def handle_deleted_files(deleted, arg_delete, arg_keep):
    record = load_deleted_record()

    for f in arg_delete:
        record[f] = "delete"
    for f in arg_keep:
        record[f] = "keep"
    if arg_delete or arg_keep:
        save_deleted_record(record)

    to_delete = []
    to_skip = []
    pending = []

    for f in deleted:
        if f in record:
            if record[f] == "delete":
                to_delete.append(f)
            else:
                to_skip.append(f)
        else:
            pending.append(f)

    return to_delete, to_skip, pending


def build_commit_message(added_modified, deleted, untracked):
    parts = []
    if untracked:
        parts.append(f"add {len(untracked)} new file(s)")
    if added_modified:
        parts.append(f"update {len(added_modified)} file(s)")
    if deleted:
        parts.append(f"delete {len(deleted)} file(s)")
    summary = ", ".join(parts) if parts else "no changes"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"[{timestamp}] {summary}"


def is_sensitive(filepath):
    name = os.path.basename(filepath).lower()
    sensitive = [".env", "credentials", "secret", ".pem", ".key", "token"]
    return any(s in name for s in sensitive)


def get_remote_url():
    out, _, _ = run(["git", "remote", "get-url", "origin"])
    return out


def ensure_gh_auth():
    """Ensure gh CLI is installed and authenticated. Auto-installs and opens login popup."""
    gh_path = find_gh()

    # Install gh if missing (Windows only)
    if not gh_path:
        print("gh CLI not found. Installing...")
        run(["winget", "install", "--id", "GitHub.cli",
             "--accept-source-agreements", "--accept-package-agreements"])
        gh_path = find_gh()
        if not gh_path:
            print("SETUP_FAILED: Could not install gh CLI.")
            sys.exit(1)
        print("gh CLI installed.")

    # Check auth
    _, _, auth_code = run([gh_path, "auth", "status"])
    if auth_code != 0:
        print("GitHub login required. Opening login window...")
        login_bat = Path(__file__).parent / "gh_login.bat"
        if not login_bat.exists():
            # Create login batch file on the fly
            login_bat.write_text(
                '@echo off\n'
                'chcp 65001 >nul 2>&1\n'
                'echo.\n'
                'echo   ========================================\n'
                'echo    GitHub Login\n'
                'echo   ========================================\n'
                'echo.\n'
                'echo   Press ENTER to open browser for login...\n'
                'echo   After authorizing in browser, return here.\n'
                'echo.\n'
                f'"{gh_path}" auth login -p https -h github.com -w\n'
                'echo.\n'
                f'"{gh_path}" auth status >nul 2>&1\n'
                'if %ERRORLEVEL% EQU 0 (\n'
                '    echo   [OK] Login successful!\n'
                ') else (\n'
                '    echo   [FAIL] Login failed.\n'
                ')\n'
                'echo.\n'
                'echo   This window will close in 3 seconds...\n'
                'timeout /t 3 >nul\n',
                encoding="utf-8"
            )
        subprocess.run(f'start /wait cmd /c "{login_bat}"', shell=True)
        _, _, auth_code2 = run([gh_path, "auth", "status"])
        if auth_code2 != 0:
            print("SETUP_FAILED: GitHub login was not completed.")
            sys.exit(1)
        print("GitHub login successful.")

    return gh_path


def do_push(branch):
    print(f"Pushing to origin/{branch}...")
    _, err, code = run(["git", "push", "origin", branch])
    if code != 0:
        print("Push failed, trying pull --rebase first...")
        _, _, pull_code = run(["git", "pull", "--rebase", "origin", branch])
        if pull_code != 0:
            print("Pull rebase failed. Please resolve conflicts manually.")
            sys.exit(1)
        _, err, code = run(["git", "push", "origin", branch])
        if code != 0:
            print(f"Push failed: {err}")
            sys.exit(1)
    print("Done! Synced to GitHub.")


def main():
    arg_delete, arg_keep, remove_files, batch, confirm, manage, set_remote = parse_args()

    # Handle --manage
    if manage:
        out, _, code = run(["git", "ls-tree", "-r", "HEAD", "--name-only"])
        if code != 0 or not out:
            print("No tracked files found.")
            sys.exit(0)
        files = [f for f in out.split("\n") if f]
        print("TRACKED_FILES:")
        for f in files:
            print(f)
        sys.exit(0)

    # Handle --remove
    if remove_files:
        branch, _, _ = run(["git", "branch", "--show-current"])
        if not branch:
            branch = "main"
        for f in remove_files:
            run(["git", "rm", f])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        msg = f"[{timestamp}] remove {len(remove_files)} file(s) from repo"
        _, err, code = run(["git", "commit", "-m", msg])
        if code != 0:
            print(f"Commit failed: {err}")
            sys.exit(1)
        print(f"Commit: {msg}")
        do_push(branch)
        return

    # Handle --set-remote
    if set_remote:
        old_url = get_remote_url()
        _, _, code = run(["git", "remote", "set-url", "origin", set_remote])
        if code != 0:
            run(["git", "remote", "add", "origin", set_remote])

        _, _, fetch_code = run(["git", "fetch", "origin", "--dry-run"])
        if fetch_code != 0:
            print(f"NEW_REMOTE:")
            print(f"URL: {set_remote}")
            print(f"OLD: {old_url}")
            if old_url:
                run(["git", "remote", "set-url", "origin", old_url])
            sys.exit(0)

        branch, _, _ = run(["git", "branch", "--show-current"])
        if not branch:
            branch = "main"
        _, _, merge_code = run(["git", "merge-base", "HEAD", f"origin/{branch}"])
        if merge_code != 0:
            print(f"NEW_REMOTE:")
            print(f"URL: {set_remote}")
            print(f"OLD: {old_url}")
            if old_url:
                run(["git", "remote", "set-url", "origin", old_url])
            sys.exit(0)

        print(f"Remote updated: {set_remote}")
        return

    # Handle --force-push-new-remote
    if "--force-push-new-remote" in sys.argv:
        idx = sys.argv.index("--force-push-new-remote")
        if idx + 1 < len(sys.argv):
            new_url = sys.argv[idx + 1]
            _, _, code = run(["git", "remote", "set-url", "origin", new_url])
            if code != 0:
                run(["git", "remote", "add", "origin", new_url])
            branch, _, _ = run(["git", "branch", "--show-current"])
            if not branch:
                branch = "main"
            print(f"Force pushing to {new_url}...")
            _, err, code = run(["git", "push", "--force", "origin", branch])
            if code != 0:
                if "not found" in err.lower() or "repository not found" in err.lower():
                    gh_path = ensure_gh_auth()
                    repo_path = new_url.replace("https://github.com/", "").replace(".git", "")
                    print(f"Repo not found. Creating {repo_path}...")
                    _, create_err, create_code = run([gh_path, "repo", "create", repo_path, "--public"])
                    if create_code != 0:
                        print(f"Failed to create repo: {create_err}")
                        sys.exit(1)
                    _, err2, code2 = run(["git", "push", "--force", "origin", branch])
                    if code2 != 0:
                        print(f"Push failed: {err2}")
                        sys.exit(1)
                else:
                    print(f"Push failed: {err}")
                    sys.exit(1)
            print("Done! Pushed to new remote.")
            return

    # Handle --confirm
    if confirm:
        branch, _, _ = run(["git", "branch", "--show-current"])
        if not branch:
            branch = "main"
        out, _, _ = run(["git", "diff", "--cached", "--name-status"])
        added = modified = deleted = 0
        for line in out.split("\n"):
            if not line:
                continue
            if line.startswith("A"):
                added += 1
            elif line.startswith("D"):
                deleted += 1
            else:
                modified += 1
        parts = []
        if added:
            parts.append(f"add {added} new file(s)")
        if modified:
            parts.append(f"update {modified} file(s)")
        if deleted:
            parts.append(f"delete {deleted} file(s)")
        summary = ", ".join(parts) if parts else "update"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        msg = f"[{timestamp}] {summary}"
        _, err, code = run(["git", "commit", "-m", msg])
        if code != 0:
            print(f"Commit failed: {err}")
            sys.exit(1)
        print(f"Commit: {msg}")
        do_push(branch)
        return

    # Main flow
    _, _, code = run(["git", "rev-parse", "--is-inside-work-tree"])
    if code != 0:
        print("NOT_A_GIT_REPO:")
        print(f"DIR: {os.getcwd()}")
        sys.exit(0)

    remote_url = get_remote_url()
    if not remote_url:
        print("NO_REMOTE:")
        sys.exit(0)

    branch, _, _ = run(["git", "branch", "--show-current"])
    if not branch:
        branch = "main"

    print(f"Branch: {branch}")
    print("Checking for changes...")

    added_modified, deleted, untracked = get_status()

    if not added_modified and not deleted and not untracked:
        print("Nothing to sync - working tree is clean.")
        sys.exit(0)

    if untracked:
        print(f"\n  New files ({len(untracked)}):")
        for f in untracked:
            if is_sensitive(f):
                print(f"    [SKIP - sensitive] {f}")
            else:
                print(f"    + {f}")
    if added_modified:
        print(f"\n  Modified files ({len(added_modified)}):")
        for f in added_modified:
            print(f"    ~ {f}")
    if deleted:
        print(f"\n  Deleted files ({len(deleted)}):")
        for f in deleted:
            print(f"    - {f}")

    files_to_delete, files_to_skip, pending = handle_deleted_files(deleted, arg_delete, arg_keep)

    if files_to_skip:
        print(f"  Skipping {len(files_to_skip)} deleted file(s) (kept on GitHub)")

    if pending and batch:
        print(f"\nPENDING_DELETE:")
        for f in pending:
            print(f)
        sys.exit(0)

    # Stage files
    staged_count = 0
    safe_untracked = [f for f in untracked if not is_sensitive(f)]
    files_to_add = added_modified + safe_untracked
    if files_to_add:
        run(["git", "add"] + files_to_add)
        staged_count += len(files_to_add)

    if files_to_delete:
        run(["git", "add"] + files_to_delete)
        staged_count += len(files_to_delete)

    if staged_count == 0:
        print("\nNo files to commit.")
        sys.exit(0)

    if batch:
        msg = build_commit_message(added_modified, files_to_delete, safe_untracked)
        print(f"\nREADY_TO_PUSH:")
        print(f"COMMIT: {msg}")
        print(f"REMOTE: {remote_url}")
        print(f"BRANCH: {branch}")
        print(f"FILES: {staged_count}")
        sys.exit(0)

    msg = build_commit_message(added_modified, files_to_delete, safe_untracked)
    _, err, code = run(["git", "commit", "-m", msg])
    if code != 0:
        print(f"Commit failed: {err}")
        sys.exit(1)
    do_push(branch)


if __name__ == "__main__":
    main()
