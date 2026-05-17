# agent-pipeline-codex

[![CI](https://github.com/scottconverse/agent-pipeline-codex/actions/workflows/ci.yml/badge.svg)](https://github.com/scottconverse/agent-pipeline-codex/actions/workflows/ci.yml)

A Codex Desktop App plugin that orchestrates multi-stage agentic work: **manifest -> research -> plan -> test-write -> execute -> policy -> verify -> drift-detect -> critique -> auto-promote -> manager**, with human-approval gates at manifest, plan, and manager-decision (the last auto-fires on clean runs at v0.5+). Built from real lessons across CivicCast, CivicSuite, AgentSuiteLocal and other projects where autonomous agent runs go wrong silently and "manager-PROMOTE" failures slip past CI.

**Current release: v0.8.0** (plain-English intake drafting before manifest validation). [CHANGELOG](CHANGELOG.md) | [User Manual](USER-MANUAL.md) | [Architecture](ARCHITECTURE.md) | [Landing page](https://scottconverse.github.io/agent-pipeline-codex/) | [Discussions](https://github.com/scottconverse/agent-pipeline-codex/discussions)

## Why this plugin exists

Agentic work fails in predictable ways:

- The agent doesn't understand the project's conventions, so it improvises and the work silently diverges from the spec.
- The agent claims tests pass without running them against a fresh dependency set.
- The agent merges in-flight work while a scope question is open.
- The agent picks architectural decisions silently rather than surfacing them.

This plugin enforces a structural pattern that catches every one of those:

1. **Manifest + scope-lock gate** - every run starts with an explicit, human-approved manifest plus a scope lock naming the canonical release-plan rung, proof statement, allowed terms, and forbidden future-rung terms.
2. **Director-decisions gate** - the researcher surfaces open questions; the human picks; choices are recorded as binding constraints before the planner runs.
3. **Plan gate** - the planner produces a plan; the human approves or sends back.
4. **Execute readiness gate** - before the runner may advance from execute to policy/verify, `implementation-report.md` must prove the full manifest Definition of Done is ready, not merely that a backend or test slice passed. The report needs a machine-readable `**DoD readiness: READY**` line and a zero-blocker DoD checklist covering expected outputs, DoD clauses, project UX/docs/testing gates, and prior blockers.
5. **Policy stage** - automated checks block the run if the manifest fails strict schema validation (v0.5), the scope lock disagrees with the canonical release plan (v0.5.9), execute readiness is missing or blocked, any change falls outside `allowed_paths`, edited paths or commit messages belong to another rung, docs contradict the locked rung, the diff contains TODO/FIXME/HACK markers, or an existing ADR was modified.
6. **Verifier stage** - independent fresh-context check against every manifest exit criterion.
7. **Manager gate** - final PROMOTE/BLOCK/REPLAN decision, must cite verifier evidence verbatim.

8. **Control-loop gate** - before any final response, stop, deferral, or skipped action during an authorized run, `.agent-runs/<run-id>/active-control-state.md` must record a valid stop condition, `scripts/policy/check_pipeline_control_loop.py --run <run-id>` must pass, `scripts/policy/final_response_gate.py --require-active-run` must print `final_response_gate: ALLOW`, and `scripts/policy/agent_decision_gate.py` must allow the specific decision through the shared `stop_validator.py`. Green CI, successful push, draft PR status, stale state, unverified blocker risk, and a recommended next action are not stop conditions.

## Install

Install through the Codex Desktop App plugin flow once the repository is published, or clone it locally and add the local path to your Codex plugin configuration:

```bash
git clone https://github.com/scottconverse/agent-pipeline-codex.git ~/agent-pipeline-codex-plugin
```

Before calling the plugin installed, run the release verifier and prove the
Codex runtime can see it:

```bash
python scripts/verify_plugin_release.py --live
```

That gate must print `PLUGIN-RELEASE-VERIFY: PASSED`, including the nested
`PLUGIN-INSTALL-ACCEPTANCE: PASSED` live check. Repository tests, standalone
skill copies, and docs deployment are not install proof.

The live gate first verifies deterministic source and installed-cache state,
then runs repeated fresh Codex probes. One transient model enumeration miss is
preserved in the transcript but does not fail the release if another fresh
probe sees the complete namespaced plugin surface and no plugin-specific loader
warning appears.

Fresh-session prompts must verify the namespaced plugin skills, not only the
standalone skill names. The expected names are:

- `agent-pipeline-codex:agent-pipeline`
- `agent-pipeline-codex:intake`
- `agent-pipeline-codex:pipeline-init`
- `agent-pipeline-codex:new-run`
- `agent-pipeline-codex:run-pipeline`
- `agent-pipeline-codex:audit-init`
- `agent-pipeline-codex:show-run-status`
- `agent-pipeline-codex:validate-manifest`

If a session only sees `agent-pipeline`, `pipeline-init`, or `run-pipeline`
without the `agent-pipeline-codex:` prefix, it may be seeing stale standalone
skills under `$CODEX_HOME/skills`; that is not proof the current plugin is
active.

For headless CI that cannot see the local Codex Desktop registry, use the
source-only gate:

```bash
python scripts/verify_plugin_release.py --source-only
```

## First use in a new project

Drop into the project root (or a fresh empty directory) and ask Codex to use the `pipeline-init` skill:

```
Use pipeline-init for this project.
```

The plugin asks one question - what do you have? - and accepts one of three inputs:

1. **A PRD or spec document.** Paste the path or contents. The plugin reads it, derives the project's conventions, scaffolds `AGENTS.md` + `.pipelines/` + `scripts/policy/` + a `.gitignore` entry, and produces a project-orientation summary.
2. **A repo URL** (or a local path to an existing repo). The plugin clones (or reads), inspects `README`, `AGENTS.md`, `pyproject.toml` / `package.json`, `.github/workflows/`, `docs/adr/`, and recent commits. Produces a project-orientation summary, flags missing pieces, installs `.pipelines/` + `scripts/policy/`.
3. **A project description paragraph or two.** Plugin reads it, asks "scaffold a new project from this, or use as context for an existing repo?" and routes to (1) or (2) accordingly.

After init, your project has:

```
.pipelines/
|-- feature.yaml                    # stage sequence for new functionality
|-- bugfix.yaml                     # stage sequence for bug fixes
|-- module-release.yaml             # six-phase release pipeline (v0.2+)
|-- manifest-template.yaml          # blank template with field docs
|-- scope-lock-template.yaml        # blank canonical rung/scope lock
|-- directive-template.yaml         # optional v0.6 directive contract template
|-- action-classification.yaml      # opt-in: enables the v0.4 judge layer
|-- self-classification-rules.md    # pre-authorized cases the executor handles solo
`-- roles/
    |-- researcher.md
    |-- planner.md
    |-- test-writer.md
    |-- executor.md                 # has the v0.5 pre-edit fact-forcing gate
    |-- verifier.md                 # emits v0.5 parseable criteria count line
    |-- drift-detector.md           # v0.5 - manifest contract vs assembled state
    |-- critic.md                   # v0.5 - adversarial cold read, six lenses
    |-- manager.md                  # v0.5 auto-promote-aware
    |-- judge.md                    # v0.4 - used only when judge layer is opt-in
    |-- preflight-auditor.md        # v0.2 module-release Phase 0
    |-- local-rehearsal.md          # v0.2 module-release Phase 2
    |-- cross-agent-auditor.md      # v0.3 audit-handoff
    `-- implementer-pre-push.md     # v0.3 audit-handoff
scripts/policy/
|-- check_manifest_schema.py        # v0.5 - strict manifest contract validator
|-- check_scope_lock.py             # v0.5.9 - canonical rung lock validator
|-- check_directive_conformance.py  # v0.6 - manifest/scope directive conformance
|-- check_plan_against_directive.py # v0.6 - plan assertion auto-approval gate
|-- check_allowed_paths.py          # generic, manifest-driven
|-- check_rung_file_ownership.py    # v0.5.9 - future-rung path/commit blocker
|-- check_release_docs_consistency.py # v0.5.9 - docs vs release-plan consistency
|-- final_response_gate.py          # pre-final continuation gate
|-- agent_decision_gate.py          # stop/skip/defer decision gate + ledger
|-- pipeline_continue.py            # executable next-action navigator
|-- stop_validator.py               # v0.5.10 - shared stop-condition truth validator
|-- check_decision_ledger.py        # schema validator for decision-ledger.ndjson
|-- show_run_status.py              # read-only run state summary
|-- check_no_todos.py               # generic, configurable scan dirs
|-- check_adr_gate.py               # generic, ADRs are append-only
|-- auto_promote.py                 # v0.5 - six-condition machine-checkable promote
`-- run_all.py                      # runner
.agent-runs/                        # gitignored - pipeline run artifacts
hooks/                               # plugin-bundled v0.7 lifecycle hooks
```

## v0.8.0: Intake drafting

If you know the work in plain English but do not have a manifest yet, start
with the separate intake skill:

```
Use intake for Add account deletion to settings, including tests, docs, and a clear rollback path.
```

`intake` creates draft run artifacts and stops. It does not validate the
manifest, approve scope, run agents, or start implementation. It writes:

- `intake.md` - the verbatim source description plus conservative interpretation
- `manifest.yaml` - a draft manifest with uncertain scope left as TODOs
- `scope-lock.yaml` - a draft scope lock that refuses to invent release-plan authority
- `intake-questions.md` - missing answers that must be resolved before validation

The hard boundary is unchanged: draft intake is not approval. The next step is
to complete the TODOs and run `agent-pipeline-codex:validate-manifest`; only
then should `agent-pipeline-codex:run-pipeline` start.

## Running a pipeline

Once a project is initialized:

```
Use intake for Add account deletion to settings with tests and docs.
                                           # draft intake.md + manifest/scope-lock
Use new-run for feature my-task-slug.      # initialize blank manifest + scope-lock skeletons
                                           # (you fill in both, then:)
Use validate-manifest for 2026-05-09-my-task-slug.
                                           # fix schema issues before agent work starts
Use run-pipeline for feature 2026-05-09-my-task-slug.
                                           # orchestrates the full sequence,
                                           # stops at human gates and on failure,
                                           # resumable from .agent-runs/<run-id>/run.log
Use show-run-status for 2026-05-09-my-task-slug.
                                           # read-only status when you need orientation
```

Three human-approval gates per run: manifest, plan, manager-decision. Each is a one-question prompt: APPROVE or describe what should change.

Before starting a run, validate the manifest and scope lock with the same
checks used by the policy stage:

```bash
python scripts/policy/validate_manifest.py --run 2026-05-09-my-task-slug
python scripts/policy/check_scope_lock.py --run 2026-05-09-my-task-slug
```

The validators report exact violations and the fix path before the pipeline
spends agent time on a fuzzy manifest or the wrong canonical rung.

## v0.2: The `module-release` pipeline

For work whose end-state is a published release artifact (module version bump, dependency migration), use `module-release` instead of `feature`. It adds two stages that prevent the most expensive class of failure: cascading discovery of pre-existing CI infrastructure bugs during the remote release run.

```
Use new-run for module-release my-module-v1.2.0-migration.
Use run-pipeline for module-release 2026-05-11-my-module-v1.2.0-migration.
```

The pipeline runs six phases:
- **Phase 0 - Preflight auditor.** Audits the module's release workflow before any product code is touched. YAML parse, workflow run health, referenced scripts exist, local `verify-release.sh` on fresh state, cross-platform reality check, diagnostic instrumentation, audit-punchlist correlation. Bugs found are bundled into ONE PR. See `pipelines/roles/preflight-auditor.md`.
- **Phase 1 - Scoped product work.** The executor role with pre-authorized self-classification rules (LIVE-STATE / FROZEN-EVIDENCE / SHAPE-GUARD / OWN-MODULE-VERSION for grep hits; MECHANICAL-CI-BUG / CONTRACT-CHANGE / ENVIRONMENTAL / NOVEL for failures) so the agent doesn't halt-and-ask on routine cases. See `pipelines/self-classification-rules.md`.
- **Phase 2 - Local release rehearsal.** Mirrors the CI environment and runs the release sequence locally on fresh state before tag push. The workflow becomes the *execution* mechanism, not the *discovery* mechanism. See `pipelines/roles/local-rehearsal.md`.
- **Phase 3 - Remote release + umbrella reconciliation.** Tag push, release workflow watch, umbrella PR through the project's release-lockstep gate.
- **Phase 4 - Verifier.** Independent fresh-context check of all release artifacts and durable docs.
- **Phase 5 - Manager.** Final PROMOTE/BLOCK/REPLAN with verifier evidence cited verbatim.

Human gates at Phase 0 results review, Phase 2 rehearsal-ok, and Phase 5 release-ok.

**Operator reference:** `docs/module-release-handbook.md` covers initial setup, expected timing per sprint type, and an honest "what this pipeline does NOT prevent" section. Originating failure receipts are documented in the handbook so future operators understand why each stage exists.

## v0.3: Dual-AI audit-handoff discipline

For projects where one AI implements and a second AI audits, v0.3 adds a complementary discipline that catches drift the pipeline doesn't:

```
Use audit-init for this project.
```

This scaffolds three artifacts:
1. `<PROJECT>_AUDIT_GATE.md` (out-of-repo) - short mandatory gate the auditing agent reads every verification turn.
2. `<PROJECT>_AUDIT_PROTOCOL.md` (out-of-repo) - long reference protocol with the 10-section output shape, status-word rules, and a known drift patterns catalog.
3. `<project>/docs/process/5-lens-self-audit.md` (in-repo, via PR) - shared discipline both agents read. The implementer runs a hostile 5-lens self-audit before every push (Engineering / UX / Tests / Docs / QA), plus a post-push SHA-propagation step.

Plus per-agent wiring (Codex project instructions feedback file on the Codex side; the equivalent project-context or skill-registration mechanism on the other AI's side) so each agent reads the right artifact on session start.

The discipline is symmetric - any AI can play either role. The plugin runs in Codex Desktop App; the second AI can be any tool that exposes a project-context or standing-instructions surface.

**Stacking with v0.2:**
- Pipeline (v0.2) catches execution-cascade failures: pre-existing CI bugs, tag-move dances, halt-and-ask loops.
- Audit-handoff (v0.3) catches drift failures: wrong endpoint, stale CHANGELOG, "Closed" without evidence, status-word abuse.

The two address different failure modes. Use both for projects with two AI systems.

**Operator reference:** `docs/audit-handoff-handbook.md`.

## v0.4: Judge layer

Real-time action-level supervision **inside** the executor stage. This is not a new pipeline stage; it is opt-in infrastructure that intercepts the executor's tool calls, classifies each one by risk, and spawns a judge subagent for the dangerous ones. Built from the Lindy case study (May 2026, Nate Jones, "LLM-as-Judge"): an agent that sent 14 unauthorized emails because manual confirmation prompts had trained the operator to click "okay" reflexively. Prompts don't hold across long context; the architectural fix is a second agent whose sole loyalty is the manifest.

```
# Opt in by creating .pipelines/action-classification.yaml in your project.
# The orchestrator detects the file at run start and uses Handler 3a
# (classify -> judge -> execute) instead of Handler 3 for the executor stage.
# No other commands change.
```

### What it does

Every tool call the executor proposes is classified against `.pipelines/action-classification.yaml` and routed by risk class:

- `read_only` (e.g. `cat`, `grep`, `git log`) -> execute + log.
- `reversible_write` (e.g. `str_replace_editor`, `git commit`, `cp`) -> execute + log.
- `external_facing` (e.g. `git push` to non-main, `gh pr create`, `curl -X POST`) -> STOP, spawn judge.
- `high_risk` (e.g. `rm -rf`, `git push --force`, `git push main`, `DROP TABLE`, `npm publish`) -> STOP, spawn judge, and require human confirm even after the judge ALLOWs.

### The four verdicts

The judge subagent receives the manifest, the matched action policy, prior judge decisions for this run, and the structured action proposal - but **not** the executor's internal reasoning chain. Context isolation is the mechanism: the judge cannot be persuaded by the same chain of inferences that produced the over-broad action.

- **`allow`** - within scope, evidence supports the justification. Proceed.
- **`block`** - outside scope, violates policy, or unsupported by evidence. Halt.
- **`revise`** - legitimate basis, wrong form. Send concrete revision instruction back to the executor (e.g. "push to feature branch, not main"). Max 3 revision cycles per action; auto-escalate after.
- **`escalate`** - requires human judgment (money, credentials, legal, or judge confidence < 0.7). Pipeline pauses for a specific human question.

### Two new artifacts per run (when judge layer is active)

- **`judge-log.yaml`** - chronological log of every action: tool, arguments, class, disposition (auto_allow / judged_allow / judged_revise / judged_block / judged_escalate / human_confirmed / human_blocked), judge reason, revision instruction. Verifier and manager read this.
- **`judge-metrics.yaml`** - counts by class and disposition, `escalation_rate`, `judge_invocations`, `revision_cycles`. The escalation rate is the operator's tuning signal - too low means rules too permissive, too high means trust is being eroded by reflexive APPROVE clicking.

### Opt-in by file presence

If `.pipelines/action-classification.yaml` does not exist in your project, the executor stage runs exactly as in v0.3 and earlier - no judge, no `judge-log.yaml`, no behavioral change. The presence of the file at run start opts that run into the judge layer. Operators choose whether to enable it per-project (or per-branch, since it's a file in the repo).

**Stacking with v0.2 and v0.3:**

- Pipeline (v0.2) catches execution-cascade failures - pre-existing CI bugs, tag-move dances, halt-and-ask loops.
- Audit-handoff (v0.3) catches drift failures - wrong endpoint, stale CHANGELOG, status-word abuse.
- **Judge layer (v0.4) catches unauthorized actions in real time** - destructive commands, external writes, force pushes, and credential-touching operations evaluated against the manifest at the action boundary instead of after the fact.

**Operator reference:** USER-MANUAL.md Section "The judge layer (v0.4)".

## v0.7.0: Hooked pipeline autonomy

v0.7.0 adds optional Codex lifecycle hooks. When Codex is configured with
`[features].plugin_hooks = true`, the plugin can add active-run context at
session start, warn on stale standalone skill names, preflight risky tool
calls, deny clearly unsafe approval requests, add corrective context after
failed tools, and continue instead of stopping when `active-control-state.md`
says the run is not at a valid stop condition.

Hooks do not replace the directive contract, judge layer, policy scripts, or
human fallback gates. They move existing pipeline discipline closer to Codex's
runtime lifecycle. The default mode is warn/context; hard blocks are limited to
concrete safety violations such as destructive commands, force pushes, secret
exposure, out-of-scope active-run writes, and invalid pipeline stops.

Local hooks work with a normal signed-in Codex session. Codex access tokens are
documented only for ChatGPT Business and Enterprise workspaces, so they are
optional for CI automation and not required for local Max/Pro-style operation.

## v0.5: Single-AI hardened

Six structural changes that make the pipeline run with **one AI** while still blocking drift and rogue-agent failures. Built from the design question: "can the pipeline do both action-level judge AND post-hoc audit with one AI?" Answer is yes - at the cost of accepting some correlated single-model-family blind spots, with explicit mitigations.

### What changed

- **Critic stage** (`pipelines/roles/critic.md`) - adversarial cold read of every artifact in a fresh context. Walks six lenses (engineering, UX, tests, docs, QA, scope). Emits a parseable `**Findings:**` count line. Structural substitute for cross-family verification.
- **Drift-detector stage** (`pipelines/roles/drift-detector.md`) - compares manifest contract against assembled final state. Catches durable doc drift, status-word abuse, cross-file inconsistency, ledger top-totals vs row counts. Emits parseable `**Drift:**` count line.
- **Pre-edit fact-forcing in executor** - before the first edit per file, the executor must produce importers/callers, public API affected, schema, and the manifest goal quoted verbatim. Forces investigation that catches blast-radius surprises before they hit the verifier.
- **Expanded judge classification** - five new `high_risk` patterns: `npm install -g`, `sudo`, non-editable non-user `pip install`, `git commit` with BREAKING in message.
- **Machine-checkable auto-promote** (`scripts/auto_promote.py`) - six conditions checked from the artifact stack: verifier-clean, critic-clean, drift-clean, policy-passed, judge-clean, tests-passed. When all six pass, the manager gate auto-fires; when any fails, the human gate remains.
- **Strict manifest schema validation** (`scripts/check_manifest_schema.py`) - minimum-length `goal` and `definition_of_done`, non-empty `expected_outputs` / `non_goals` / `rollback_plan`, forbidden status words banned from manifest contracts, broad `allowed_paths` requires non-empty `forbidden_paths`. Fuzzy manifests fail at the start of the run, not after they cascade.

### How the pipeline shape changes

Pre-v0.5: `manifest -> research -> plan -> test-write -> execute -> policy -> verify -> manager`

v0.5: `manifest -> research -> plan -> test-write -> execute -> policy -> verify -> drift-detect -> critique -> auto-promote -> manager`

The new three stages add ~10-20 minutes of wall-clock per run depending on artifact size. The auto-promote stage typically lands the manager decision in <30 seconds when the six conditions are green, eliminating the third human gate on clean runs.

### Honest limit

Single-model-family blind spots correlate. If both the executor and the critic share a wrong assumption that fits the manifest, both sign off and auto-promote fires green. Dual-AI (v0.3) is the only structural defense against this. **Recommended mitigation:** periodic sample audit by a different model family on a weekly cadence. The v0.3 `audit-init` discipline still applies; v0.5 does not replace it.

### Stacking with v0.2, v0.3, v0.4

- v0.2 catches execution-cascade failures (pre-executor).
- v0.3 catches drift failures via cross-family audit (post-executor, separate session).
- v0.4 catches unauthorized actions in real time (during executor).
- **v0.5 catches the drift class without needing a second AI** (during verify -> drift-detect -> critique -> auto-promote).

The four stack. Most projects run v0.4 + v0.5 by default and reach for v0.3 when they have two model families available.

**Operator reference:** USER-MANUAL.md Section "v0.5 single-AI hardening" + ARCHITECTURE.md Section 8 "Single-AI hardening (v0.5)".

## v0.6.0: Directive contracts

v0.6.0 closes the directive-conformant re-approval loop. Operators can add
`.agent-runs/<run-id>/directive.yaml` before a run to pre-declare the exact
manifest, exact scope lock, plan acceptance assertions, and manager acceptance
assertions. The runner binds the directive hash into `run.log`, auto-approves
the manifest and plan gates only when on-disk artifacts mechanically conform,
and extends auto-promote from six conditions to six plus the directive's
manager assertions.

Manual fallback is preserved: absent directives, malformed directives,
mismatches, failed assertions, and hash tampering keep or restore the existing
interactive gate. Judge-layer high-risk confirmations and `escalate` prompts
remain human surfaces because a directive cannot know future tool calls.

## v0.5.10: Evidence-bound stop validation

v0.5.10 closes the stale-control-state escape hatch by centralizing stop
truth in `stop_validator.py`. `final_response_gate.py`,
`pipeline_continue.py`, and `agent_decision_gate.py` now call the same validator
instead of each trusting `active-control-state.md` independently. Human gates
are valid only at manifest, plan, or manager stages; failed-gate stops must be
backed by current `run.log` evidence when a log exists; stale scope-repair
states cannot authorize stopping after a passing `scope-lock-receipt.txt`; and
unrecorded blocker claims require an evidence file, not just plausible text.

## v0.5.9: Canonical rung authority

v0.5.9 adds the missing guard between "the agent is authorized to continue"
and "the agent is working on the right thing." A run now carries
`.agent-runs/<run-id>/scope-lock.yaml`, which binds the work to a specific
section of the canonical release plan. The policy stage blocks missing locks,
release-plan mismatches, future-rung paths, contradictory docs, and commit
subjects that belong to another rung.

Before starting rung work from a prompt, the orchestrator runs:

```bash
python scripts/policy/agent_decision_gate.py --run <run-id> --intent start_rung_work --claimed-rung <rung> --prompt-text "<user wording>"
```

If the user says "Begin v0.6 publish-dashboard work" while the release plan
says v0.6 is "Summary + signed records," the gate returns `SCOPE_CONFLICT`.
The agent stops before edits and requires an explicit scope amendment. It may
not infer that the release ladder changed.

## What this plugin will NOT do

- It will not propose broad autonomous mode. Hooks add guardrails around explicit pipeline authority; every gate remains explicit or mechanically directive-bound.
- It will not silently expand scope. The policy stage blocks any change outside `allowed_paths`.
- It will not silently change rungs. The scope-lock gates block prompt, path, docs, and commit-message conflicts with the canonical release plan.
- It will not skip tests. AGENTS.md hard-rule "never skip tests" is enforced as a project default.
- It will not promote a run if the verifier marked any criterion NOT MET. Manager hard rule.

## Project-specific customization

After `pipeline-init`, the files installed in your repo are yours to edit. Add project-specific policy checks alongside the generic ones (e.g., a CivicCast-style `check_ffmpeg_wrapper.py`). Customize the role files to reference your project's specific ADRs, AGENTS.md sections, test patterns. The plugin's workflow skills work against whatever's in your repo's `.pipelines/` and `scripts/policy/` directories.

## Documentation

- `skills/*/SKILL.md` - Codex skill entrypoints for onboarding, new-run, validation, run-pipeline, status, and audit-init
- `commands/pipeline-init.md` - the full onboarding workflow logic
- `commands/new-run.md` - the run-init workflow logic
- `commands/validate-manifest.md` - manifest schema preflight
- `commands/run-pipeline.md` - the orchestrator workflow logic (includes v0.4 Handler 3a judge interception and v0.5 Handler 4 auto-promote-aware manager)
- `commands/show-run-status.md` - read-only run status workflow
- `commands/audit-init.md` - scaffolds the v0.3 dual-AI audit-handoff infrastructure
- `pipelines/roles/*.md` - what each role does, what's forbidden
- `pipelines/manifest-template.yaml` - every manifest field with inline docs
- `pipelines/scope-lock-template.yaml` - canonical rung/scope lock template
- `scripts/auto_promote.py` - v0.5 six-condition promote-eligibility checker (`--version` to confirm release)
- `scripts/check_manifest_schema.py` - v0.5 manifest validator (`--version` to confirm release)
- `scripts/check_scope_lock.py` - canonical release-plan rung validator
- `scripts/check_rung_file_ownership.py` - future-rung path and commit-subject blocker
- `scripts/check_release_docs_consistency.py` - docs vs locked rung consistency gate
- `scripts/validate_manifest.py` - standalone manifest preflight wrapper for source and scaffolded projects
- `scripts/check_decision_ledger.py` - schema-v1 decision-ledger validator
- `scripts/show_run_status.py` - read-only status summary over run.log and active-control-state
- `.pipelines/templates/workflow-cost-directives.md` - canonical GitHub Actions cost-discipline contract
- `USER-MANUAL.md` - end-to-end operator reference, every command + gate + troubleshooting case
- `ARCHITECTURE.md` - diagrams, file layout, artifact data flow, extension points
- `CHANGELOG.md` - every release with rationale, what changed, what didn't

## Lessons baked in

This plugin's defaults reflect failures from prior projects. Notably:

- Halts apply to ALL repo state changes, including in-flight cleanup work
- Auto mode never overrides explicit stops
- "Tests pass locally" is not evidence; CI on a fresh dep set is
- Manifest amendments are corrections, not expansions, and the pattern of needing them means the manifest template should use directory-level path granularity for same-module test paths
- The manager must cite verifier evidence verbatim; encouragement and summarization are forbidden in the role file

## License

Apache 2.0.
