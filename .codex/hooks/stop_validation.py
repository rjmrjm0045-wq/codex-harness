#!/usr/bin/env python3
"""Run npm validation scripts at the end of a Codex turn when available."""

import json
import subprocess
import sys
from pathlib import Path


SCRIPT_ORDER = ("lint", "build", "test")


def continue_ok() -> None:
    print(json.dumps({"continue": True}))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}

    cwd = Path(payload.get("cwd") or ".").resolve()
    if payload.get("stop_hook_active"):
        continue_ok()
        return 0

    package_json = cwd / "package.json"

    if not package_json.exists():
        continue_ok()
        return 0

    try:
        package = json.loads(package_json.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({
            "decision": "block",
            "reason": f"Could not read package.json for validation: {exc}",
        }))
        return 0

    scripts = package.get("scripts") or {}
    commands = [name for name in SCRIPT_ORDER if name in scripts]

    if not commands:
        continue_ok()
        return 0

    for name in commands:
        try:
            result = subprocess.run(
                ["npm", "run", name],
                cwd=str(cwd),
                capture_output=True,
                text=True,
                shell=False,
                timeout=120,
            )
        except FileNotFoundError:
            print(json.dumps({
                "decision": "block",
                "reason": "`npm` was not found. Install Node.js/npm or adjust the Stop hook validation.",
            }))
            return 0
        except subprocess.TimeoutExpired as exc:
            output = "\n".join(part for part in [exc.stdout, exc.stderr] if part).strip()
            if len(output) > 4000:
                output = output[-4000:]
            detail = f"\n\n{output}" if output else ""
            print(json.dumps({
                "decision": "block",
                "reason": f"`npm run {name}` timed out after 120 seconds.{detail}",
            }))
            return 0
        if result.returncode != 0:
            output = "\n".join(part for part in [result.stdout, result.stderr] if part).strip()
            if len(output) > 4000:
                output = output[-4000:]
            print(json.dumps({
                "decision": "block",
                "reason": f"`npm run {name}` failed. Fix it before stopping.\n\n{output}",
            }))
            return 0

    continue_ok()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
