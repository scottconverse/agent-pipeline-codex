# Latest Test Directive Check - 2026-05-28

## Repo state checked

- Repository: `agent-pipeline-codex`
- Branch: `main`
- Remote tracking state at check time: `main...origin/main`
- HEAD at check time: `34fc924` / `v0.9.1`

## Latest test directive

The latest test-related directive is the v0.9.1 baseline-isolation rule for release rehearsal and verifier test failures.

When `verify-release.sh` or an unexpected verifier test run fails or hangs, first prove whether the same failure exists on the merge-base/main baseline before treating it as a branch regression.

The required isolation move is:

1. Note the failing test name, hang point, or error signature.
2. Stash branch changes.
3. Check out the merge-base against `origin/main`.
4. Re-run the exact same failing command in the same environment.
5. Restore the branch and stash.

Interpretation:

- Baseline passes: debug the branch diff as the regression source.
- Baseline fails the same way: document the baseline SHA and treat it as a pre-existing failure, not a blocker for the branch.
- Baseline fails differently: both failures are real; debug the worse/newer one first.

## Source files

- `README.md`, section `v0.9.1: Baseline isolation for release rehearsal`
- `CHANGELOG.md`, release `0.9.1`
- `skills/pipeline-init/references/pipeline-payload/pipelines/roles/local-rehearsal.md`, Step 2.5
- `skills/pipeline-init/references/pipeline-payload/pipelines/roles/verifier.md`, Tests check
