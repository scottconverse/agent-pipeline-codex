# validate-manifest command

Validate an Agent Pipeline manifest without starting or resuming the pipeline.

## Required input

One of:

- A run id under `.agent-runs/`.
- A direct path to `manifest.yaml`.

## Procedure

1. Resolve the manifest path.
2. Run:

   ```bash
   python scripts/policy/validate_manifest.py --run <run-id>
   ```

   or, from the plugin source tree:

   ```bash
   python scripts/validate_manifest.py --manifest <path>
   ```

3. Report the validator output exactly enough for the user to fix the manifest.
4. Do not start `run-pipeline` from this command.

