# Contributing

Thanks for helping improve Agent Pipeline for Codex.

## Development Rules

- Keep the Codex repo aligned with `agent-pipeline-claude` where the shared pipeline contract is unchanged.
- Keep Codex-specific surfaces Codex-specific: `.codex-plugin/plugin.json`, `skills/`, `AGENTS.md` templates, install instructions, and landing-page runtime copy.
- Do not edit historical CHANGELOG entries except to fix factual errors in this repo's runtime-specific split.
- Update README, USER-MANUAL, ARCHITECTURE, CHANGELOG, and `docs/index.html` together when changing user-facing behavior.
- Run the validation checks before pushing:

```bash
python scripts/auto_promote.py --version
python scripts/check_manifest_schema.py --version
python -m json.tool .codex-plugin/plugin.json
```

## Release Notes

This repo follows the version of the runtime-specific Codex plugin. For shared pipeline behavior changes, mirror the corresponding upstream pipeline release and document any Codex-only adaptation separately.
