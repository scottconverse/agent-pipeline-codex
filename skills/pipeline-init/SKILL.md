---
name: pipeline-init
description: "Initialize a project for Agent Pipeline for Codex from a PRD/spec, existing repo, or project description; scaffold `.pipelines/`, `scripts/policy/`, `.agent-runs/` gitignore support, and a starter `AGENTS.md` when missing."
---

# Pipeline Init

Follow the canonical workflow in `references/pipeline-init.md`, adapted for Codex Desktop App:

- Treat `$ARGUMENTS` as the user's message content or any explicit arguments they provided.
- When the command says `AskUserQuestion`, ask the user directly or use Codex's available structured user-input tool if present.
- When the command says `Read`, use normal file reads.
- When the command says `Bash`, use the shell tool from the current project root.
- Scaffold `AGENTS.md`, not `CLAUDE.md`.

Preserve the command's hard rules:

- Do not skip the orientation summary.
- Do not silently overwrite existing project instructions, `.pipelines/`, or `scripts/policy/`.
- Do not modify files outside the user's project directory and this plugin's read-only templates.
- Do not propose autonomous mode.

Templates and source material are bundled inside this installed skill folder:

- `references/pipeline-payload/pipelines/`
- `references/pipeline-payload/scripts/`
- `references/AGENTS.md`
