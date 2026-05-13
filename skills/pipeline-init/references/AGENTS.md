# AGENTS.md

This project uses Agent Pipeline for Codex.

## Project Orientation

- Purpose: TODO
- Primary users: TODO
- Stack: TODO
- Test command: TODO
- Lint/static command: TODO

## Order Of Operations

1. Read this file and the active manifest before editing.
2. Keep work inside the manifest's `allowed_paths`.
3. Treat `forbidden_paths` as absolute unless the human director amends the manifest.
4. Run the policy checks and project tests named by the manifest before claiming a stage is ready for verification.
5. If a slice changes `.github/workflows/*.yml` or `.github/workflows/*.yaml`, name the workflow files in the plan before editing, apply the workflow-cost directives below, run `scripts/policy/run_all.py --run <run-id>`, and record workflow-cost evidence in the run artifacts.

## Non-Negotiables

- Do not skip tests.
- Do not silently expand scope.
- Do not rewrite durable release/audit evidence unless the manifest explicitly authorizes it.
- Do not use status words such as done, complete, ready, shippable, or taggable without evidence from the project's release gate.
- Do not add or modify GitHub Actions workflows without satisfying the workflow-cost directives. Unresolved workflow-cost violations are release risks and block completion.

## GitHub Actions Workflow-Cost Directives

1. Never add a daily cron without explicit Scott approval. Weekly is the maximum default schedule. Daily is allowed only for a specific justified need, such as security scanning or dependency drift, and the run record must prove weekly is insufficient before daily is used.
2. Every new GitHub Actions workflow must include the required concurrency block with `group: ${{ github.workflow }}-${{ github.ref }}` and `cancel-in-progress: true`, except release or tag workflows where cancellation would corrupt the release.
3. Do not duplicate `push: branches: [main]` and `pull_request: branches: [main]` for the same validation workflow.
4. Batch work-in-progress commits before pushing; squash local work-in-progress commits when doing so preserves useful history.
5. Add `paths:` filters when adding heavy workflows, including TeX, Docker, Playwright, browser installs, large language models, cleanroom, or e2e validation.
6. macOS jobs are allowed on release tags only unless Scott explicitly approves a PR-fired exception.
7. Windows jobs are allowed on PR only when truly necessary, and the run record or policy evidence must justify the cost.
8. Python version matrices are allowed on tags or weekly cron. PR CI tests one production Python version by default, currently Python 3.12.
9. Cache anything that takes more than 30 seconds to install or download.
10. Every `upload-artifact` step must set `retention-days: 7` unless the artifact is a release artifact or Scott explicitly approves longer retention.

## Pipeline Files

- `.pipelines/` contains the local pipeline definitions and role files.
- `scripts/policy/` contains deterministic policy checks.
- `.agent-runs/` contains per-run artifacts and is gitignored by default.

## Custom Project Rules

TODO: add project-specific conventions, branch policy, documentation requirements, UI/QA gates, security constraints, and release rules.
