# agent-pipeline-codex v0.8.0 - intake drafting

**TL;DR:** v0.8 adds a separate `agent-pipeline-codex:intake` skill for the moment before a run has a manifest. Give it a plain-English product, repo, design, task, bug, or feature description and it drafts the starting run artifacts without starting the pipeline.

## What changed

v0.8 adds one new namespaced plugin skill:

- `agent-pipeline-codex:intake`

The skill writes draft artifacts under `.agent-runs/<run-id>/`:

- `intake.md` with the source description and conservative interpretation.
- `manifest.yaml` as a starter manifest draft.
- `scope-lock.yaml` as a starter scope draft.
- `intake-questions.md` when required facts are missing.

## Why this exists

Before v0.8, a project with no `manifest.yaml` had a sharp first step: the operator had to already know how to translate a task into pipeline-shaped artifacts. That was safe, but not friendly.

`intake` creates a softer on-ramp. It turns "describe what you're working on" into reviewable draft artifacts, then stops before validation or agent work. The operator still has to inspect, edit, and validate the manifest before `run-pipeline` can execute.

## Safety boundary

Draft intake is not approval. The new skill does not:

- start or resume `run-pipeline`;
- validate a manifest;
- create a directive contract;
- spawn subagents;
- run tests or policy scripts;
- write outside `.agent-runs/<run-id>/`.

When the request is underspecified, it writes TODOs or `intake-questions.md` instead of inventing scope, allowed paths, release-plan facts, or completion criteria.

## How to use it

In a project initialized with `agent-pipeline-codex:pipeline-init`, start with:

```text
Use agent-pipeline-codex:intake for Add account deletion to settings. Include tests, docs, and a clear rollback path.
```

Then review the generated artifacts, fill missing answers, run `agent-pipeline-codex:validate-manifest`, and only then run `agent-pipeline-codex:run-pipeline`.

## Files to read

- `commands/intake.md`
- `skills/intake/SKILL.md`
- `skills/intake/references/intake.md`
- `USER-MANUAL.md` section "Intake drafting"
- `ARCHITECTURE.md` intake data-flow notes

## Operator note

The repo file is the source of truth. If this announcement is pasted into GitHub Discussions, link back to this file so the discussion copy stays traceable.
