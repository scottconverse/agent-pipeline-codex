---
name: new-run
description: "Create new `.agent-runs/<run-id>/manifest.yaml` and `scope-lock.yaml` skeletons from installed pipeline templates without starting the pipeline."
---

# New Run

Follow the canonical workflow in `references/new-run.md`, adapted for Codex Desktop App:

- Treat `$ARGUMENTS` as the user's message content or explicit arguments.
- Use the shell tool for date and directory operations.
- Use safe file edits for the new manifest and scope-lock only.
- Ask the user directly when the command references `AskUserQuestion`.

Stop after the manifest and scope-lock skeletons are created and shown. Do not start the pipeline, validate semantic manifest or scope-lock content, run policy checks, spawn agents, or modify `.pipelines/manifest-template.yaml` / `.pipelines/scope-lock-template.yaml`.
