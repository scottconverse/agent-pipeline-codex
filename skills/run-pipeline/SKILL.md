---
name: run-pipeline
description: Orchestrate or resume an Agent Pipeline run from `.agent-runs/<run-id>/`, executing stages in order, stopping at human gates or failures, and using Codex subagents for isolated agent stages.
---

# Run Pipeline

Follow the canonical workflow in `../../commands/run-pipeline.md`, adapted for Codex Desktop App:

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
- Never propose autonomous mode.
- At any stop, give the exact resume instruction: run the pipeline again with the same pipeline type and run id.
