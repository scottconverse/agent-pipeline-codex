---
name: run-pipeline
description: Orchestrate or resume an Agent Pipeline run from `.agent-runs/<run-id>/`, executing stages in order, stopping at human gates or failures, and using Codex subagents for isolated agent stages.
---

# Run Pipeline

Follow the canonical workflow in `references/run-pipeline.md`, adapted for Codex Desktop App:

- Treat `$ARGUMENTS` as the user's message content or explicit arguments.
- Use Codex `spawn_agent` only when the user has authorized this pipeline run and the stage requires isolated subagent work.
- When the command says `Agent`, use a Codex subagent with the stage role file plus run context.
- When the command says `AskUserQuestion`, ask the user directly or use Codex's available structured user-input tool if present.
- When the command says `Bash`, use the shell tool from the project root.
- Preserve append-only `run.log` behavior.

Hard rules:

- Never silently skip a stage.
- Never advance past a `BLOCKED` or `FAILED` stage.
- Never rewrite `run.log`.
- Never modify the manifest mid-run.
- Never propose autonomous mode; when the user explicitly authorizes autonomous continuation, keep working until a valid stop condition is reached.
- Never end a turn during an authorized pipeline run unless `.agent-runs/<run-id>/active-control-state.md` records a valid stop condition and `scripts/check_pipeline_control_loop.py --run <run-id>` passes.
- Treat unresolved `Open Caveats / Release Risks` items as blocking work. They are not summary notes unless each remaining item starts with `INTENTIONAL DEFERRAL:`.
- Do not treat successful push, green CI, PR draft status, a recommended next action, or release/tag after all gates pass as stop conditions.
- After an authorized push, monitor the pushed PR/branch CI for the head SHA, inspect logs for proof, fix failing checks within scope, commit/push fixes, and repeat until CI is green or a true blocker/human decision is reached.
- At any stop, give the exact resume instruction: run the pipeline again with the same pipeline type and run id.
