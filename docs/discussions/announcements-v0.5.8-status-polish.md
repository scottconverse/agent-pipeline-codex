# agent-pipeline-codex v0.5.8 status polish

**TL;DR:** v0.5.8 is the promotion-polish release. It does not add a new pipeline layer; it makes the current v0.5 stack easier to trust, easier to inspect, and easier to present publicly.

## What changed

- `show-run-status` now reports when malformed `run.log` lines were skipped, so crash-recovery status checks do not silently hide corrupted lines.
- The decision ledger now has a production writer-to-validator regression test.
- Git action classification has focused negative tests for read-only commands and force-push variants.
- README and CONTRIBUTING expose the source-only CI badge.
- The landing page, user manual, changelog, plugin metadata, installed cache, and standalone compatibility skills are synchronized at `0.5.8`.

## Why this exists

The v0.5.7 audit pass found the core correctness blockers fixed, then called out the last trust-polish gaps: transparent status reporting, ledger proof through the real writer, tighter classification regression coverage, and public CI visibility.

This release closes those gaps. The result is not a larger pipeline; it is a cleaner one. Operators can inspect a run without mutating it, see when the log had malformed lines, and trust that the safety regexes have targeted regression coverage.

## What to try first

After starting or resuming a run, use:

```text
show-run-status <run-id>
```

It prints the completed stage count, latest non-complete event, active control state, and artifact inventory without advancing the pipeline.

## Files to read

- `CHANGELOG.md` section `0.5.8`
- `USER-MANUAL.md` command reference for `show-run-status`
- `docs/index.html` landing page timeline
- `tests/test_show_run_status.py`
- `tests/test_decision_ledger.py`
- `tests/test_action_classification.py`

## Operator note

The repo file is the source of truth. If this announcement is pasted into GitHub Discussions, link back to this file so the discussion copy stays traceable.
