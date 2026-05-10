import json
import subprocess
from pathlib import Path

import pre_commit_checks as checks


def write_package(root: Path, scripts: dict[str, str]) -> None:
    (root / "package.json").write_text(
        json.dumps({"scripts": scripts}),
        encoding="utf-8",
    )


def test_available_scripts_uses_lint_build_test_order(tmp_path):
    write_package(
        tmp_path,
        {
            "test": "vitest",
            "lint": "eslint .",
            "build": "next build",
            "format": "prettier .",
        },
    )

    assert checks.available_scripts(tmp_path) == ["lint", "build", "test"]


def test_run_checks_skips_when_package_json_is_missing(tmp_path):
    calls = []

    def runner(command, cwd):
        calls.append((command, cwd))
        return subprocess.CompletedProcess(command, 0)

    assert checks.run_checks(tmp_path, runner) == 0
    assert calls == []


def test_run_checks_stops_on_first_failure(tmp_path):
    write_package(tmp_path, {"lint": "eslint .", "build": "next build", "test": "vitest"})
    calls = []

    def runner(command, cwd):
        calls.append(command)
        return subprocess.CompletedProcess(command, 1 if command[-1] == "build" else 0)

    assert checks.run_checks(tmp_path, runner) == 1
    assert calls == [["npm", "run", "lint"], ["npm", "run", "build"]]
