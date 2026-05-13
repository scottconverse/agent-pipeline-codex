---
name: audit-init
description: "Scaffold dual-AI audit-handoff infrastructure: out-of-repo audit gate/protocol plus in-repo 5-lens self-audit documentation and optional Codex/other-agent wiring notes."
---

# Audit Init

Follow the canonical workflow in `references/audit-init.md`, adapted for Codex Desktop App:

- Treat Codex as either implementer or auditor depending on the user's role assignment.
- For Codex-side standing instructions, produce `AGENTS.md` or another user-approved Codex project-instructions file rather than Claude memory files.
- When the command says `AskUserQuestion`, ask the user directly or use Codex's available structured user-input tool if present.
- Open a PR for the in-repo `docs/process/5-lens-self-audit.md` only if the user has authorized GitHub publishing for the target project.

Templates live at:

- `references/audit-gate-template.md`
- `references/audit-protocol-template.md`
- `references/5-lens-self-audit-template.md`
