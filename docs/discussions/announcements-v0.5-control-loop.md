# agent-pipeline-codex v0.5 control-loop enforcement

**TL;DR:** the pipeline no longer relies on the agent remembering that "green CI means continue." Stopping, deferring, skipping push, skipping CI, writing a stopping handoff, compacting-and-stopping, and final-answering now go through executable gates.

## What changed

Three scripts make the continuation rule mechanical:

- `final_response_gate.py` discovers active `.agent-runs/*/active-control-state.md` files and blocks a final response when any active run still has `final_response_allowed: false`.
- `agent_decision_gate.py` validates the agent's specific stop/defer/skip/final decision. It rejects unverified blockers, invalid stop reasons, and skipped actions without evidence. With `--write-ledger`, it appends `.agent-runs/<run-id>/decision-ledger.ndjson`.
- `pipeline_continue.py` prints the next required action when stopping is not allowed.

## What is no longer a stop condition

- green CI
- successful push
- draft PR status
- recommended next action
- release or tag after all required gates pass
- open caveats
- unverified blocker or risk

## Why this exists

The failure receipt was blunt: the agent knew the continuation rule, repeated it correctly, and still stopped after a successful subtask. The old hardening existed as instructions plus a validator that only worked when invoked with a known run id. That still left room for chat-logic drift.

The new control plane adds a pre-decision gate and a durable ledger. If the agent claims a blocker, the gate requires evidence. If the blocker is inferred, the gate blocks and `pipeline_continue.py` prints the next required action.

## Files to read

- `docs/process/pipeline-control-loop.md`
- `scripts/final_response_gate.py`
- `scripts/agent_decision_gate.py`
- `scripts/pipeline_continue.py`
- `ARCHITECTURE.md` section 4, "Control-loop state"
- `USER-MANUAL.md` section "Control-loop gate"

## Operator note

The repo file is the source of truth. If this announcement is pasted into GitHub Discussions, link back to this file so the discussion copy stays traceable.
