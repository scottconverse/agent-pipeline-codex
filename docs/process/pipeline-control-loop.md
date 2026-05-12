# Pipeline Control Loop

The pipeline continuation rule is mechanical.

During an authorized pipeline run, the agent may not send a final response unless `.agent-runs/<run-id>/active-control-state.md` records a valid stop condition and `scripts/check_pipeline_control_loop.py --run <run-id>` passes.

## Required Control State

Every active run records:

```yaml
active_run: true
current_stage: <stage-id-or-post-push-ci>
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

## Caveat Rule

`Open Caveats / Release Risks` is a blocking section. Each bullet must be fixed before the slice completes.

The only permitted unfixed bullet starts with `INTENTIONAL DEFERRAL:` and cites the manifest or director decision that authorizes the deferral.

## Post-Push Rule

After every authorized push, the runner monitors CI for the exact pushed SHA. If checks fail, the runner inspects logs, fixes failures inside scope, verifies locally, commits, pushes, and repeats.

Green CI is evidence. It is not a stop condition.

## Merge, Release, And Tag Rule

Merge, release, and tag are not stop conditions when the action is inside the authorized slice and all required review, test, judge, CI, and release gates have passed. The runner executes the action and continues to the next authorized control-loop step.
