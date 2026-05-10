---
name: harness
description: Plan, create, and run Harness framework phased implementation workflows. Use when the user asks to plan work as phases or steps, create `phases/` task files, prepare step-by-step implementation instructions, run `scripts/execute.py`, recover blocked/error steps, or manage Harness task status.
---

# Harness

## Overview

Use this skill to operate projects that use the Harness framework. The framework turns a larger implementation request into self-contained step files under `phases/`, then runs them sequentially with `scripts/execute.py`.

## Workflow

### Explore

Read `/docs/` documents such as `PRD.md`, `ARCHITECTURE.md`, `ADR.md`, and `UI_GUIDE.md` before planning or implementing. Read `AGENTS.md` for project rules and CRITICAL constraints.

### Discuss

If implementation needs product, architecture, API, authentication, environment, or deployment decisions that cannot be inferred safely, present the concrete decision points to the user before creating steps.

### Design Steps

When the user asks for an implementation plan, draft small sequential steps and ask for feedback before writing phase files unless they explicitly asked to create files immediately.

Use these design rules:

- Keep scope small: one layer or module per step. Split steps if several modules must change together.
- Make each step self-contained. Do not rely on prior chat context; put required paths and facts in the step file.
- Force context gathering by listing files the agent must read before editing.
- Give interface-level guidance where possible, but state hard constraints explicitly.
- Use executable acceptance criteria such as `npm run build` and `npm test`.
- Write specific warnings as "Do not do X. Reason: Y."
- Use kebab-case step names such as `project-setup`, `api-layer`, or `auth-flow`.

## File Layout

Create or update `phases/index.json`:

```json
{
  "phases": [
    {
      "dir": "0-mvp",
      "status": "pending"
    }
  ]
}
```

Create `phases/{task-name}/index.json`:

```json
{
  "project": "<project-name>",
  "phase": "<task-name>",
  "steps": [
    { "step": 0, "name": "project-setup", "status": "pending" },
    { "step": 1, "name": "core-types", "status": "pending" }
  ]
}
```

Field rules:

- `project`: project name from `AGENTS.md` or the user's request.
- `phase`: task name matching the directory name.
- `steps[].step`: zero-based integer sequence.
- `steps[].name`: kebab-case slug.
- `steps[].status`: start as `"pending"`.
- Do not set timestamps at creation time. `execute.py` manages `created_at`, `started_at`, `completed_at`, `failed_at`, and `blocked_at`.

Create one `phases/{task-name}/step{N}.md` per step:

````markdown
# Step {N}: {name}

## Files To Read

- `/docs/ARCHITECTURE.md`
- `/docs/ADR.md`
- {previous step output or modified file paths}

## Task

{Concrete implementation instructions, file paths, signatures, and constraints.}

## Acceptance Criteria

```bash
npm run build
npm test
```

## Verification

1. Run the acceptance criteria.
2. Check architecture and ADR compliance.
3. Update `phases/{task-name}/index.json`:
   - success: `"status": "completed"`, `"summary": "<one-line useful summary>"`
   - repeated failure: `"status": "error"`, `"error_message": "<specific error>"`
   - user action needed: `"status": "blocked"`, `"blocked_reason": "<specific reason>"`

## Prohibited

- Do not break existing tests.
- {Step-specific "do not do X; reason: Y" rules.}
````

## Execution

Run the phase sequentially:

```bash
python scripts/execute.py {task-name}
python scripts/execute.py {task-name} --push
```

`execute.py` creates or checks out `feat-{task-name}`, injects `AGENTS.md` and `docs/*.md` into every step prompt, passes completed step summaries forward, retries failed steps up to three times, records timestamps, and separates code commits from phase metadata commits.

## Recovery

For an `error` step, change that step's `status` back to `"pending"`, remove `error_message`, and rerun `scripts/execute.py`.

For a `blocked` step, resolve the `blocked_reason`, change `status` back to `"pending"`, remove `blocked_reason`, and rerun `scripts/execute.py`.
