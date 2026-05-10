#!/usr/bin/env python3
"""Block high-risk shell commands before Codex runs them."""

import json
import re
import sys


DENY_PATTERNS = [
    (re.compile(r"\brm\s+-rf\b", re.IGNORECASE), "Recursive force delete is blocked."),
    (re.compile(r"\bRemove-Item\b.*\b-Recurse\b.*\b-Force\b", re.IGNORECASE), "Recursive force delete is blocked."),
    (re.compile(r"\bgit\s+push\b.*\s--force(?:-with-lease)?\b", re.IGNORECASE), "Force push is blocked."),
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE), "Hard reset is blocked."),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE is blocked."),
]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")

    for pattern, reason in DENY_PATTERNS:
        if pattern.search(command):
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }))
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
