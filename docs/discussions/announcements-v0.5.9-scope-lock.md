# agent-pipeline-codex v0.5.9 canonical rung lock

**TL;DR:** v0.5.9 adds a mechanical guard that proves the work being started is the work the canonical release plan says is next. If user wording, edited paths, docs, or commit messages point at a future rung, the pipeline stops before edits with `SCOPE_CONFLICT`.

## What changed

- `new-run` now creates both `manifest.yaml` and `scope-lock.yaml`.
- `scope-lock.yaml` binds a run to a canonical release-plan section: rung number, title, proof statement, modules, allowed terms, forbidden future-rung terms, scope bullets, and exit criteria.
- `check_scope_lock.py` fails missing or mismatched locks.
- `check_rung_file_ownership.py` blocks future-rung paths and commit subjects.
- `check_release_docs_consistency.py` blocks README, CHANGELOG, docs index, and other docs that describe the current rung with another rung's terms.
- `agent_decision_gate.py --intent start_rung_work` blocks prompt/plan conflicts before implementation starts.
- `run_all.py` writes `scope-lock-receipt.txt` only after scope lock, path ownership, and docs consistency pass.

## Why this exists

The existing pipeline could prevent early stopping, path drift, weak manifests, and some post-hoc documentation drift. It still did not prove that "v0.6" meant the same thing in the user's prompt, the canonical release plan, implementation paths, release docs, and commit message.

That gap allowed confident work on the wrong rung. v0.5.9 closes that gap by making rung authority explicit and executable.

## Example failure

If `docs/spec/release-plan.md` says:

```text
0.6 - Summary + signed records
0.7 - Publish dashboard
```

Then this prompt is blocked:

```text
Begin v0.6 publish-dashboard work
```

The gate reports:

```text
SCOPE_CONFLICT: release-plan.md says v0.6 is Summary + signed records; publish dashboard belongs to v0.7. Replan or get explicit scope amendment before editing.
```

## Operator note

The repo file is the source of truth. If this announcement is pasted into GitHub Discussions, link back to this file so the discussion copy stays traceable.
