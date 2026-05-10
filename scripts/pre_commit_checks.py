#!/usr/bin/env python3
"""Run project validation commands for the Git pre-commit hook."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence


SCRIPT_ORDER = ("lint", "build", "test")
Runner = Callable[[Sequence[str], Path], subprocess.CompletedProcess]


def _default_runner(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=str(cwd), shell=False)


def _load_package(root: Path) -> dict | None:
    package_json = root / "package.json"
    if not package_json.exists():
        print("pre-commit: package.json not found; skipping npm lint/build/test checks.")
        return None

    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"pre-commit: failed to read package.json: {exc}", file=sys.stderr)
        raise

    if not isinstance(data, dict):
        raise ValueError("package.json must contain a JSON object")
    return data


def available_scripts(root: Path) -> list[str]:
    package = _load_package(root)
    if package is None:
        return []

    scripts = package.get("scripts") or {}
    if not isinstance(scripts, dict):
        raise ValueError("package.json scripts must be a JSON object")

    return [name for name in SCRIPT_ORDER if name in scripts]


def run_checks(root: Path, runner: Runner = _default_runner) -> int:
    try:
        commands = available_scripts(root)
    except Exception:
        return 1

    if not commands:
        print("pre-commit: no lint/build/test npm scripts found; skipping.")
        return 0

    for name in commands:
        print(f"pre-commit: running npm run {name}")
        try:
            result = runner(["npm", "run", name], root)
        except FileNotFoundError:
            print("pre-commit: npm was not found. Install Node.js/npm to commit.", file=sys.stderr)
            return 1

        if result.returncode != 0:
            print(f"pre-commit: npm run {name} failed; commit aborted.", file=sys.stderr)
            return result.returncode

    print("pre-commit: lint/build/test checks passed.")
    return 0


def main() -> int:
    return run_checks(Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
