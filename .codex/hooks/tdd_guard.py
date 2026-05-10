#!/usr/bin/env python3
"""Require test changes before production-code edits."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


TEST_FILE_RE = re.compile(
    r"(^|/)(tests?|__tests__)/|"
    r"(^|/)[^/]+(_test|\.test|\.spec)\.[^/]+$|"
    r"(^|/)test_[^/]+\.py$",
    re.IGNORECASE,
)
SOURCE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".swift",
    ".ts",
    ".tsx",
}
EXEMPT_PREFIXES = (
    ".codex/",
    ".github/",
    "docs/",
    "phases/",
)
EXEMPT_FILENAMES = {
    ".gitignore",
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
}
def repo_root(cwd: str | None) -> Path:
    start = cwd or os.getcwd()
    if not Path(start).is_dir():
        start = os.getcwd()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    if result.returncode == 0 and result.stdout and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return Path(start).resolve()


def normalize_path(path: str) -> str:
    return path.strip().strip('"').replace("\\", "/")


def changed_files_from_patch(command: str) -> list[str]:
    files: list[str] = []
    markers = (
        "*** Add File: ",
        "*** Update File: ",
        "*** Delete File: ",
    )
    for line in command.splitlines():
        for marker in markers:
            if line.startswith(marker):
                files.append(normalize_path(line[len(marker) :]))
    return files


def is_test_file(path: str) -> bool:
    normalized = normalize_path(path)
    return bool(TEST_FILE_RE.search(normalized))


def is_exempt(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized in EXEMPT_FILENAMES:
        return True
    return normalized.startswith(EXEMPT_PREFIXES)


def is_source_file(path: str) -> bool:
    normalized = normalize_path(path)
    if is_exempt(normalized) or is_test_file(normalized):
        return False
    return Path(normalized).suffix.lower() in SOURCE_EXTENSIONS


def git_changed_test_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    if result.returncode != 0:
        return []

    files: list[str] = []
    for line in result.stdout.splitlines():
        candidate = line[3:].strip()
        if " -> " in candidate:
            candidate = candidate.split(" -> ", 1)[1].strip()
        candidate = normalize_path(candidate)
        if is_test_file(candidate):
            files.append(candidate)
    return files


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def handle_pre_tool_use(payload: dict[str, Any], root: Path) -> int:
    if payload.get("tool_name") != "apply_patch":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    files = changed_files_from_patch(command)
    if not files:
        return 0

    test_files = [path for path in files if is_test_file(path)]
    source_files = [path for path in files if is_source_file(path)]

    if test_files and not source_files:
        return 0

    if not source_files:
        return 0

    changed_tests = git_changed_test_files(root)

    if not changed_tests:
        sample = ", ".join(source_files[:3])
        deny(
            "TDD guard blocked production-code edits before tests. "
            f"Add or update a test first, then retry. Source files: {sample}"
        )
        return 0

    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    root = repo_root(payload.get("cwd"))
    event_name = payload.get("hook_event_name")

    if event_name == "PreToolUse":
        return handle_pre_tool_use(payload, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
