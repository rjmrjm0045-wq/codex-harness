#!/usr/bin/env sh
set -eu

ROOT="$(git rev-parse --show-toplevel)"
python "$ROOT/.codex/hooks/tdd_guard.py"
