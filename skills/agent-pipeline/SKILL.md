---
name: agent-pipeline
description: Use when the user asks to understand, install, initialize, run, or resume the Agent Pipeline for Codex. This is the overview/router skill; for concrete execution prefer the specific pipeline-init, new-run, run-pipeline, or audit-init skill when the user's intent matches one.
---

# Agent Pipeline for Codex

This plugin is the Codex Desktop App variant of `agent-pipeline-claude` v0.5.2. It keeps the same pipeline definitions, policy scripts, role files, run-state convention, landing page structure, and release history, but exposes the workflow through Codex skills instead of Claude Code commands.

Use this skill to orient the user and route to a specific workflow:

- Project onboarding: `skills/pipeline-init/SKILL.md`
- New run scaffolding: `skills/new-run/SKILL.md`
- Run orchestration / resume: `skills/run-pipeline/SKILL.md`
- Dual-AI audit handoff setup: `skills/audit-init/SKILL.md`

Canonical reference files live at repo root:

- `README.md`
- `USER-MANUAL.md`
- `ARCHITECTURE.md`
- `CHANGELOG.md`
- `docs/index.html`

Do not execute a workflow from this overview skill when a more specific skill matches. The overview is for capability discovery, explanation, and routing.
