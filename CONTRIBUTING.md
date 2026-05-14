# Contributing

Thanks for helping improve Agent Pipeline for Codex.

## Development Rules

- Keep the Codex repo aligned with `agent-pipeline-claude` where the shared pipeline contract is unchanged.
- Keep Codex-specific surfaces Codex-specific: `.codex-plugin/plugin.json`, `skills/`, `AGENTS.md` templates, install instructions, and landing-page runtime copy.
- Do not edit historical CHANGELOG entries except to fix factual errors in this repo's runtime-specific split.
- Update README, USER-MANUAL, ARCHITECTURE, CHANGELOG, and `docs/index.html` together when changing user-facing behavior.
- Run the validation checks before pushing:

```bash
python -m pytest -q
python scripts/check_actions_budget.py --all
python scripts/verify_plugin_release.py --source-only
```

Before a plugin release or any claim that the installed Codex Desktop surface
works, also run:

```bash
python scripts/verify_plugin_release.py --live
```

The live verifier must show the namespaced `agent-pipeline-codex:*` skills. A
standalone skill under `$CODEX_HOME/skills` is compatibility only and is not
install proof.

## CI

The GitHub Actions workflow is intentionally source-only so it does not need a
Codex Desktop plugin registry. It runs `verify_plugin_release.py --source-only`
on pull requests and manual dispatch. Local release verification is stricter
and includes the live Codex runtime check.

## Release Checklist

1. Update `.codex-plugin/plugin.json`, README, USER-MANUAL, CHANGELOG,
   ARCHITECTURE, and `docs/index.html` for the new version.
2. Update `skills/agent-pipeline/references/` and
   `skills/pipeline-init/references/pipeline-payload/` so initialized projects
   receive the same policy scripts and docs as the source repo.
3. Run the source-only verifier.
4. Sync the local marketplace, installed plugin cache, and standalone
   compatibility skills.
5. Run the live verifier.
6. Commit, push, and confirm the GitHub Pages deployment if the landing page
   changed.

## Release Notes

This repo follows the version of the runtime-specific Codex plugin. For shared pipeline behavior changes, mirror the corresponding upstream pipeline release and document any Codex-only adaptation separately.
