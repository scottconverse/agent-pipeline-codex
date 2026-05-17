# agent-pipeline-codex v0.7.0 - hooked pipeline autonomy

**TL;DR:** v0.7 moves part of the pipeline discipline into Codex lifecycle hooks. The pipeline can now load active run context at session start, warn on stale skill names, preflight risky tool calls, deny unsafe approval requests, add corrective context after failed tools, and continue when an active run is not at a valid stop condition.

## What changed

v0.7 adds an optional plugin-bundled hook bundle:

- `SessionStart` adds the active run id, current stage, next action, directive-bound status, and judge status when Codex starts or resumes.
- `UserPromptSubmit` warns on stale standalone skill names and blocks explicit gate-bypass prompts during active runs.
- `PreToolUse` warns on risky operations and denies concrete unsafe cases such as irreversible commands, forced remote updates, publish/deploy operations, credential exposure, and active-run writes outside manifest `allowed_paths`.
- `PermissionRequest` denies unsafe approval requests instead of training the operator to approve vague prompts.
- `PostToolUse` adds corrective context after actual tool/test failures or changes to pipeline contract artifacts.
- `Stop` reuses the final-response gate so Codex continues when `active-control-state.md` says the run is not allowed to stop.

## How to enable it

Plugin hooks are opt-in in Codex. Add this to your Codex config, restart Codex, then review/trust the hooks through `/hooks` if prompted:

```toml
[features]
plugin_hooks = true
```

Local hook operation works with a normal signed-in Codex session. Codex access tokens are not required for local Max/Pro-style use; OpenAI documents access tokens for ChatGPT Business and Enterprise workspace automation.

## Why this exists

v0.6 made directive-conformant gates auto-fire when the artifacts match a predeclared contract. v0.7 handles a different failure mode: long Codex sessions where the model knows the pipeline rules but the runtime moment has moved on. Hooks put reminders and narrow hard stops at the Codex lifecycle boundary instead of relying only on orchestrator prose.

## Honest limit

Hooks are guardrails, not a sandbox and not a replacement for the judge layer, directive contracts, policy scripts, verifier, critic, drift-detector, or human gates. The promotion evidence still lives in run artifacts. Hooks make the session more self-correcting; they do not create broad autonomous mode.

## Files to read

- `hooks/hooks.json`
- `hooks/hook_runner.py`
- `hooks/hook_utils.py`
- `docs/design/v-next-hooks.md`
- `USER-MANUAL.md` section "Hooked pipeline autonomy (v0.7)"
- `ARCHITECTURE.md` section "Hook data flow (v0.7)"

## Operator note

The repo file is the source of truth. If this announcement is pasted into GitHub Discussions, link back to this file so the discussion copy stays traceable.
