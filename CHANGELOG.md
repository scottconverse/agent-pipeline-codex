# Changelog

All notable changes to `agent-pipeline-codex` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project follows [Semantic Versioning](https://semver.org/) once it
leaves beta. While in `0.1.x-beta`, breaking changes to slash-command
arguments, manifest fields, or role-file contracts may land in any
release; the `CHANGELOG` will call them out.

## [Unreleased]

## [0.8.0] - 2026-05-17

### Added

- **Intake skill.** Added `agent-pipeline-codex:intake`, a separate
  plain-English onboarding skill for cases where the operator has a product,
  repo, design, task, bug, or feature description but no manifest yet. It drafts
  `.agent-runs/<run-id>/intake.md`, `manifest.yaml`, `scope-lock.yaml`, and
  `intake-questions.md` when required.

### Changed

- **Plugin metadata and install verification.** Bumped the plugin to `0.8.0`
  and expanded install acceptance to require the new namespaced `intake` skill
  plus its bundled command/reference files.

### Security / Safety

- **Failure mode closed.** Operators no longer have to choose between a blank
  `new-run` skeleton and asking the model to improvise work without a manifest.
  `intake` provides a friendly drafting step while preserving the rule that
  execution starts only after manifest review and validation.
- **Honest limit.** Intake drafts are not approval, not directive contracts, and
  not executable authority. They intentionally leave uncertain scope as TODOs
  or intake questions instead of inventing allowed paths, release-plan facts, or
  completion criteria.

## [0.7.0] - 2026-05-16

### Added

- **Optional Codex lifecycle hooks.** Added plugin-bundled hooks for
  `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`,
  `PostToolUse`, and `Stop`. They load active run context, warn on stale
  standalone skill names, guard risky tool calls, deny clearly unsafe approval
  requests, add corrective context after failed tools, and continue invalid
  pipeline stops.
- **Hook utilities and tests.** Added a small read-only hook runtime plus tests
  for active-run discovery, directive-bound detection, hook JSON output,
  prompt warnings, risky tool-call denial, post-tool corrective context, and
  stop-condition continuation.
- **Hook design memo.** Added `docs/design/v-next-hooks.md` with official Codex
  documentation citations, platform limits, and the relationship between hooks,
  directive contracts, the judge layer, and human fallback gates.

### Changed

- **Plugin metadata.** Bumped the plugin to `0.7.0` and declared
  `hooks/hooks.json` in `.codex-plugin/plugin.json`.
- **Install verification.** The plugin install acceptance surface now verifies
  hook files are present and installed alongside skills, commands, pipelines,
  and policy scripts.

### Security / Safety

- **Failure mode closed.** Pipeline discipline no longer depends only on the
  model remembering the orchestrator markdown during long sessions. Codex
  runtime events can now re-inject active run context, block invalid stops, and
  catch obvious unsafe actions before they execute.
- **Honest limit.** Hooks are guardrails, not a full sandbox or replacement for
  the judge layer, directive contracts, policy scripts, or Codex platform
  approvals. Codex access tokens remain optional Business/Enterprise CI
  plumbing and are not required for local Max/Pro-style use.

## [0.6.0] - 2026-05-16

### Added

- **Directive contract auto-approval.** Added optional
  `.agent-runs/<run-id>/directive.yaml` support so directive-conformant runs
  can auto-approve manifest and plan gates without weakening the gate model.
  The directive pre-approves exact manifest and scope-lock content, declares
  plan assertions, declares additional manager assertions, names author and
  authority source, and binds a SHA-256 hash into `run.log` at run start.
- **Directive policy scripts.** Added `check_directive_conformance.py`,
  `check_plan_against_directive.py`, and shared directive utilities. Mismatch,
  malformed directives, absent directives, and hash tampering all fail closed
  to the existing interactive path, with manifest/scope mismatch reported as a
  unified diff.
- **Directive template and design memo.** Added `pipelines/directive-template.yaml`
  and `docs/design/v-next-directive-contract.md` with platform citations,
  schema, preserved protections, new protections, migration notes, and honest
  limits.
- **Directive regression tests.** Added coverage for conformant auto-approval,
  non-conformant fallback with diff output, absent-directive prior behavior,
  mid-run directive tampering, run-log hash mismatch on resume, and manager
  assertion extension through `auto_promote.py`.

### Changed

- **Auto-promote is six plus N.** `auto_promote.py` still requires the six
  v0.5 conditions, then adds every directive-declared manager assertion when a
  directive is present. `manager-decision.md` cites the directive hash, author,
  authority source, and satisfied directive assertions.
- **Execute-stage DoD readiness gate.** Executor and runner instructions now
  forbid advancing a partial slice to policy/verify. `implementation-report.md`
  must declare `**DoD readiness: READY**` with a parseable zero-blocker DoD
  checklist, and `check_execute_readiness.py` now blocks `run_all.py` when the
  full manifest Definition of Done is not implemented or explicitly deferred.
- **Live install verification hardening.** The live plugin acceptance gate now
  runs repeated fresh Codex probes and preserves each transcript so one
  transient model enumeration miss cannot fail a release when deterministic
  installed-cache/source checks are correct.
- **Main-branch CI coverage.** The source-only release verifier now runs on
  pushes to `main`, not only pull requests and manual dispatches.

### Security / Safety

- **Failure mode closed.** Directive-conformant runs no longer force operators
  to re-type APPROVE for manifest and plan content they already authored
  verbatim, reducing reflexive approval training while preserving every prior
  gate's catchable failure mode.
- **Honest limit.** Directive contracts can encode machine-checkable assertions
  over artifacts. They cannot encode taste, novel judgment, future high-risk
  tool calls, credentials, destructive actions, or Codex platform approvals; any
  such case keeps the human gate cost.

## [0.5.10] - 2026-05-14

Patch release. Closes stale-control-state stop escapes by binding final,
continue, and agent-decision gates to one shared stop validator.

### Added

- **Shared stop validator.** Added `scripts/stop_validator.py` and scaffold
  payload coverage so `final_response_gate.py`, `pipeline_continue.py`, and
  `agent_decision_gate.py` all use the same stop-condition truth function.
- **Run-evidence stop checks.** Human approval stops are now valid only at the
  manifest, plan, or manager gates and must match the resume stage derived from
  `run.log` when pipeline evidence exists. Failed-gate stops require a matching
  `FAILED` or `BLOCKED` event when `run.log` exists.
- **Regression tests for stale stops.** Added focused coverage for stale human
  gates, failed-gate proof, and evidence-file-only unrecorded blocker claims.

### Changed

- **Evidence-bound decisions.** `agent_decision_gate.py` no longer accepts
  plain text evidence for unrecorded blocker claims. If the claimed blocker
  does not match active control state, it must cite an existing evidence file.
- **Centralized continuation behavior.** `pipeline_continue.py` now reports
  validator failures from the same logic used by `final_response_gate.py`,
  preventing valid-looking stale control state from becoming an escape hatch.

## [0.5.9] - 2026-05-14

Patch release. Adds mechanical rung/scope authority so the pipeline proves it
is working on the canonical release-plan rung before product edits begin.

### Added

- **Canonical scope lock.** `new-run` now creates
  `.agent-runs/<run-id>/scope-lock.yaml` from
  `.pipelines/scope-lock-template.yaml`. Product work must name the canonical
  source, current rung, title, proof statement, required modules, allowed
  feature terms, forbidden future-rung terms, scope bullets, and exit criteria.
- **Scope-lock policy check.** Added `check_scope_lock.py`, which fails when
  the run lacks a scope lock or when the lock does not match the declared rung
  in the canonical release plan.
- **Rung ownership policy check.** Added `check_rung_file_ownership.py`, which
  blocks edited paths and commit subjects that contain future-rung terms such
  as publish-dashboard work under a summary-records rung.
- **Release-doc consistency policy check.** Added
  `check_release_docs_consistency.py`, which blocks docs that describe the
  current rung using terms owned by another rung.
- **Start-rung decision gate.** `agent_decision_gate.py` now supports
  `--intent start_rung_work --claimed-rung <rung> --prompt-text "<prompt>"`
  and blocks prompt/plan conflicts with `SCOPE_CONFLICT`.
- **Scope-lock receipt.** `run_all.py` writes
  `.agent-runs/<run-id>/scope-lock-receipt.txt` after scope lock, rung
  ownership, and docs consistency checks pass.

### Changed

- **Control-loop contract.** The documented control loop now states that the
  agent may not infer the release ladder changed. Conflicting user wording
  requires `scope_conflict` and an explicit scope amendment before edits.
- **Policy stage.** The combined policy runner now includes the three scope
  authority checks as hard gates for run-aware policy execution.

## [0.5.8] - 2026-05-13

Patch release. Adds promotion polish after the v0.5.7 re-evaluation: clearer
status output, a production ledger writer-to-validator test, tighter git
classification regressions, and public CI badges.

### Added

- **Run-log transparency.** `show-run-status` now reports how many malformed
  `run.log` lines it skipped, so crash-recovery status reads cannot silently
  hide partial writes.
- **Ledger writer-to-validator coverage.** Added a regression test that writes
  a real `decision-ledger.ndjson` row through `agent_decision_gate.py` and then
  validates it with `check_decision_ledger.py`.
- **Focused git-classification negatives.** Added tests proving the feature
  branch push rule does not catch read-only git commands, main pushes, or
  force pushes, and that the force-push rule catches both argument orders.
- **CI visibility.** Added source-only CI badges to README and CONTRIBUTING.

## [0.5.7] - 2026-05-13

Patch release. Closes the v0.5.6 audit punch list by hardening action
classification tests, manifest parser failure modes, run-state visibility, and
ledger validation.

### Added

- **Action-classification regex tests.** Added fixtures that compile and
  exercise every shipped `action-classification.yaml` regex against matching
  and non-matching commands.
- **Run status command.** Added `scripts/show_run_status.py`,
  `commands/show-run-status.md`, and the `show-run-status` skill so operators
  can inspect a run without resuming it.
- **Decision-ledger validator.** Added `scripts/check_decision_ledger.py` and
  schema-v1 rows for `decision-ledger.ndjson`.
- **Pipeline fixture integration test.** Added a deterministic fixture that
  exercises auto-promote, control-state validation, final-response blocking,
  decision gating, run-status output, and ledger validation together.

### Changed

- **Manifest parser fail-closed behavior.** The constrained stdlib manifest
  parser now explicitly rejects unsupported YAML block scalars, anchors,
  aliases, and merge keys instead of silently misreading them.
- **Judge tuning visibility.** The run-pipeline handler now requires a
  checkpoint summary of judge action counts, blocks, revisions, and
  escalation rate after executor runs with the judge layer active.
- **First-use workflow.** README and USER-MANUAL now place
  `validate-manifest` between `new-run` and `run-pipeline`, and list
  `show-run-status` as the read-only status path.

### Fixed

- **Ambiguous test report parsing.** `auto_promote.py` now blocks if any
  non-zero failure count appears anywhere in `implementation-report.md`, even
  when another suite line says `0 failed`.
- **Version-test brittleness.** Release tests now derive expected version
  strings from plugin metadata instead of hard-coding a release number.
- **Mermaid reliability.** Architecture diagrams were simplified and kept to
  GitHub-safe Mermaid syntax.

## [0.5.6] - 2026-05-13

Patch release. Finishes the shared policy-helper migration, hardens
auto-promote parser coverage, and makes plugin handoff prompts require the
namespaced `agent-pipeline-codex:*` skill surface so stale standalone skill
copies cannot masquerade as the current plugin.

### Added

- **Policy utility regression tests.** Added tests for shared repo-root
  detection in source and installed layouts, plus quoted-hash YAML comment
  stripping.
- **Auto-promote parser edge coverage.** Added tests for count lines with
  mixed case and extra comma spacing, malformed verifier/critic count lines,
  and blocker drift count lines.

### Changed

- **Shared policy utility migration.** Moved the remaining policy scripts onto
  `scripts/policy_utils.py` for repo-root detection so source and scaffolded
  project layouts use one implementation.
- **Namespaced plugin guidance.** Updated install and fresh-session guidance to
  require `agent-pipeline-codex:agent-pipeline`,
  `agent-pipeline-codex:pipeline-init`,
  `agent-pipeline-codex:new-run`,
  `agent-pipeline-codex:run-pipeline`,
  `agent-pipeline-codex:audit-init`, and
  `agent-pipeline-codex:validate-manifest` when proving the plugin is active.

### Fixed

- **Standalone skill drift.** Treat stale standalone skills under
  `$CODEX_HOME/skills` as install-surface drift and document that plugin
  verification must use the namespaced plugin skill list.
- **User Manual skill count.** Corrected the operator-facing skill inventory to
  include `validate-manifest`.

## [0.5.5] - 2026-05-13

Patch release. Hardens the policy layer against audit-found bypasses, adds a
manifest preflight command, centralizes workflow-cost directives, and adds
source-only CI for the plugin repo.

### Added

- **Manifest preflight command.** Added `scripts/validate_manifest.py`,
  `commands/validate-manifest.md`, and the `validate-manifest` skill so
  operators can check a manifest before starting or resuming a run.
- **Policy regression tests.** Added coverage for manifest hash parsing,
  forbidden status words, broad-path requirements, allowed-path parsing,
  untracked-file detection, committed workflow diff detection, and
  auto-promote artifact decisions.
- **Source-only CI workflow.** Added a lightweight pull-request and
  workflow-dispatch CI workflow that runs `verify_plugin_release.py
  --source-only` without requiring a local Codex Desktop plugin registry.
- **Canonical workflow-cost directive file.** Added
  `.pipelines/templates/workflow-cost-directives.md` so AGENTS and role files
  reference one binding list instead of drifting copies.
- **Fail-closed final-response gate.** Added `scripts/final_response_gate.py` and scaffold payload coverage for `scripts/policy/final_response_gate.py`. The gate discovers active `.agent-runs/*/active-control-state.md` files and blocks final responses whenever an authorized run still has `final_response_allowed: false`.
- **Agent decision gate and ledger.** Added `scripts/agent_decision_gate.py` to validate stop/defer/skip/final decisions, reject unverified blocker claims, and append `.agent-runs/<run-id>/decision-ledger.ndjson`.
- **Pipeline continuation navigator.** Added `scripts/pipeline_continue.py` to print the next required action for active runs when stopping is not allowed.
- **Public docs for control-loop enforcement.** Updated the landing page, architecture diagrams, and discussion seed posts so the public surface explains the final-response gate, decision gate, decision ledger, and continuation navigator.
- **Mechanical control-loop gate.** Added `scripts/check_pipeline_control_loop.py`, `.agent-runs/<run-id>/active-control-state.md`, and `docs/process/pipeline-control-loop.md` so authorized runs cannot end unless a valid stop condition is recorded and checked.
- **Workflow-cost policy gate.** Added `scripts/check_actions_budget.py` and scaffold payload coverage so changed GitHub Actions workflows are checked for mandatory cost directives before a slice can complete.

### Changed

- **Workflow-cost gate now sees committed workflow diffs.**
  `check_actions_budget.py --run <run-id>` compares HEAD against the upstream
  or explicit base ref so committed workflow edits cannot pass vacuously when
  `git status` is clean.
- **Allowed-path gate now includes untracked files.** New files created by the
  executor are checked before they are staged or committed.
- **Release verifier supports headless CI.** `verify_plugin_release.py
  --source-only` runs the non-live release checks when Codex Desktop is not
  available.
- **Continuation is executable.** Updated `run-pipeline`, `feature.yaml`, `bugfix.yaml`, `manifest-template.yaml`, manager, verifier, and implementer-pre-push roles so successful push, green CI, draft PR status, unverified blockers, recommended next action, and release/tag after all gates pass are not stop conditions. The final-response and decision gates must pass before stopping is allowed.
- **Caveats are blocking.** `Open Caveats / Release Risks` now blocks completion unless each item is fixed or marked `INTENTIONAL DEFERRAL:` with cited authorization.
- **Workflow-cost discipline is slice completeness.** Updated runtime `run-pipeline`, scaffolded AGENTS.md, planner/executor/verifier/manager role guidance, and control-loop docs so workflow file changes must name touched workflows, apply the 10 directives, record evidence, and treat unresolved violations as release risks.

### Fixed

- **Quoted `#` manifest values.** The minimal manifest parser now strips YAML
  comments without truncating `#` characters inside quoted scalar or list
  values.
- **Source mojibake/BOM cleanup.** Removed encoded-dash/section corruption and
  BOM residue from source and scaffold copies.
- **Mermaid sequence diagrams.** Quoted participant labels and removed angle
  brackets from sequence participant display names so GitHub rendering has a
  valid Mermaid surface.

## [0.5.4] - 2026-05-13

Patch release. Adds a real Codex Desktop plugin install-acceptance gate so
repository tests cannot be mistaken for slash/plugin registration proof.

### Added

- **Plugin install-acceptance gate.** Added `scripts/check_plugin_install_acceptance.py`.
  Static mode verifies `.codex-plugin/plugin.json`, the expected skills,
  Codex `config.toml`, the local marketplace manifest, and the installed
  cache version. Live mode launches a fresh `codex exec` process and verifies
  `agent-pipeline-codex` appears under Available plugins, exposes all expected
  namespaced skills, and emits no plugin-specific loader warnings.
- **Plugin release verifier.** Added `scripts/verify_plugin_release.py` so the
  source tests, skill packaging check, static plugin install check, and live
  Codex runtime check can be run as one release gate.
- **Install-surface tests.** Added pytest coverage for the source skill layout,
  a valid installed Codex-home layout, and the missing-plugin failure path.
- **Nested skill-packaging scan.** `check_skill_packaging.py` now scans bundled
  reference markdown as well as `SKILL.md` so installed procedure files cannot
  keep stale repo-root references undetected.

### Fixed

- **Skill loader errors.** Removed a BOM from `skills/agent-pipeline/SKILL.md`
  and quoted YAML descriptions in all skill frontmatter so every expected
  namespaced plugin skill loads cleanly.

### Required release proof

Before claiming a plugin release is installed, run:

```bash
python scripts/verify_plugin_release.py --live
```

The release is not complete unless that command prints
`PLUGIN-RELEASE-VERIFY: PASSED` and the nested
`PLUGIN-INSTALL-ACCEPTANCE: PASSED`.

## [0.5.3] - 2026-05-11

Patch release. Fixes GitHub skill-install packaging so each installed Codex
skill is self-contained under `$CODEX_HOME/skills/<name>`.

### Fixed

- **Self-contained installed skills.** Bundled each skill's command references,
  templates, pipeline definitions, and policy scripts inside that skill folder
  so `skill-installer` installs everything the skill needs.
- **Packaging regression check.** Added `scripts/check_skill_packaging.py` to
  simulate installed skill folders and fail on parent-directory references or
  missing bundled files.

### Migration

Reinstall the skills from `agent-pipeline-codex` v0.5.3. Existing project
scaffolds and `.agent-runs/` artifacts are unchanged.
## [0.5.2] - 2026-05-11

Runtime split release. The plugin is now `agent-pipeline-codex` and is published as the Codex Desktop App companion to `agent-pipeline-claude` v0.5.2. The structural surface is unchanged; the runtime packaging, plugin manifest, project-instructions template, and user-facing install language are Codex-specific.

### Changed

- **Plugin split.** `agent-pipeline-codex` mirrors `agent-pipeline-claude` v0.5.2 as a separate runtime-specific repo with its own `.codex-plugin/plugin.json`, `skills/`, and `pipelines/templates/AGENTS.md`.
- **Codex skill entrypoints.** Added skills for overview/routing, project onboarding, run initialization, run orchestration, and audit-handoff scaffolding. The command markdown remains as canonical workflow logic, with skills adapting the tool names to Codex.
- **Codex documentation and landing page.** README, USER-MANUAL, ARCHITECTURE, and `docs/index.html` identify Codex Desktop App as the runtime and use `agent-pipeline-codex` repository links.

### Why this release exists

The Claude Code side and the Codex Desktop App side had been entangled in one repo, with parallel plugin manifests, parallel orchestration logic, and a version-string invariant that had to handle both. The two sides have different runtime models, different distribution mechanisms, and different release cadences. Separating them removes the entanglement and lets each side ship on its own schedule.

`0.5.2` rather than `0.6.0` because the surface area of the plugin (commands, roles, policy scripts, pipeline definitions, run state) is unchanged. The change is purely identity (name) and scope (single-runtime).

### Migration

Existing installs:

```bash
# Update the plugin reference in Codex Desktop App
git clone https://github.com/scottconverse/agent-pipeline-codex.git ~/agent-pipeline-codex-plugin
```

Projects already initialized with `pipeline-init` continue to work - the scaffolded `.pipelines/`, `scripts/policy/`, and `.agent-runs/<run-id>/` files are unchanged. Re-running `pipeline-init` to refresh the scaffolded scripts is recommended but not required.

The GitHub repo URL change propagates automatically via GitHub's redirect for git clone, but bookmarks to `https://github.com/scottconverse/agentic-pipeline` and `https://scottconverse.github.io/agentic-pipeline/` should be updated to use the new name.

---

## [0.5.1] - 2026-05-11

Patch release. Adds standing doc-currency invariants to the drift-detector role so cumulative drift cannot ship under a feature-scoped manifest.

### Why this release exists

v0.5's drift-detector was contracted against the manifest's `expected_outputs` only. That contract is sound for the run's own scope but lets cumulative drift accumulate across releases: a feature-scoped manifest legitimately ships its feature, the verifier passes, but the project's top-of-file content (counts, tables, diagrams, version strings, section orderings) goes stale because nothing in the manifest names the back-audit.

The v0.5 dogfood run (`.agent-runs/2026-05-11-version-flag/`) had this exact gap - the drift-detector caught the in-scope `--version` drift but did not flag months-stale top-of-file content in README, USER-MANUAL, and `docs/index.html`. The fix is structural: invariants every release silently makes get their own enforcement, independent of any manifest.

### Changed

- `pipelines/roles/drift-detector.md` - added Section 8 **Standing doc-currency invariants**. Five invariants checked on EVERY run regardless of manifest scope:
  - **8a Version-string consistency** (`blocker` on mismatch): every authoritative version string in the repo agrees - `plugin.json`, `marketplace.json` (top-level metadata AND each plugin entry), `pyproject.toml` if present, every `argparse action="version"` string under `scripts/`, the top `## [X.Y.Z]` in `CHANGELOG.md`, `<div class="badge">vX.Y.Z` in `docs/index.html`, `**Version:** X.Y.Z` in `USER-MANUAL.md`.
  - **8b File-inventory tables** (`non-blocker` on small drift, `blocker` on whole-release-missing): USER-MANUAL "What you get" counts match `ls` reality; README scaffold block lists every file actually in `pipelines/roles/` and `scripts/`.
  - **8c Pipeline-diagram parity** (`blocker` on docs releases): `docs/index.html` `.pipeline-diagram` stages match `pipelines/feature.yaml` stage list and order.
  - **8d Section-ordering sanity** (`non-blocker`): per-version sections in README and USER-MANUAL appear in monotonic order; a `## v0.5:` followed by a `## v0.4:` is a reliable back-audit signal.
  - **8e Stability-posture currency** (`non-blocker`): any explicit current-release version reference in `docs/index.html` matches the current release.
- Output checklist updated to require explicit PASS/FAIL on every standing invariant.
- Drift item numbering shifted: Section 8 was Drift items; now Section 9. The count line in Section 2 was already abstracted across all numbered drift sections, so this is a forward-compatible rename.
- `--version` flag bumped to `agent-pipeline-codex 0.5.1` on `scripts/auto_promote.py` and `scripts/check_manifest_schema.py`.

### Stacking with v0.2, v0.3, v0.4, v0.5

No new stages, no new role files, no new policy scripts. v0.5.1 extends the contract of the existing drift-detector role file. All v0.5 behavior is preserved; the only behavioral change is that more drift items will be flagged on future runs.

### Honest limit

The standing invariants are enforced by a role file the drift-detector subagent reads. A subagent could in principle disregard a hard rule. The structural backstop is `auto_promote.py`'s read of the drift count line - if the drift-detector reports blocker drift, auto-promote refuses to fire, and the manager human-approval gate runs. The invariants harden the role contract but do not replace the auto-promote gate.

---

## [0.5.0] - 2026-05-11

The single-AI hardened release. Six structural changes that compensate for dropping dual-AI cross-family verification: two new agent roles (critic, drift-detector), pre-edit fact-forcing in the executor, expanded judge classification, machine-checkable auto-promote, and strict manifest schema validation. Built from the design question "can the pipeline do both action-level judge AND post-hoc audit with one AI?" Answer: yes, with the structural defense in this release.

The release is a structural substitute for the dual-AI audit-handoff discipline (v0.3) when running with a single AI. Existing dual-AI projects keep working; nothing in this release removes capability. The shipped honest limit: same-model-family verification cannot fully replace cross-family verification. The CHANGELOG entry below names the residual risk and the recommended mitigation.

### Added

- `pipelines/roles/critic.md` - adversarial critic role file. Fires after the verifier in a fresh context. Reads every artifact cold and produces a structured findings report with a parseable Section 2 count line (`**Findings: T total, B blocker, C critical, M major, N minor**`). Walks six adversarial lenses: engineering, UX, tests, docs, QA, scope. Hard rules forbid encouragement, severity softening, "no findings" without per-lens evidence, and trusting the verifier or executor at face value. Structural substitute for cross-family verification in single-AI runs.
- `pipelines/roles/drift-detector.md` - drift-detector role file. Fires after the verifier (before the critic). Compares manifest fields against the final assembled state. Catches the gap class neither the judge (per-action) nor the verifier (per-criterion) can see - durable doc drift, cross-file consistency, status-word abuse, ledger top-totals vs row counts, "Closed" without evidence. Emits parseable Section 2 count line (`**Drift: T total, B blocker**`).
- `scripts/check_manifest_schema.py` - manifest schema validator. Wired into both run-pipeline.md Phase A2 (run-start, before any stage fires) and `scripts/run_all.py` CHECKS (policy stage, defense in depth). Rules: `goal` >= 30 chars, `definition_of_done` >= 80 chars, `expected_outputs` non-empty, `non_goals` non-empty, `rollback_plan` non-empty, broad `allowed_paths` requires non-empty `forbidden_paths`, forbidden status words (`done`, `complete`, `ready`, `shippable`, `taggable`) banned from goal/dod. The fuzzy-manifest class of failure now blocks at the gate before it cascades into downstream work.
- `scripts/auto_promote.py` - machine-checkable promote decision. Reads verifier-report.md, critic-report.md, drift-report.md, policy-report.md, judge-metrics.yaml (when present), and implementation-report.md. Evaluates six conditions: verifier-clean (zero NOT MET, zero PARTIAL), critic-clean (zero blocker, zero critical), drift-clean (zero blocker), policy-passed, judge-clean (zero judged_block, zero human_blocked, vacuous when judge inactive), tests-passed. When all six pass, writes a preset `manager-decision.md` with `**Decision: PROMOTE**` and a citation block; otherwise writes `auto-promote-report.md` naming the failing conditions and exits 1.
- `--version` flag on `scripts/auto_promote.py` and `scripts/check_manifest_schema.py`. Operators run either script with `--version` to print `agent-pipeline-codex 0.5.0` and confirm which release is installed. The flag uses argparse's built-in `action="version"`, so it fires before required-arg validation - `auto_promote.py --version` works without supplying `--run`. Output is `agent-pipeline-codex 0.5.0` on stdout, exit code 0. Added as the deliverable of the v0.5 self-dogfood pipeline run (`.agent-runs/2026-05-11-version-flag/`, gitignored), which exercised every new v0.5 stage end-to-end and validated the auto-promote short-circuit.

### Changed

- `pipelines/roles/executor.md` - added a "Pre-edit fact-forcing gate" section. Before the first edit/write to any file in the run, the executor must produce a fact block (importers/callers, public API affected, data schema touched, manifest goal quoted verbatim) either inline in `implementation-report.md` or in `.agent-runs/<run-id>/notes/pre-edit-<filename>.md`. The drift-detector and critic stages check for the block and treat its absence as a finding on any touched file.
- `pipelines/roles/verifier.md` - added Section 0 "Criteria count line" requirement. The verifier must emit `**Criteria: T total, M MET, P PARTIAL, N NOT MET, A NOT APPLICABLE**` as a parseable line so `auto_promote.py` can read the verdict count without scanning the full report.
- `pipelines/roles/manager.md` - added "Auto-promote awareness (v0.5)" section. When `manager-decision.md` already exists with `**Decision: PROMOTE**` as the first line (auto-promote preset), the manager runs in validate-and-append mode instead of re-deciding. Inputs list extended with drift-report.md, critic-report.md, auto-promote-report.md, and judge-log.yaml/judge-metrics.yaml when present. PROMOTE criteria extended: critic blocker/critical = 0, drift blocker = 0, judge judged_block + human_blocked = 0.
- `pipelines/action-classification.yaml` - five new patterns under `high_risk`: `npm install --global` and `npm install -g`, `sudo`, `pip install` (non-editable, non-user), `git commit` with BREAKING in the message. Each tightens action-time defense against the failure modes operators most commonly cite.
- `pipelines/feature.yaml` - three new stages between `verify` and `manager`: `drift-detect`, `critique`, `auto-promote`. Manager stage gets `auto_promote_aware: true` flag.
- `pipelines/bugfix.yaml` - same three new stages and the manager flag.
- `pipelines/module-release.yaml` - three new phases between `phase4-verify` and `phase5-manager`: `phase4b-drift-detect`, `phase4c-critique`, `phase4d-auto-promote`. `phase5-manager` gets `auto_promote_aware: true`.
- `commandsrun-pipeline.md` - Phase A2 now invokes `check_manifest_schema.py` before any stage runs. Handler 2 (`role: pipeline`) handles `optional_artifact: true` for the auto-promote stage. New **Handler 4** for `role: manager` with `auto_promote_aware: true`: checks for the preset, short-circuits the human gate when present, falls through to standard Handler 3 + Handler 1 when absent.
- `scripts/run_all.py` - `check_manifest_schema` added to `CHECKS` list. Runs first so a fuzzy manifest fails the policy stage even if it slipped past Phase A2.

### Why each piece exists

- **Critic stage.** v0.4's judge catches per-action scope violations in real time, but doesn't read the assembled output. The verifier reads the assembled output, but in the same model family as the executor - correlated blind spots are exactly the class of failure neither catches. The critic runs in a fresh context with a deliberately adversarial role contract.
- **Drift-detector stage.** Drift between manifest contract and durable artifacts is invisible to per-action and per-criterion verification. It only surfaces when you compare the manifest's promises to the assembled final state.
- **Pre-edit fact-forcing in executor.** Asking an LLM "are you sure?" is useless. Demanding concrete artifacts (importer list, schema, instruction quote) forces investigation that catches blast-radius surprises before they hit the verifier.
- **Expanded judge classification.** Global npm installs leak project-level promises into system-level state; sudo escalations sidestep manifest scope; non-editable pip installs in shared environments produce non-reversible side effects; BREAKING-marked commits are semver-major signals deserving explicit confirmation.
- **Machine-checkable auto-promote.** The manager gate becomes auto-firing when all six structural conditions hold. Humans get the time back without losing the gate - when any condition fails, the human gate is still there.
- **Strict manifest schema validation.** Every drift cascade investigated in prior projects traced back to a fuzzy manifest. The schema check makes the fuzzy state fail-fast.

### Stacking with v0.2, v0.3, v0.4

- v0.2 module-release pipeline: catches execution-cascade failures (pre-existing CI bugs, tag-move dances, halt-and-ask loops). Pre-executor.
- v0.3 dual-AI audit-handoff: catches drift failures via cross-family separation of duties. Post-executor, separate session.
- v0.4 judge layer: catches unauthorized actions in real time. During executor.
- **v0.5 hardened single-AI**: catches the drift class without needing a second AI, at the cost of accepting some correlated blind spots. During verify -> drift-detect -> critique -> auto-promote.

Use v0.3 when you have two model families available. Use v0.5 when you want single-AI operation. The two stack - projects can run both, with v0.3's cross-family audit firing on a sample of v0.5 runs.

### Known limitations

- **Correlated single-model-family blind spots.** Critic and verifier are both same-model-family. If both agents share a wrong assumption that fits the manifest, both sign off and the auto-promote fires green. Dual-AI is the only structural defense against this. Mitigation: periodic sample audit by a different model family on a weekly cadence or after every Nth run. The v0.3 `audit-init` discipline still applies.
- **Auto-promote depends on parseable count lines.** The verifier, critic, and drift-detector role files explicitly require the count-line format. If a role file is customized in a way that drops or malforms the line, auto_promote.py treats the run as NOT_ELIGIBLE and falls back to the human gate.
- **The judge layer still fires only on the executor stage.** Even with v0.5 active, the judge does not intercept critic, drift-detector, or verifier actions. Those roles are read-only by contract.
- **Schema validation cannot verify manifest correctness, only structure.** A confident-wrong manifest that satisfies every schema rule still produces wrong work. The manifest gate (human) remains the only place the manifest's content is reviewed.

## [0.4.0] - 2026-05-11

The judge layer. Real-time action-level supervision inside the executor stage. Built from Nate Jones, "LLM-as-Judge" (May 2026). The Lindy case study - an agent that sent 14 unauthorized emails because operator-trained-reflex APPROVE clicking defeated manual confirmation - showed that prompts don't hold across long context, and per-action confirmation alone breeds the cookie-banner effect. The architectural fix is a second agent (the judge) whose sole loyalty is the manifest, evaluated in context isolation from the executor's reasoning chain.

### Added

- `pipelines/roles/judge.md` - role file for the judge subagent. Returns exactly one of four verdicts: `allow`, `block`, `revise`, `escalate`. Output is a single YAML block, no prose. Hard rules forbid helping the executor, negotiating, inferring authorization, summarizing, deferring to executor confidence, approving by precedent, or modifying anything outside the verdict file. Inputs are deliberately scoped: manifest, matched action policy, prior judge decisions for the run, and the structured action proposal - but **not** the executor's reasoning chain. Context isolation is the mechanism.
- `pipelines/action-classification.yaml` - opt-in classification rules. Four risk classes (`read_only`, `reversible_write`, `external_facing`, `high_risk`) with first-match-wins evaluation top-to-bottom within each class. Class priority `high_risk` -> `external_facing` -> `reversible_write` -> `read_only`. Default class for unmatched actions: `reversible_write`. Ships with the common dangerous and external-facing patterns: `rm -rf`, `git push --force`, `git push main`, `DROP TABLE`, `npm publish`, `gh pr create`, `curl -X POST`, `docker push`, `kubectl apply`, credential-touching `export *KEY=`, etc.
- `commandsrun-pipeline.md` - **Handler 3a** for the executor stage when `.pipelines/action-classification.yaml` exists. Wraps the executor in a classify -> judge -> execute inner loop. Routes by class: `read_only` and `reversible_write` execute immediately + log; `external_facing` requires judge ALLOW; `high_risk` requires judge ALLOW plus human confirm. Verdict routing: `allow` executes, `block` halts the pipeline, `revise` returns a concrete revision instruction (max 3 cycles per action_id; auto-escalate after), `escalate` pauses for a specific human question. Handler 3 (the v0.3 executor handler) is preserved unchanged and is selected when `action-classification.yaml` is absent - the layer is opt-in by file presence.
- `judge-log.yaml` artifact - chronological per-action record written to the run directory when the judge layer is active. Captures tool, arguments, class, disposition (`auto_allow` / `judged_allow` / `judged_revise` / `judged_block` / `judged_escalate` / `human_confirmed` / `human_blocked`), judge verdict, judge reason, revision instruction, and timestamp.
- `judge-metrics.yaml` artifact - aggregate counts plus `escalation_rate`, `judge_invocations`, `revision_cycles`. Written alongside `judge-log.yaml` at executor-stage end. The escalation rate is the operator's tuning signal - see USER-MANUAL.md Section "The judge layer (v0.4)".
- `judge-decisions/<action_id>.yaml` directory - per-action verdict files written by the judge subagent. Read by the next judge invocation as `prior_judge_decisions` so re-proposals of blocked actions are detected without depending on conversation memory.
- ARCHITECTURE.md Section 7 - full design rationale, the classify -> judge -> execute inner-loop diagram, the context-isolation diagram, the relationship-to-other-gates table, the four-verdicts spec, and the opt-in-by-file-presence model.
- README.md Section "v0.4: Judge layer" - quickstart overview with the four classes, the four verdicts, and the artifacts produced. One-line summary: "Pipeline (v0.2) catches execution-cascade failures. Audit-handoff (v0.3) catches drift failures. Judge layer (v0.4) catches unauthorized actions in real time."
- USER-MANUAL.md Section "The judge layer (v0.4)" - operator-facing guidance. Enabling and disabling, customizing rules per project, reading `judge-log.yaml` and `judge-metrics.yaml`, escalation-rate tuning (too-low vs too-high vs healthy range 0.02-0.10), adding project-specific high-risk patterns, and what to do when the judge ESCALATEs and you aren't sure (don't reflex-APPROVE - fix the manifest ambiguity).

### Why each new piece exists

- **Context isolation prevents single-model-family correlated judgment.** The judge cannot be persuaded by the same chain of inferences that produced the over-broad action because it never sees them. The manifest and the action proposal are the inputs; the executor's reasoning chain is deliberately withheld.
- **Four verdicts, not two, prevent BLOCK fatigue.** ALLOW / BLOCK alone forces the judge into binary calls on actions where a small revision (push to feature branch, not main) would make the action correct. `revise` and `escalate` give the judge ways to be useful without halting the pipeline on every borderline call.
- **High_risk + human confirm even after judge ALLOW is belt-and-suspenders.** A judge ALLOW on `rm -rf` or `git push --force` is still a moment a human should see. The judge's ALLOW raises confidence that the action is authorized; the human confirm is the final check that no inferred-authorization slipped through.
- **Opt-in by file presence keeps the layer composable.** Projects that don't need real-time action supervision (small repos, no external services, mature contributor base) can run without the file and get v0.3 behavior. Projects that need it add one YAML file. There is no separate `/enable-judge` command and no manifest field to remember.
- **Metrics in `judge-metrics.yaml`, not just logs, give the operator a tuning loop.** Without an aggregate, operators can't tell whether they're at 0% escalation (rules too loose) or 30% (cookie-banner fatigue forming). The `escalation_rate` is computed every run; reviewing it after the first 5-10 runs typically converges the rules to a healthy range.

### Stacking with v0.2 and v0.3

- Pipeline (v0.2) catches execution-cascade failures: pre-existing CI bugs, tag-move dances, halt-and-ask loops. Pre-executor.
- Audit-handoff (v0.3) catches drift failures: wrong endpoint, stale CHANGELOG, status-word abuse. Post-executor.
- **Judge layer (v0.4) catches unauthorized actions in real time.** **During** the executor stage, at the action boundary, before the action lands. The other two run before and after the executor; the judge runs **during**.

The three layers address three different failure classes and can be enabled independently. Many projects will run all three.

### Known limitations

- **Single-model-family blind spots may still correlate.** The judge is a subagent of the same model family as the executor. Some classes of failure (e.g., a particular phrasing that biases both agents identically) can persist. The architectural defense (context isolation) reduces this risk; it does not eliminate it.
- **The judge is slower than no-judge.** Every `external_facing` and `high_risk` action incurs a subagent spawn. For executor stages dominated by `read_only` and `reversible_write` actions this is negligible; for stages with many external operations (e.g., heavy `gh` API or `curl` use) it adds real wallclock time.
- **Rules drift.** The shipped `action-classification.yaml` is generic. Projects with their own dangerous commands (`make deploy-prod`, custom CLI tools) will need to add project-specific rules; until they do, those actions fall into the default class (`reversible_write`) and execute without judge review.
- **The judge cannot see future state.** It evaluates one action at a time against the current manifest. A sequence of individually-authorized actions that compose into an unauthorized outcome (e.g., creating three files that together expose a secret) is not caught by the judge - it is caught by the policy stage and the verifier.
- **Auto-escalation after 3 revision cycles is an upper bound, not a target.** If revision_cycles is consistently high across runs, that usually indicates a manifest clarity problem, not a judge problem.

## [0.3.0] - 2026-05-11

The dual-AI audit-handoff discipline. Built from the CivicCast `process/shared-audit-knowledge` PR (commit `bfc5a2a`) which formalized a pattern that had been proven across multiple sprints: an implementing AI runs a hostile 5-lens self-audit before push, a verifying AI runs a documented 10-section protocol after push, and both share an in-repo doc so neither re-derives the rules from scratch each session.

### Added

- `audit-init` workflow skill. Scaffolds the three-artifact dual-AI audit infrastructure for a project: out-of-repo `<PROJECT>_AUDIT_GATE.md` and `<PROJECT>_AUDIT_PROTOCOL.md`, in-repo `<project>/docs/process/5-lens-self-audit.md` (lands via PR), plus per-agent wiring (Codex project instructions feedback file on the Codex side, runtime-equivalent project-context file on the second AI's side).
- `pipelines/roles/cross-agent-auditor.md` - role file for the verifying agent. Mandatory 10-section output (Verdict / Claim Verification Matrix / Durable Artifact Reads / Substantive Content Checks / Drift Matrix / Working Tree & Remote State / Unreported Catches / Open Caveats / Paste-Ready Directive / Recommended Next Action). Status-word rules. Runtime confidence separation. Failure handling.
- `pipelines/roles/implementer-pre-push.md` - role file for the implementing agent. Five lenses (Engineering / UX / Tests / Docs / QA). Artifact-state checklist. Post-push SHA-propagation step. Proof-anchor vs release-target distinction. Report format with mandatory 5-lens block.
- `pipelines/templates/audit-gate-template.md` - short gate template with `<PROJECT_NAME>`, `<IMPLEMENTER_AGENT>`, `<AUDITOR_AGENT>`, `<AUDIT_PROTOCOL_PATH>` placeholders.
- `pipelines/templates/audit-protocol-template.md` - long protocol template with 22 sections; section 22 (Known Drift Patterns) is the project's catalog that accumulates over time.
- `pipelines/templates/5-lens-self-audit-template.md` - in-repo shared doc template with generic artifact-state checklist; project-specific items accumulate as the auditor surfaces new drift patterns.
- `docs/audit-handoff-handbook.md` - operator reference. When to use, how the two halves interact, role-agent matrix, stacking with the pipeline, honest expectations of what the discipline reduces vs. what it doesn't.

### Why each new piece exists

- **Dual-AI separation of duties.** A single AI auditing its own work catches less drift than two AIs with separate context. The implementer reads its own diff as the agent that produced it; the auditor reads cold against a documented protocol. Second-perspective catches what first-perspective missed - the same property that makes human code review work.
- **5-lens self-audit before push.** A chat-promise ("I'll keep this in mind") is not a behavior change. The behavior change is the durable artifact: the hostile self-audit on the actual diff, with results printed in the report. Forces the implementing agent to rebut its own diff before pushing.
- **10-section verification output.** Sparse audits ("looks good to me") generate no useful directives for the next implementing turn. The 10-section structure forces the auditor to produce a paste-ready directive every turn, even when cleanup is complete (then it's the next-phase directive).
- **In-repo shared doc.** Both agents read it. When the auditor finds drift, the auditor's directive references the relevant section. New drift patterns get added as artifact-state checklist items - the discipline strengthens over time.
- **Out-of-repo gate and protocol.** They govern the auditor's behavior BEFORE entering the repo. They can be updated without dragging a PR through project review (when standards tighten mid-sprint).

### Role-agent symmetry

The discipline is symmetric. Any AI can play either role; the plugin runs in Codex Desktop App, the second AI can be any tool that exposes a standing-instructions surface (project-context file, skill registration, custom-instruction field, etc.). `audit-init` asks for role assignment and wires the per-agent pointers accordingly. Single-agent fallback is supported but loses the structural benefit.

### Stacking with v0.2

- The pipeline (v0.2) catches execution-cascade failures: pre-existing CI infrastructure bugs, tag-move dances, halt-and-ask loops.
- The audit-handoff discipline (v0.3) catches drift failures: wrong endpoint, stale CHANGELOG, "Closed" without evidence, status-word abuse, durable docs drifting in parallel.

The two stack. Pipeline's Phase 1 is where the implementer's 5-lens fires. Pipeline's Phase 4 is where the auditor's 10-section output fires. Human gates remain unchanged.

### Known limitations

- The discipline does not prevent wrong-direction product decisions (audit verifies execution, not strategy).
- It does not prevent cascading CI infrastructure bugs (that's what the pipeline's Phase 0 is for).
- Single-agent runs collapse to self-audit-only - the structural benefit comes from independent context.
- The drift-pattern catalog (section 22 of the protocol) starts empty for new projects. The first few audit cycles will surface patterns that establish the project's specific drift profile.

## [0.2.0] - 2026-05-11

The `module-release` pipeline. Built from the CivicSuite civicrecords-ai v1.5.0 sprint that burned ~8 hours on cascading discovery of three pre-existing latent `release.yml` bugs. Validated end-to-end against the CivicSuite D2/B3 staff_key_gate sprint, which shipped CivicCore v1.1.0 with **zero tag moves** on the first push - the pipeline's design target.

### Added

- `pipelines/module-release.yaml` - 4-phase pipeline: Phase 0 preflight -> Phase 1 product -> Phase 2 local rehearsal -> Phase 3 remote release + umbrella -> Phase 4 verifier -> Phase 5 manager. Human gates at Phase 0 / Phase 2 / Phase 5.
- `pipelines/roles/preflight-auditor.md` - Phase 0 role. Audits the module's release workflow and supporting CI before any product code is touched. Check 1-7 sequence (YAML parse, workflow run health, scripts exist, local verify on fresh state, cross-platform reality, diagnostic instrumentation, audit-punchlist correlation). Bugs found are bundled into ONE PR.
- `pipelines/roles/local-rehearsal.md` - Phase 2 role. Mirrors the CI environment and runs the release sequence locally on fresh state before the tag push. The release workflow becomes the execution mechanism, not the discovery mechanism.
- `pipelines/self-classification-rules.md` - pre-authorized classifications applied during Phase 1: LIVE-STATE / FROZEN-EVIDENCE / SHAPE-GUARD / OWN-MODULE-VERSION for grep hits; MECHANICAL-CI-BUG / CONTRACT-CHANGE / ENVIRONMENTAL / NOVEL for failures. Bundling discipline and a tag-move budget (target 0, ceiling 1 per sprint).
- `scripts/preflight_infrastructure.py` - Phase 0 runner. Six automated checks; non-zero exit blocks Phase 1 work.
- `docs/module-release-handbook.md` - operator reference with honest timing expectations (`~8h -> ~2-3h` for infra-debt modules) and a "what this pipeline does NOT prevent" section (unknown unknowns, inter-module integration surprises, agent judgment errors).

### Why each new piece exists

- **Phase 0 prevents the cascade.** The civicrecords-ai sweep had three latent `release.yml` bugs that surfaced one at a time during Phase 3 (remote release). Each surface required a PR + merge + tag-move + 4-minute CI cycle. Phase 0 inverts this: find the bugs by reading workflow YAML, grepping referenced scripts, running `verify-release.sh` locally on fresh state, and cross-referencing the audit punchlist. Fix all of them in ONE bundled PR. Then product work begins.
- **Self-classification rules prevent halt-and-ask churn.** The civicrecords-ai chat had ~25% of its content as "agent halted, asked permission, human answered, agent continued" on routine cases (URL update, version-string update, frozen-doc skip, shape-guard skip). The rules pre-authorize the long tail; halt-and-ask is reserved for genuine novelty.
- **Phase 2 prevents the tag-move dance.** The civicrecords-ai v1.5.0 tag moved FOUR times during recovery. Phase 2 forces the agent to run the release sequence locally before pushing the tag; the workflow becomes the execution mechanism, not the discovery mechanism.

### Validation

End-to-end run against CivicSuite D2/B3 staff_key_gate sprint (2026-05-11):
- Phase 0 found one infrastructure bug, bundled fix shipped as CivicCore PR #55.
- Phase 1 product work shipped staff_key_gate helper as CivicCore PR #56.
- Phase 2 local rehearsal passed on fresh state; SHA captured matched final release.
- Phase 3 tag push: **zero tag moves**, release published first try.
- Six downstream module sweeps merged green; umbrella PR #123 merged through `release-lockstep-gate`.
- All 26 modules PASS on `verify-suite-state.py --remote-only`.

### Known limitations

- Designed for module-version-bump and dependency-migration sprints. Not a fit for pure feature work (use `feature.yaml`) or bug fixes that don't ship a release (use `bugfix.yaml`).
- The Phase 2 local rehearsal cannot fully simulate signed/notarized Windows installer builds without a local Windows VM, or macOS notarization without paid Apple credentials. Document the trust gaps in the rehearsal report.
- Pipeline timing wins are concentrated in modules with infrastructure debt. Low-debt modules see modest improvement (~30 min sprint stays ~30 min).

## [0.1.0-beta] - 2026-05-09

Initial public beta. The plugin has shipped real features in at least
one project (CivicCast Sprint 0.3); the slash-command edge cases will
surface in your codebase before they surface in the maintainer's.

### Added

- `pipeline-init` workflow skill with three onboarding paths:
  PRD/spec document, existing repo (URL or local path), or description
  paragraph. Scaffolds `.pipelines/`, `scripts/policy/`, `AGENTS.md`,
  and a `.gitignore` entry.
- `new-run` workflow skill. Initializes
  `.agent-runs/<run-id>/manifest.yaml` from the template.
- `run-pipeline` orchestrator workflow skill. Reads the pipeline YAML,
  walks stages in order, dispatches to one of three handlers
  (human-gate / pipeline-command / agent), writes append-only
  `run.log`, resumes from the right place on re-invocation.
- `feature` pipeline (8 stages: manifest -> research -> plan ->
  test-write -> execute -> policy -> verify -> manager).
- `bugfix` pipeline (7 stages: manifest -> research -> plan ->
  reproduce -> patch -> policy -> verify -> manager).
- Six role files: researcher, planner, test-writer, executor, verifier,
  manager. Each is the verbatim contract a fresh subagent receives.
- Three policy checks shipped:
  `check_allowed_paths.py`, `check_no_todos.py`,
  `check_adr_gate.py`, plus the `run_all.py` aggregator.
- `manifest-template.yaml` with inline field documentation: `id`,
  `type`, `branch`, `goal`, `allowed_paths`, `forbidden_paths`,
  `non_goals`, `expected_outputs`, `required_gates`, `risk`,
  `rollback_plan`, `definition_of_done`, `director_notes`.
- Documentation: `README.md`, `USER-MANUAL.md` (operator-facing),
  `ARCHITECTURE.md` (with Mermaid diagrams), `docs/index.html`
  (GitHub Pages landing page).

### Lessons baked into defaults

- **Halts apply to ALL repo state changes.** No "obviously safe"
  cleanup PRs while a gate is open.
- **The manager must cite verifier evidence verbatim.** The role file
  forbids encouragement and summarization - these were how bad runs
  promoted in prior projects.
- **Policy checks halt the pipeline on non-zero exit.** No "warning
  only" - that's how scope creep gets in.
- **The `run.log` is append-only.** Editing it to "fix" a stage hides
  the underlying bug. The orchestrator parses the log to determine
  resume point; resume is the only valid recovery.
- **Subagents have fresh context.** Each stage starts with the role
  file + on-disk artifacts. The orchestrator's conversation history is
  not shared.
- **Cleanroom CI is recommended in the orientation summary.** A
  Docker-based reproduction with a fresh dependency set catches
  "works on my machine" bugs that local pytest misses.

### Known limitations

- The orchestrator does not currently support nested pipelines (one
  pipeline invoking another). Out of scope for v0.1.
- The plugin does not enforce that you have committed your manifest
  before starting a run; you can if you want, but `.agent-runs/` is
  gitignored by default.
- The `bugfix` pipeline assumes the bug is reproducible; if it isn't,
  the `reproduce` stage will fail and you'll need to fall back to a
  `feature`-style flow.
- Policy checks are written in Python; if your project doesn't have
  Python available, the policy stage will fail. (Roadmap item: a
  shell-only fallback.)

### Roadmap (not committed - feedback wanted)

- v0.2: optional `cleanroom` stage that runs the test suite in a Docker
  container with a fresh dependency install.
- v0.2: project-specific check templates (e.g.,
  `check_no_console_log.py` for JS projects, `check_ffmpeg_wrapper.py`
  for media projects).
- v0.3: a `refactor` pipeline type for behavior-preserving changes
  (different verifier criteria - diff-mode tests).
- v0.3: a `--dry-run` flag on `run-pipeline` that walks the stage
  list and prints what would happen without spawning agents.

[0.3.0]: https://github.com/scottconverse/agent-pipeline-codex/releases/tag/v0.3.0
[0.2.0]: https://github.com/scottconverse/agent-pipeline-codex/releases/tag/v0.2.0
[0.1.0-beta]: https://github.com/scottconverse/agent-pipeline-codex/releases/tag/v0.1.0-beta
