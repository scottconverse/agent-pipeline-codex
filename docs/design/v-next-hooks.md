# vNext Design: Codex Lifecycle Hooks

## Summary

v0.7 adds optional plugin-bundled Codex lifecycle hooks to make Agent Pipeline
discipline active at Codex runtime boundaries. The hooks load active run
context, warn on stale or bypassing prompts, preflight risky tool calls, deny
clearly unsafe permission requests, add corrective context after failed tools,
and prevent final responses when the run is not at a valid stop condition.

The hooks are opt-in because OpenAI's plugin documentation requires
`[features].plugin_hooks = true` before plugin-bundled hooks run:
<https://developers.openai.com/codex/plugins/build>. The hook event model is
the Codex lifecycle described in the official hooks documentation:
<https://developers.openai.com/codex/hooks>.
OpenAI's hook documentation also notes that non-managed hooks require trust
review before they run.

## Platform limits

Codex hooks are guardrails, not a cryptographic or sandbox boundary. The
`PreToolUse` hook is used for supported tool-call preflight, but the existing
judge layer, manifest/scope checks, directive gates, and human fallback gates
remain authoritative. Hooks do not bypass Codex platform approvals.

Codex access tokens are not required for local hook operation. OpenAI documents
Codex access tokens for ChatGPT Business and Enterprise workspaces:
<https://developers.openai.com/codex/enterprise/access-tokens>. v0.7 therefore
documents tokens as optional CI plumbing for those workspaces, not as a
requirement for local Max/Pro-style use.

## Design

The plugin declares `hooks/hooks.json` from `.codex-plugin/plugin.json`. Each
hook calls `hooks/hook_runner.py`, which reads Codex's hook JSON from stdin,
uses `hooks/hook_utils.py` to inspect on-disk Agent Pipeline artifacts, and
prints Codex hook JSON only when it has context, denial, or continuation
instructions to provide.

The default behavior is warn/context mode. Hard blocking is limited to concrete
safety violations already recognized by the pipeline discipline: destructive
commands, force pushes, publish/deploy operations, credential exposure,
active-run writes outside manifest `allowed_paths`, explicit gate bypass
prompts, and invalid stop conditions.

When an active run is detectable, hooks append concise JSONL receipts to
`.agent-runs/<run-id>/hook-events.jsonl`. This file supports auditability but
does not replace promotion evidence.

## Preserved protections

- Directive contracts still bind exact manifest/scope/plan/manager criteria.
- The v0.4 judge layer still owns context-isolated high-risk action review.
- Human gates still fire when artifacts are absent, malformed, divergent, or
  judgment-required.
- `final_response_gate.py` and `stop_validator.py` remain the single source of
  truth for valid stop conditions.
- Pipeline promotion still requires policy, verifier, drift, critic, judge,
  tests, and directive-manager evidence.
