# Pipeline Control Loop

The pipeline continuation rule is mechanical.

During an authorized pipeline run, the agent may not send a final response, defer work, skip push, skip CI, write a stopping handoff, compact-and-stop, or pause unless `.agent-runs/<run-id>/active-control-state.md` records a valid stop condition, `scripts/policy/stop_validator.py` can prove that stop condition from current run evidence, `scripts/policy/check_pipeline_control_loop.py --run <run-id>` passes, `scripts/policy/final_response_gate.py --require-active-run` prints `final_response_gate: ALLOW`, and `scripts/policy/agent_decision_gate.py` allows that specific decision.

`stop_validator.py` is the shared truth executable imported by the final, continue, and agent-decision gates. It rejects valid-looking but stale state, including human approval stops outside manifest/plan/manager, human gates that do not match the resume stage derived from `run.log`, stale scope-repair stops after a passing scope-lock receipt, and failed-gate stops without matching failed or blocked run evidence.

`final_response_gate.py` is the pre-final executable. It discovers `.agent-runs/*/active-control-state.md` files and fails closed when any active run records `final_response_allowed: false` or when the shared validator rejects the recorded stop.

`agent_decision_gate.py` is the pre-decision executable. It rejects unverified blocker claims, invalid stop reasons, skipped actions without evidence, and any decision that conflicts with the active control state. If a claimed blocker does not match active control state, the claim must cite an existing evidence file; plain text evidence alone is not enough. With `--write-ledger`, it appends the decision to `.agent-runs/<run-id>/decision-ledger.ndjson`.

`pipeline_continue.py` is the navigator executable. It prints the active run's required continuation action when stopping is not allowed.

## Required Control State

Every active run records:

```yaml
active_run: true
current_stage: <stage-id>
last_completed_gate: <gate-or-none>
next_required_action: <concrete-action>
stop_condition: none | human_approval_gate | failed_gate_needs_user_direction | destructive_action | credential_or_secret_required | scope_conflict | external_system_unavailable_after_retry | user_explicitly_paused_or_stopped
final_response_allowed: true | false
continuing_to: <concrete-action>
```

## Valid Stop Conditions

- `human_approval_gate`
- `failed_gate_needs_user_direction`
- `destructive_action`
- `credential_or_secret_required`
- `scope_conflict`
- `external_system_unavailable_after_retry`
- `user_explicitly_paused_or_stopped`

## Invalid Stop Conditions

- `successful_push`
- `green_ci`
- `recommended_next_action`
- `open_caveats`
- `release_or_tag_after_gates_pass`
- `pr_draft_status`
- `unverified_blocker_or_risk`

## Caveat Rule

`Open Caveats / Release Risks` is a blocking section. Each bullet must be fixed before the slice completes.

The only permitted unfixed bullet starts with `INTENTIONAL DEFERRAL:` and cites the manifest or director decision that authorizes the deferral.

## Post-Push Rule

After every authorized push, the runner monitors CI for the exact pushed SHA. If checks fail, the runner inspects logs, fixes failures inside scope, verifies locally, commits, pushes, and repeats.

Green CI is evidence. It is not a stop condition.

## Rung / Scope Authority Rule

Before product work starts, `.agent-runs/<run-id>/scope-lock.yaml` must exist and pass `python scripts/policy/check_scope_lock.py --run <run-id>`.

The scope lock names the canonical release-plan source, current rung, rung title, proof statement, required modules, allowed feature terms, forbidden future-rung terms, and replan triggers. The policy stage also runs:

- `check_rung_file_ownership.py --run <run-id>` to block edited paths or commit messages that belong to another rung.
- `check_release_docs_consistency.py --run <run-id>` to block README, CHANGELOG, docs index, or other docs that name the current rung with future-rung work.

If user wording conflicts with the canonical release plan, the pipeline must stop before edits with `scope_conflict` and require an explicit scope amendment. The agent may not infer that the release ladder changed.

Before starting rung work from a user prompt, run:

```bash
python scripts/policy/agent_decision_gate.py --run <run-id> --intent start_rung_work --claimed-rung <current-rung> --prompt-text "<user wording>"
```

No product commit is valid without a durable `.agent-runs/<run-id>/scope-lock-receipt.txt` containing:

```text
scope_lock: PASS
canonical_rung: <rung> <title>
edited_paths_match_rung: PASS
docs_consistency: PASS
```

No push is valid if the commit message or docs contradict the locked rung.

## Pre-Final Gate

Before every final response in an authorized pipeline run, run:

```bash
python scripts/policy/final_response_gate.py --require-active-run
```

If the command prints `final_response_gate: BLOCK`, do not send a final response. Continue to the printed `continuing_to` action.

Before every stop, defer, skipped push, skipped CI, handoff-and-stop, compact-and-stop, or user question during an authorized run, run:

```bash
python scripts/policy/agent_decision_gate.py --intent <intent> --claimed-stop-condition <condition> --write-ledger
```

If the command prints `agent_decision_gate: BLOCK`, do not stop. Continue to the printed continuation action or verify the claimed blocker with evidence and run the gate again.

When uncertain what to do next, run:

```bash
python scripts/policy/pipeline_continue.py
```

## Workflow-Cost Rule

GitHub Actions cost discipline is part of slice completeness. If a slice adds or modifies `.github/workflows/*.yml` or `.github/workflows/*.yaml`, the plan names those workflow files before editing, the executor applies the 10 directives below, the policy stage runs `check_actions_budget`, and implementation/verifier artifacts record workflow-cost evidence. Unresolved workflow-cost violations are release risks and block completion.

1. Never add a daily cron without explicit Scott approval. Weekly is the maximum default schedule. Daily is allowed only for a specific justified need, such as security scanning or dependency drift, and the run record must prove weekly is insufficient before daily is used.
2. Every new GitHub Actions workflow must include the required concurrency block with `group: ${{ github.workflow }}-${{ github.ref }}` and `cancel-in-progress: true`, except release or tag workflows where cancellation would corrupt the release.
3. Do not duplicate `push: branches: [main]` and `pull_request: branches: [main]` for the same validation workflow.
4. Batch work-in-progress commits before pushing; squash local work-in-progress commits when doing so preserves useful history.
5. Add `paths:` filters when adding heavy workflows, including TeX, Docker, Playwright, browser installs, large language models, cleanroom, or e2e validation.
6. macOS jobs are allowed on release tags only unless Scott explicitly approves a PR-fired exception.
7. Windows jobs are allowed on PR only when truly necessary, and the run record or policy evidence must justify the cost.
8. Python version matrices are allowed on tags or weekly cron. PR CI tests one production Python version by default, currently Python 3.12.
9. Cache anything that takes more than 30 seconds to install or download.
10. Every `upload-artifact` step must set `retention-days: 7` unless the artifact is a release artifact or Scott explicitly approves longer retention.

## Merge, Release, And Tag Rule

Merge, release, and tag are not stop conditions when the action is inside the authorized slice and all required review, test, judge, CI, and release gates have passed. The runner executes the action and continues to the next authorized control-loop step.
