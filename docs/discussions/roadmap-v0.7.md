# Roadmap - v0.7 shipped set and v0.8 carry-forward

This is a living roadmap for the post-hook era. v0.7 shipped optional Codex lifecycle hooks because Codex gained a first-class hook surface that maps directly to the pipeline's existing control-loop and action-safety receipts.

## Shipped in v0.7.0

- Plugin-bundled `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, and `Stop` hooks.
- Active-run context injection on startup/resume.
- Stale standalone skill-name warning.
- Prompt-level gate-bypass blocking during active runs.
- Tool-call warning/denial for concrete unsafe actions.
- Permission-request denial for vague or unsafe approvals.
- Stop-hook continuation through the existing final-response gate.
- Hook audit receipts at `.agent-runs/<run-id>/hook-events.jsonl` when an active run is detectable.

## What's plausible for v0.8

### Candidate 1 - Hook trust and install diagnostics

**Status:** New receipt from v0.7 implementation.

Codex requires plugin hooks to be enabled and trusted before they run. The plugin now documents the config and `/hooks` review step, but operators still need a crisp diagnostic that says "hooks are installed, enabled, trusted, and firing" or names the missing step.

**Sketch:** add a `check_hook_activation.py` verifier that runs direct hook JSON smoke tests, checks installed-cache hook files, checks config, and records whether live Codex hook execution was observed.

### Candidate 2 - Configurable hook strictness

**Status:** Design candidate.

v0.7 defaults to warn/context mode with narrow hard blocks. Some teams may want strict mode for release branches and warn mode for everyday feature branches.

**Sketch:** add `.pipelines/hook-policy.yaml` with `mode: warn|strict`, plus per-pattern overrides. Keep strict mode opt-in and fail closed on malformed policy.

### Candidate 3 - Hook metrics summary

**Status:** Sketch.

`hook-events.jsonl` gives raw receipts. Operators will eventually want grouped counts: how many warnings, denials, stop continuations, and prompt-bypass blocks happened across a run.

**Sketch:** extend `show-run-status` to summarize hook event counts when the file exists, without making hook metrics promotion evidence.

## Still plausible from earlier roadmaps

- Project memory layer.
- Per-stage budgets and timeouts.
- Better PRD-to-manifest auto-fill.
- Cross-run artifact diff.
- Richer run-status views.
- Multi-repo orchestration after enough cross-repo receipts accumulate.

## What's still rejected

- Broad autonomous mode.
- Optional gates.
- Replacing the policy stage with hooks.
- Auto-generating manifests without operator review.

## How this roadmap moves

Receipts move candidates. If v0.7 hooks catch or miss a real action in your project, post the run context, hook event, and the artifact that proves what happened.
