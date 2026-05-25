# agent-pipeline-codex v0.9.1 - baseline isolation for release rehearsal

**TL;DR:** v0.9.1 teaches the release-rehearsal and verifier roles to check
whether a failure or hang already reproduces on the merge-base before deep
debugging the branch.

## What changed

v0.9.1 adds durable role text in two places:

- `local-rehearsal.md` now has Step 2.5, a mandatory
  regression-vs-baseline isolation move after any `verify-release.sh` failure
  or hang.
- `verifier.md` now points to the same Step 2.5 when a verifier test run fails
  or hangs in a way `implementation-report.md` did not show.

The step is deliberately small: note the failure signature, stash branch
changes, check out the merge-base, rerun the same command in the same
environment, then restore the branch.

## Why this exists

A real CivicSuite run lost time because an implementing agent jumped straight
to verbose test debugging after `verify-release.sh` hung. The hang was not a
branch regression. It reproduced from baseline and came from accumulated host
state.

The missing question was: "does this happen on main too?"

v0.9.1 writes that question into the role contract so it survives fresh
sessions, compaction, and agent handoff. It is not a chat-side reminder.

## Outcome rule

- Baseline passes: debug the branch diff.
- Baseline fails the same way: document the baseline SHA and surface the
  pre-existing failure separately.
- Baseline fails differently: both are real; debug the worse one first.

## Files to read

- `skills/pipeline-init/references/pipeline-payload/pipelines/roles/local-rehearsal.md`
- `skills/pipeline-init/references/pipeline-payload/pipelines/roles/verifier.md`
- `CHANGELOG.md`

## Operator note

The repo file is the source of truth. If this announcement is pasted into
GitHub Discussions, link back to this file so the discussion copy stays
traceable.
