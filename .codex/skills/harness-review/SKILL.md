---
name: harness-review
description: Review repository changes in a Harness framework project against `AGENTS.md`, architecture docs, ADR decisions, tests, and build readiness. Use when the user asks to review current changes, validate a Harness step output, check guardrail compliance, or produce a structured implementation review.
---

# Harness Review

## Overview

Use this skill to review changes in a Harness-managed project. Focus on concrete risks, rule violations, missing tests, and whether the project remains buildable.

## Inputs

Before reviewing, read these files when they exist:

- `/AGENTS.md`
- `/docs/ARCHITECTURE.md`
- `/docs/ADR.md`
- changed files from `git diff` and `git status`

If the review is for a specific Harness phase or step, also read:

- `phases/{task-name}/index.json`
- `phases/{task-name}/step{N}.md`
- `phases/{task-name}/step{N}-output.json` if relevant

## Checklist

Check:

1. **Architecture compliance**: Does the change follow the structure and boundaries in `ARCHITECTURE.md`?
2. **Technical decision compliance**: Does it stay within ADR choices?
3. **Test coverage**: Are new or changed behaviors covered by appropriate tests?
4. **CRITICAL rules**: Does it violate any CRITICAL rule in `AGENTS.md`?
5. **Buildability**: Do relevant build, lint, typecheck, or test commands pass or have a clear reason they were not run?

## Output

Lead with findings. Prefer file and line references for every issue.

Use this table when the user asks for the Harness checklist format:

| Item | Result | Notes |
|------|--------|-------|
| Architecture compliance | PASS/FAIL | {details} |
| Technical stack compliance | PASS/FAIL | {details} |
| Test coverage | PASS/FAIL | {details} |
| CRITICAL rules | PASS/FAIL | {details} |
| Buildability | PASS/FAIL | {details} |

If there are violations, give specific fixes. If no issues are found, say so clearly and mention any tests or commands that were not run.

When doing a code review, keep the review stance: bugs, regressions, and missing tests first; summary second.
