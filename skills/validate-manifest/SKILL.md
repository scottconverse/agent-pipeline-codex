---
name: validate-manifest
description: Validate an Agent Pipeline manifest before starting or resuming a run, using the same strict schema enforced by the policy stage.
---

# validate-manifest

Use when the user asks to validate, check, or preflight an Agent Pipeline manifest.

## Workflow

1. Locate the target manifest:
   - If the user gives a run id, use `.agent-runs/<run-id>/manifest.yaml`.
   - If the user gives a path, use that path.
   - If neither is provided, ask for the run id or manifest path and stop.
2. Run the local validator from the project root:
   - `python scripts/policy/validate_manifest.py --run <run-id>` when initialized in a project.
   - `python scripts/validate_manifest.py --manifest <path>` when validating from the plugin repo.
3. Report PASS or the exact violations. Tell the user to edit `manifest.yaml` and rerun the validator before `run-pipeline`.

Do not start the pipeline from this skill. This skill only validates the manifest.

