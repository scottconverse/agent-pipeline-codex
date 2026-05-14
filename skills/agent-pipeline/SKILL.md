---
name: agent-pipeline
description: "Use when the user asks to understand, install, initialize, run, or resume the Agent Pipeline for Codex. This is the overview/router skill; for concrete execution prefer the specific pipeline-init, new-run, run-pipeline, or audit-init skill when the user's intent matches one."
---

# Agent Pipeline for Codex

This plugin is the Codex Desktop App variant of `agent-pipeline-claude` v0.5.2 with v0.5.7 audit-punch-list hardening, run-status tooling, and namespaced plugin install proof. It keeps the same pipeline definitions, policy scripts, role files, run-state convention, landing page structure, and release history, but exposes the workflow through Codex skills instead of Claude Code commands.

When proving the plugin is active in a fresh Codex session, verify the namespaced plugin skills (`agent-pipeline-codex:agent-pipeline`, `agent-pipeline-codex:pipeline-init`, `agent-pipeline-codex:new-run`, `agent-pipeline-codex:run-pipeline`, `agent-pipeline-codex:audit-init`, `agent-pipeline-codex:show-run-status`, `agent-pipeline-codex:validate-manifest`). Standalone skills under `$CODEX_HOME/skills` are compatibility copies and are not proof that the current plugin cache loaded.

Use this skill to orient the user and route to a specific workflow:

- Project onboarding: invoke the `pipeline-init` skill
- New run scaffolding: invoke the `new-run` skill
- Run orchestration / resume: invoke the `run-pipeline` skill
- Dual-AI audit handoff setup: invoke the `audit-init` skill

Canonical reference files are bundled inside this installed overview skill:

- `references/README.md`
- `references/USER-MANUAL.md`
- `references/ARCHITECTURE.md`
- `references/CHANGELOG.md`

Do not execute a workflow from this overview skill when a more specific skill matches. The overview is for capability discovery, explanation, and routing.
