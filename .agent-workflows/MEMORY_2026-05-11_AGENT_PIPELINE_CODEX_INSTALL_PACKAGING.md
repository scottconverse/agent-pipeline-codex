# Session Memory - Agent Pipeline Codex Install Packaging

Date: 2026-05-11

## Current State

- Local repo: `C:\Users\scott\OneDrive\Desktop\Claude\agent-pipeline-codex`
- GitHub repo: `https://github.com/scottconverse/agent-pipeline-codex`
- GitHub Pages: `https://scottconverse.github.io/agent-pipeline-codex/`
- Current commit: `d1929ef5f770f8191a9497d43be2d318af0d7161`
- Branch: `main`, tracking `origin/main`

## What Happened

The Codex mirror repo was created, committed, pushed, and GitHub Pages was enabled.

The user then asked to install and invoke `https://github.com/scottconverse/agent-pipeline-codex`.
Using `skill-installer`, these skills installed into `C:\Users\scott\.codex\skills`:

- `agent-pipeline`
- `pipeline-init`
- `new-run`
- `run-pipeline`
- `audit-init`

The install was incomplete for real use because the skill installer copied only each `skills/<name>/` directory. The installed `SKILL.md` files reference repo-relative files such as `../../commands/run-pipeline.md`, but after installation that resolves to `C:\Users\scott\.codex\commands\run-pipeline.md`, which does not exist.

## Diagnosis

This is a packaging flaw in `agent-pipeline-codex` v0.5.2:

- The repo works as a source tree.
- The individual installed skills are not self-contained.
- `skill-installer` does not install the full plugin repo, command files, pipeline templates, or scripts when asked to install `skills/...`.

## Next Fix

Make every installable skill self-contained:

1. Add per-skill `references/` folders containing the command or workflow material each skill needs.
2. Update each `SKILL.md` to reference `references/...` paths inside its own installed folder.
3. For `pipeline-init`, include enough payload or clear install mode so it can copy pipeline templates and policy scripts after installation.
4. Add validation that simulates a `skill-installer` install into a temp directory and verifies every referenced path exists.
5. Bump patch version after the packaging fix, likely `0.5.3`, because this is a packaging/install bug fix with no pipeline contract change.

## Pause Point

Do not continue implementation until after compaction. The next session should start from the handoff:

`.agent-workflows/HANDOFF_2026-05-11_AGENT_PIPELINE_CODEX_PACKAGING_FIX_PAUSED.md`
