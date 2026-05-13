---
name: new-run
description: "Create a new `.agent-runs/<run-id>/manifest.yaml` from the installed pipeline manifest template without starting the pipeline."
---

# New Run

Follow the canonical workflow in `references/new-run.md`, adapted for Codex Desktop App:

- Treat `$ARGUMENTS` as the user's message content or explicit arguments.
- Use the shell tool for date and directory operations.
- Use safe file edits for the new manifest only.
- Ask the user directly when the command references `AskUserQuestion`.

Stop after the manifest skeleton is created and shown. Do not start the pipeline, validate semantic manifest content, run policy checks, spawn agents, or modify `.pipelines/manifest-template.yaml`.
