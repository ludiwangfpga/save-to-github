#!/usr/bin/env python3
"""
Install save! skill for Claude Code.
Copies command and scripts to ~/.claude/ directory.
"""

import shutil
import os
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
COMMANDS_DIR = CLAUDE_DIR / "commands"
SCRIPTS_DIR = CLAUDE_DIR / "scripts"

SOURCE_DIR = Path(__file__).parent


def main():
    print("Installing save! skill for Claude Code...\n")

    # Create directories
    COMMANDS_DIR.mkdir(parents=True, exist_ok=True)
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    # Copy command file
    src_cmd = SOURCE_DIR / "commands" / "save!.md"
    dst_cmd = COMMANDS_DIR / "save!.md"
    shutil.copy2(src_cmd, dst_cmd)
    print(f"  [OK] {dst_cmd}")

    # Copy scripts
    for name in ["save.py", "gh_login.bat"]:
        src = SOURCE_DIR / "scripts" / name
        dst = SCRIPTS_DIR / name
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  [OK] {dst}")

    print("\nInstallation complete!")
    print("Use /save! in Claude Code to sync your project to GitHub.")
    print("\nFirst-time setup will be handled automatically:")
    print("  - gh CLI will be installed if missing (Windows)")
    print("  - GitHub login popup will open if not authenticated")


if __name__ == "__main__":
    main()
