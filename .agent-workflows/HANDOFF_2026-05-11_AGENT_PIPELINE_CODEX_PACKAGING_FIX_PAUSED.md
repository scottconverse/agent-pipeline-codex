# Handoff - Agent Pipeline Codex Packaging Fix Paused

Date: 2026-05-11

## Active Target

Fix `agent-pipeline-codex` install packaging so Codex skills installed from GitHub are self-contained and can be invoked after installation.

## Status

RED / paused before implementation.

The repo is published and usable as a source tree, but the GitHub skill-install path is defective.

## Repo State

### agent-pipeline-codex

- Path: `C:\Users\scott\OneDrive\Desktop\Claude\agent-pipeline-codex`
- Branch: `main`
- Remote: `origin https://github.com/scottconverse/agent-pipeline-codex.git`
- Published commit: `d1929ef5f770f8191a9497d43be2d318af0d7161`
- GitHub Pages URL: `https://scottconverse.github.io/agent-pipeline-codex/`

### CivicSuite Context To Preserve

The user asked "where are we with CivicSuite?" immediately before this packaging issue.

CivicSuite state at pause:

- Umbrella repo `C:\Users\scott\OneDrive\Desktop\Claude\CivicSuite`
  - Branch `main...origin/main`
  - HEAD `add3a5b17b5ce62ad20a3f26293e5269c40e5baf`
  - Dirty pre-existing installer generated/dist artifacts remain out of scope.
  - `python scripts/verify-suite-state.py --remote-only` returned `VERIFY-SUITE-STATE: PASSED` for all 26 modules.
- `civicrecords-ai`
  - Branch `fix/b2-remove-secret-file-env-pointers-2026-05-12`
  - HEAD `0c1de94c01d378010dcb9e31d9344cd050e35159`
  - Dirty Phase 1B B2 edits in 18 tracked files.
  - B2 remains RED at Phase 2 rehearsal.
  - Do not tag v1.6.0 or open umbrella release-truth PR without Scott's explicit approval gate.

## What Was Completed This Session

1. Created a separate local repo `agent-pipeline-codex` from `agent-pipeline-claude` v0.5.2.
2. Added Codex-specific:
   - `.codex-plugin/plugin.json`
   - `skills/agent-pipeline/SKILL.md`
   - `skills/pipeline-init/SKILL.md`
   - `skills/new-run/SKILL.md`
   - `skills/run-pipeline/SKILL.md`
   - `skills/audit-init/SKILL.md`
   - `pipelines/templates/AGENTS.md`
3. Updated README, USER-MANUAL, ARCHITECTURE, CHANGELOG, and `docs/index.html` for Codex.
4. Added `CONTRIBUTING.md` and `.gitattributes`.
5. Browser-checked the landing page at desktop and mobile widths.
6. Fixed mobile landing-page clipping/overflow found during QA.
7. Committed:
   - `d1929ef5f770f8191a9497d43be2d318af0d7161`
   - message: `feat: scaffold agent-pipeline-codex plugin`
8. Created/pushed GitHub repo:
   - `https://github.com/scottconverse/agent-pipeline-codex`
9. Enabled GitHub Pages from `main` `/docs`.
10. Verified landing page:
    - `https://scottconverse.github.io/agent-pipeline-codex/`
    - HTTP 200
    - title: `agent-pipeline-codex - structural discipline for agentic development`
11. Installed five skills using `skill-installer`.
12. Found the packaging flaw when invoking `run-pipeline`.

## Exact Packaging Failure

Installed skill path:

`C:\Users\scott\.codex\skills\run-pipeline\SKILL.md`

It contains:

```markdown
Follow the canonical workflow in `../../commands/run-pipeline.md`, adapted for Codex Desktop App:
```

After installation, this resolves to:

`C:\Users\scott\.codex\commands\run-pipeline.md`

That file does not exist.

Confirmed installed files:

```text
C:\Users\scott\.codex\skills\agent-pipeline\SKILL.md
C:\Users\scott\.codex\skills\pipeline-init\SKILL.md
C:\Users\scott\.codex\skills\new-run\SKILL.md
C:\Users\scott\.codex\skills\run-pipeline\SKILL.md
C:\Users\scott\.codex\skills\audit-init\SKILL.md
```

No command files, pipeline templates, policy scripts, or root docs were installed by `skill-installer`.

## Root Cause

The repo was built as a full Codex plugin source tree, but the user installed it through the individual skill installer path. That installer copies only selected `skills/<skill-name>/` directories into `$CODEX_HOME/skills`. Therefore any skill instruction that assumes access to sibling repo folders (`../../commands`, `../../pipelines`, `../../scripts`) breaks once installed.

## Recommended Fix

Implement `agent-pipeline-codex` v0.5.3 as a packaging patch.

### Fix Strategy

Make installed skills self-contained.

Suggested structure:

```text
skills/
  run-pipeline/
    SKILL.md
    references/
      run-pipeline.md
  new-run/
    SKILL.md
    references/
      new-run.md
  audit-init/
    SKILL.md
    references/
      audit-init.md
      audit-gate-template.md
      audit-protocol-template.md
      5-lens-self-audit-template.md
  pipeline-init/
    SKILL.md
    references/
      pipeline-init.md
      AGENTS.md
      pipeline-payload/
        pipelines/...
        scripts/...
  agent-pipeline/
    SKILL.md
    references/
      README.md
      USER-MANUAL.md
      ARCHITECTURE.md
      CHANGELOG.md
```

Then update every `SKILL.md` to reference only paths inside its own folder, such as:

```markdown
Follow `references/run-pipeline.md`.
```

### Validation To Add

Add a script, e.g.:

`scripts/check_skill_packaging.py`

It should:

1. Enumerate every `skills/*/SKILL.md`.
2. Extract backticked relative file references.
3. Resolve references relative to that skill folder.
4. Fail on missing files.
5. Optionally simulate installing each skill into a temp `$CODEX_HOME/skills/<name>` and repeat the check.

Run:

```powershell
python scripts/check_skill_packaging.py
python scripts/auto_promote.py --version
python scripts/check_manifest_schema.py --version
python -m json.tool .codex-plugin/plugin.json
```

### Version Updates

Likely bump:

- `.codex-plugin/plugin.json`: `0.5.2` -> `0.5.3`
- `README.md`: current release -> `v0.5.3`
- `USER-MANUAL.md`: version -> `0.5.3`
- `CHANGELOG.md`: add `[0.5.3] - 2026-05-11` packaging fix
- `docs/index.html`: visible release marks -> `0.5.3`
- `scripts/auto_promote.py --version`: `agent-pipeline-codex 0.5.3`
- `scripts/check_manifest_schema.py --version`: `agent-pipeline-codex 0.5.3`

Because this is a packaging/install bug fix, patch version is appropriate.

## Next Session Steps

1. Read this handoff.
2. Work in:
   `C:\Users\scott\OneDrive\Desktop\Claude\agent-pipeline-codex`
3. Create the self-contained skill references/payload.
4. Update version to `0.5.3`.
5. Add packaging validation script.
6. Run validation.
7. Commit and push.
8. Reinstall skills from GitHub.
9. Invoke `run-pipeline` again and confirm it can read its canonical workflow from the installed skill folder without falling back to the source repo.

## Do Not

- Do not touch CivicSuite B2 while fixing this packaging issue.
- Do not modify `agent-pipeline-claude`.
- Do not assume `skill-installer` installs the full repo.
- Do not leave skills depending on `../../commands` or any path outside the installed skill folder.
- Do not claim the Codex plugin install is fixed until reinstall from GitHub succeeds and `run-pipeline` can load its references from `C:\Users\scott\.codex\skills\run-pipeline`.

## Pause Instruction

Workflow paused here for compaction. Resume with the packaging fix only unless Scott redirects.
