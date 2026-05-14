---
description: Orchestrate an agentic pipeline run end-to-end (resumable). Stops at human gates and on failure.
argument-hint: <pipeline-type> <run-id>
---

# run-pipeline - orchestrate a pipeline run

You are the orchestrator of an agentic pipeline. The pipeline definition lives in `.pipelines/<pipeline-type>.yaml`. The run state lives in `.agent-runs/<run-id>/`. You execute every stage in order, write progress to `run.log`, and stop only at a valid stop condition. During an authorized pipeline run, the agent may not end a turn, defer, skip push, skip CI, write a stopping handoff, compact-and-stop, or ask a non-gate question unless `.agent-runs/<run-id>/active-control-state.md` records a valid stop condition, `python scripts/policy/check_pipeline_control_loop.py --run <run-id>` passes, `python scripts/policy/final_response_gate.py --require-active-run` prints `final_response_gate: ALLOW`, and `python scripts/policy/agent_decision_gate.py --intent <intent> --claimed-stop-condition <condition> --write-ledger` allows that specific decision.

Before advancing from execute to policy/verify, enforce the DoD readiness
gate: `implementation-report.md` must contain `**DoD readiness: READY**` and a
parseable `**DoD checklist: T total, R ready, B blocked, D deferred**` line
with zero blocked items. If `scripts/policy/check_execute_readiness.py` exists,
it must pass; if it is absent in an older project, enforce the same parse
manually and update the project plumbing before promotion. If readiness fails,
continue implementation inside the authorized executor scope instead of
advancing a partial slice to full-rung gates.

You do NOT do the work of any stage yourself. You delegate every agent stage to a subagent via the Codex `spawn_agent` tool, run policy stages via the shell tool, and ask the user via `a structured user question` at human gates. Your job is the loop and the logging.

## Arguments

`$ARGUMENTS` contains two whitespace-separated tokens:

- **`<pipeline-type>`** - must match a YAML in `.pipelines/`.
- **`<run-id>`** - the directory name under `.agent-runs/` (typically `YYYY-MM-DD-<slug>`).

If `$ARGUMENTS` does not contain exactly two tokens, stop and report usage: `run-pipeline <pipeline-type> <run-id>`.

---

## Phase A - Setup

### A1. Read the pipeline definition

Read `.pipelines/<pipeline-type>.yaml`. Parse the stages list in document order. Each stage has these fields:

- `name` - string, e.g. `manifest`, `research`, `policy` (or `id` in `module-release.yaml`'s richer schema)
- `role` - one of `human`, `pipeline`, `researcher`, `planner`, `test-writer`, `executor`, `verifier`, `drift-detector`, `critic`, `manager`
- `artifact` - filename written under `.agent-runs/<run-id>/`
- `gate` (optional) - `human_approval` if a human must sign off after the stage produces its artifact
- `command` (optional) - only on `role: pipeline` stages; the shell command to execute
- `optional_artifact` (optional, v0.5) - if `true`, the absence of the named artifact does NOT fail the stage. Used by the `auto-promote` stage: it writes `auto-promote-report.md` only when NOT_ELIGIBLE; when ELIGIBLE, it writes `manager-decision.md` instead, and the named artifact may be absent.
- `auto_promote_aware` (optional, v0.5) - if `true`, the runner checks for an auto-promote preset before spawning this stage's agent. When `.agent-runs/<run-id>/manager-decision.md` exists with `**Decision: PROMOTE**` as its literal first line, the human-approval gate is satisfied automatically and the manager subagent is invoked only to validate-and-append, not to re-decide.

If the YAML is missing or unparseable, stop and report.

### A2. Read and validate the manifest

Read `.agent-runs/<run-id>/manifest.yaml`. If it does not exist, stop and tell the user to run `new-run <pipeline-type> <slug>` first.

Inspect the manifest text. The `goal:` line must contain a non-empty quoted string. If it is `goal: ""`, stop and tell the user to fill in the manifest before starting the pipeline.

**v0.5 strict schema validation:** before any stage runs, invoke `python scripts/policy/check_manifest_schema.py --run <run-id>` via the shell tool. If it exits non-zero, append `<TS> | manifest-schema | FAILED | see stdout` to `run.log`, display the violation output to the user, and STOP the pipeline. This catches fuzzy manifests at the start of the run rather than letting them cascade through researcher/planner/executor before the policy stage discovers them.

### A2.5. Read and validate the scope lock

Read `.agent-runs/<run-id>/scope-lock.yaml`. If it does not exist, stop before product work starts and tell the user to fill it in from `.pipelines/scope-lock-template.yaml`.

Invoke `python scripts/policy/check_scope_lock.py --run <run-id>` via the shell tool. If it exits non-zero, append `<TS> | scope-lock | FAILED | see stdout` to `run.log`, display the violation output to the user, and STOP the pipeline with `scope_conflict`.

Before interpreting user wording as authorization to start or redirect rung work, invoke:

```bash
python scripts/policy/agent_decision_gate.py --run <run-id> --intent start_rung_work --claimed-rung <current-rung> --prompt-text "<user wording>"
```

If it prints `agent_decision_gate: BLOCK`, do not edit. The user wording conflicts with the canonical release plan. Stop with `scope_conflict` and require an explicit scope amendment. The agent may not infer that the release ladder changed.

### A3. Read the run log (resume state)

Read `.agent-runs/<run-id>/run.log` if it exists. The log format is one event per line:

```
TIMESTAMP | STAGE_NAME | STATUS | NOTE
```

Where `STATUS` is one of `COMPLETE`, `FAILED`, `BLOCKED`. Parse the lines into a list of completed stages (`COMPLETE` only - `FAILED` and `BLOCKED` mean the stage is still incomplete and must re-run).

If `run.log` does not exist, treat the completed-stages list as empty.

### A4. Determine the resume point

Walk the stage list from the YAML in order. The first stage whose `name` is NOT in the completed set is where you resume.

If every stage is complete, jump to **Phase C - Wrap-up**.

### A5. Report the plan to the user

Print to the user (no tool call needed - just plain text):

- The pipeline name (`<pipeline-type>`)
- The run id
- Total stage count and their names in order
- Which stages are already complete (from the log)
- Which stage is starting now
- A note that the run will stop at any valid stop condition, and can be resumed by re-invoking `run-pipeline <pipeline-type> <run-id>` with the same arguments
- A note that successful push, green CI, PR draft status, open caveats, and a recommended next action are not stop conditions
- A note that an unverified blocker or risk is not a stop condition; claimed blockers must be verified before they can stop, defer, or skip an action
- A note that workflow-cost discipline is part of slice completeness when the slice changes `.github/workflows/*.yml` or `.github/workflows/*.yaml`

### A6. Workflow-cost discipline

The pipeline treats GitHub Actions cost discipline as mandatory policy, not advisory guidance.

If the slice adds or modifies `.github/workflows/*.yml` or `.github/workflows/*.yaml`, the run must:

1. Name the workflow files in `plan.md` before editing.
2. Apply the 10 workflow-cost directives below.
3. Run `python scripts/policy/run_all.py --run <run-id>` so `check_actions_budget` validates the mechanically checkable rules.
4. Record workflow-cost evidence in `.agent-runs/<run-id>/implementation-report.md` and `.agent-runs/<run-id>/verifier-report.md`.
5. Treat unresolved workflow-cost violations as release risks that block slice completion.

The 10 workflow-cost directives are:

1. Never add a daily cron without explicit Scott approval. Weekly is the maximum default schedule. Daily is allowed only for a specific justified need, such as security scanning or dependency drift, and the run record must prove weekly is insufficient before daily is used.
2. Every new GitHub Actions workflow must include this concurrency block, except release or tag workflows where cancellation would corrupt the release:

   ```yaml
   concurrency:
     group: ${{ github.workflow }}-${{ github.ref }}
     cancel-in-progress: true
   ```

3. Do not duplicate `push: branches: [main]` and `pull_request: branches: [main]` for the same validation workflow. Use `pull_request:` by default. Use `push: branches: [main]` only for workflows that must run on direct main pushes, such as deployments.
4. Batch work-in-progress commits before pushing. Before pushing a slice branch, squash local work-in-progress commits when doing so preserves the useful history. Avoid pushing many small commits that each trigger full CI.
5. Add `paths:` filters when adding any heavy workflow, especially workflows that install TeX, build Docker images, run Playwright, install browsers, run large language models, or perform cleanroom/e2e validation. Documentation-only changes must not trigger heavyweight CI unless the workflow validates documentation.
6. macOS jobs are allowed on release tags only. Do not add `runs-on: macos-latest` to PR-fired jobs unless Scott explicitly approves the exception.
7. Windows jobs are allowed on PR only when truly necessary. Windows runners cost more than Linux runners. New workflows must justify Windows use in the run record or policy check evidence.
8. Python version matrices are allowed on tags or weekly cron. PR CI must test one production Python version by default, currently Python 3.12, unless Scott explicitly approves broader PR matrix coverage.
9. Cache anything that takes more than 30 seconds to install. This includes apt packages, Playwright browsers, Ollama models, Docker layers, npm caches, pip caches, and other large dependency downloads. Use first-party cache support from setup actions when available.
10. Every `upload-artifact` step must set `retention-days: 7` unless the artifact is a release artifact or Scott explicitly approves longer retention.

---

## Phase B - Stage execution loop

For each stage starting at the resume point, in order, execute the appropriate handler below. After the handler completes, write a log line and proceed to the next stage. If any handler returns FAILED or BLOCKED, stop the loop immediately - do not advance.

### Logging

For every stage outcome, append one line to `.agent-runs/<run-id>/run.log` using the Bash tool. Get the timestamp with `date -u +"%Y-%m-%dT%H:%M:%SZ"`. Format:

```
2026-05-09T04:30:00Z | <stage_name> | COMPLETE | <note>
```

Use the Bash redirect `>> ` so the log appends rather than overwrites. Quote the line carefully - the note may contain spaces.

### Handler 1 - `role: human` with `gate: human_approval`

These stages exist at the start of the pipeline (the `manifest` stage). They represent a checkpoint where the human director must approve before any agent runs.

Steps:

1. If the stage has a previously-produced artifact (look at the prior stages for the artifact filename), instruct the user to review it: `Review .agent-runs/<run-id>/<artifact_filename> before continuing.`
2. Use `a structured user question` with:
   - Question: `Gate: <stage_name> - type APPROVE to proceed, or describe what needs to change to stop the pipeline.`
   - Header: `Gate`
   - Options:
     - Label: `APPROVE` - Description: `Proceed to the next stage.`
     - Label: `Block - needs changes` - Description: `Stop the pipeline; describe required changes in the next message.`
3. If the user selects `APPROVE`: append `<TS> | <stage_name> | COMPLETE | human approved` to `run.log` and continue to the next stage.
4. If the user selects `Block - needs changes` OR types any other free-form response: append `<TS> | <stage_name> | BLOCKED | <user response, single line>` to `run.log`. Report the block reason to the user. STOP the pipeline. Do not advance.

### Handler 2 - `role: pipeline` with a `command`

The standard stages of this type are `policy` and (v0.5) `auto-promote`. They run the command named in the stage's `command` field.

Steps:

1. Substitute `{run_id}` in the `command` field with the actual run id.
2. Use the shell tool to run the command from the repo root. Capture both stdout and stderr (`2>&1`). Save the combined output.
3. **Artifact handling** depends on the stage:
   - For regular pipeline stages (no `optional_artifact`): Write the captured output to `.agent-runs/<run-id>/<artifact_filename>` (use the Write tool - do not use shell redirection because the orchestrator must see the output too).
   - For stages with `optional_artifact: true` (v0.5 `auto-promote`): the command writes its own outputs (either `manager-decision.md` on success or `auto-promote-report.md` on failure). The orchestrator does NOT write the captured output; it leaves whatever the command produced in place. The captured stdout is still displayed to the user for transparency.
4. **Exit code handling** also depends on the stage:
   - For regular pipeline stages: If the Bash exit code is `0`: append `<TS> | <stage_name> | COMPLETE | command exit 0` to `run.log` and continue. If non-zero: append `<TS> | <stage_name> | FAILED | see <artifact_filename>` to `run.log`, display the report content, and STOP the pipeline.
   - For the v0.5 `auto-promote` stage specifically: BOTH exit codes 0 and 1 advance the pipeline. Exit 0 means ELIGIBLE (manager-decision.md was preset); exit 1 means NOT_ELIGIBLE (auto-promote-report.md names which conditions failed; the manager stage will run with the human gate). Append `<TS> | <stage_name> | COMPLETE | auto-promote ELIGIBLE` or `<TS> | <stage_name> | COMPLETE | auto-promote NOT_ELIGIBLE` accordingly. Exit code 2 (run dir not found) is a real failure and STOPS the pipeline.

### Handler 3 - agent role (`researcher`, `planner`, `test-writer`, `executor`, `verifier`, `manager`)

These stages do real work: an isolated subagent reads inputs, produces an artifact, and exits.

**Selection note for `role: executor`:** before applying Handler 3, check whether `.pipelines/action-classification.yaml` exists in the project. If it does, the judge layer is opt-in active for this run - use **Handler 3a** instead of Handler 3 for the executor stage only. All other roles continue to use Handler 3 unchanged. If `action-classification.yaml` does not exist, Handler 3 is used for the executor as well.

Steps:

1. Read `.pipelines/roles/<role>.md` in full. This is the role's instructions - the subagent will see it verbatim as its prompt header.
2. Build the run-context block:
   - Open with: `--- manifest.yaml ---\n` followed by the manifest content
   - For each prior stage in YAML order whose `artifact` file exists in `.agent-runs/<run-id>/`, append: `\n--- <artifact_filename> ---\n` followed by the file content
   - Skip stages whose artifact file does not exist
3. Spawn a default Codex subagent with:
   - **Description:** `<role> stage for run <run-id>`
   - **Prompt:** the role file content verbatim, followed by `\n\n---\n\nRUN CONTEXT:\n` followed by the run-context block, followed by `\n\nRUN ID: <run-id>\nWORKING DIR: .agent-runs/<run-id>/\nWrite your output to .agent-runs/<run-id>/<expected_artifact_filename> and stop.`
4. After the Codex subagent completes, verify the expected artifact exists. The expected filename is the stage's `artifact` field. Use the shell tool: `test -s .agent-runs/<run-id>/<artifact>` (the `-s` flag also catches empty files).
5. If the artifact file is missing or empty: append `<TS> | <stage_name> | FAILED | artifact not produced (or empty)` to `run.log`. Report the failure with the agent's last message. STOP the pipeline.
6. If the artifact exists and is non-empty: append `<TS> | <stage_name> | COMPLETE | <artifact_filename> written` to `run.log`. Briefly report the stage completed and continue to the next stage.

### Handler 3a - executor with judge interceptor (opt-in via action-classification.yaml)

This handler is selected for `role: executor` ONLY when `.pipelines/action-classification.yaml` exists. It wraps the standard executor in a **classify -> judge -> execute** inner loop. The executor role file is unchanged; the executor does not know the judge exists. Interception happens transparently in the orchestrator.

The judge is real-time, action-level supervision: every tool call the executor proposes is classified by risk class, and dangerous actions are intercepted before they execute. The classifier and the judge stop unauthorized actions in real time rather than catching them at the policy or verifier stages after they have already affected the working tree.

#### Setup

1. Read `.pipelines/action-classification.yaml`. Parse the four class lists (`high_risk`, `external_facing`, `reversible_write`, `read_only`) and the `default_class`. Each entry has a `pattern` (regex; optional if `tool` is set), an optional `tool` filter (e.g. `bash`, `str_replace_editor`), and a `note`.
2. Read `.pipelines/roles/judge.md` - the judge subagent will receive this verbatim as its prompt header when invoked.
3. Read the executor role file and build the run-context block exactly as in Handler 3 step 2.
4. Create the per-run directory `.agent-runs/<run-id>/judge-decisions/` (the judge writes its YAML verdicts into this directory).
5. Initialize an empty in-memory list `prior_judge_decisions` (used to detect re-proposals of blocked actions).
6. Initialize counters for `judge-metrics.yaml`: `total_actions`, `by_class` (four classes), `by_disposition` (auto_allow, judged_allow, judged_revise, judged_block, judged_escalate, human_confirmed, human_blocked), `judge_invocations`, `revision_cycles`, `escalation_rate`.

#### Inner loop

Spawn the executor subagent exactly as in Handler 3 step 3 (same role-file + run-context + working-directory prompt). The executor proceeds normally. For each tool call the executor proposes:

**Step 1 - Classify.** Walk the four class lists in this order: `high_risk`, `external_facing`, `reversible_write`, `read_only`. Within each class, walk entries top-to-bottom. The first entry whose `tool` filter matches (if present) AND whose `pattern` regex matches (if present) wins; classification stops. If no entry matches across all classes, use `default_class` (typically `reversible_write`). Record the matched class and the matched rule's `note` for logging.

**Step 2 - Route by class.**

- `read_only` -> execute the action immediately. Append a `judge_log` entry with `disposition: auto_allow`. Continue.
- `reversible_write` -> execute the action immediately. Append a `judge_log` entry with `disposition: auto_allow`. Continue.
- `external_facing` -> STOP. Proceed to Step 3 (spawn judge).
- `high_risk` -> STOP. Proceed to Step 3 (spawn judge). After the judge returns ALLOW, ALSO require human confirmation via Step 5 before executing.

**Step 3 - Spawn judge subagent.** Build the judge context (deliberately scoped - the judge must NOT see the executor's reasoning chain or planning context):

- `--- manifest.yaml ---\n` followed by the manifest content
- `--- action_policy ---\n` followed by the matched rule's class, pattern, and note
- `--- prior_judge_decisions ---\n` followed by the YAML content of every file under `.agent-runs/<run-id>/judge-decisions/` concatenated in chronological order (so the judge can detect re-proposals). If the directory is empty, write `(none yet)`.
- `--- action_proposal ---\n` followed by an `action_proposal:` YAML block containing `action_id` (generate as `exec-<NNN>` where NNN is a zero-padded counter starting at 001 for this run), `tool`, `arguments` (verbatim), `action_class`, `executor_justification` (the executor's stated reason - extract from the proposed-tool-call context), `executor_evidence` (the file paths, line numbers, or prior artifacts the executor cited; empty list if none).

Spawn a default Codex subagent with:

- **Description:** `judge stage for action <action_id> in run <run-id>`
- **Prompt:** the content of `.pipelines/roles/judge.md` verbatim, followed by `\n\n---\n\nRUN CONTEXT:\n` followed by the judge-context block built above, followed by `\n\nRUN ID: <run-id>\nWRITE YOUR OUTPUT to .agent-runs/<run-id>/judge-decisions/<action_id>.yaml and stop.`

Increment `judge_invocations`.

**Step 4 - Parse the verdict.** Read `.agent-runs/<run-id>/judge-decisions/<action_id>.yaml`. Validate it contains exactly one `judge_decision:` block with a `verdict` field set to one of `allow`, `block`, `revise`, `escalate`. If the file is missing, empty, or the verdict field is invalid, treat the action as auto-escalated: append a `judge_log` entry with `disposition: judged_escalate` and a synthetic escalation question pointing to the malformed verdict file. Fall through to Step 5.

Append the parsed verdict to `prior_judge_decisions`.

**Step 5 - Route by verdict.**

- `allow` (and class is `external_facing`): execute the action. Append `judge_log` with `disposition: judged_allow`.
- `allow` (and class is `high_risk`): use `a structured user question` with the question "Judge ALLOWed a high-risk action: `<arguments>`. Judge reason: `<reason>`. Confirm execution? (Type APPROVE to execute, or describe what should change.)" If user types APPROVE: execute the action; append `judge_log` with `disposition: human_confirmed`. Otherwise: do not execute; append `judge_log` with `disposition: human_blocked`; STOP the executor stage (write `<TS> | execute | BLOCKED | high-risk action denied by human` to `run.log` and halt the pipeline).
- `block`: do not execute. Append `judge_log` with `disposition: judged_block`. Write `<TS> | execute | BLOCKED | judge BLOCK on action <action_id>: <reason>` to `run.log`. STOP the pipeline; report the block reason and the resume command.
- `revise`: do not execute. Append `judge_log` with `disposition: judged_revise`. Send the executor a revision message containing the `revision_instruction` field verbatim. The executor should produce a revised action proposal; increment `revision_cycles` and return to Step 1 with the revised proposal. **Cap: 3 revision cycles per action_id**. On the 4th cycle, auto-escalate (treat as if `verdict: escalate` with `escalation_question: "Executor proposed this action 4 times after revise verdicts; revision loop is not converging."`).
- `escalate`: use `a structured user question` with the `escalation_question` field verbatim as the question text. Options: `APPROVE` (proceed with action), `Block - needs changes` (halt with feedback). If APPROVE: execute the action; append `judge_log` with `disposition: human_confirmed`. Otherwise: append `judge_log` with `disposition: human_blocked`; STOP the pipeline.

Increment the matching `by_disposition` counter.

**Step 6 - Continue.** Return control to the executor subagent. The executor proceeds to its next tool call; the loop repeats.

#### Logging the action

For every action (auto-allowed or judged), append one entry to an in-memory `judge_log_actions` list, formatted as:

```yaml
- action_id: "exec-NNN"
  tool: <tool name>
  arguments: <arguments verbatim, single-quoted YAML if multiline>
  class: <matched class>
  disposition: <one of: auto_allow | judged_allow | judged_revise | judged_block | judged_escalate | human_confirmed | human_blocked>
  judge_verdict: <only if judged: allow | block | revise | escalate>
  judge_reason: <only if judged: the verdict's reason field>
  revision_instruction: <only if judged_revise: the verdict's revision_instruction>
  timestamp: <ISO-8601 UTC, e.g. 2026-05-11T14:30:00Z>
```

Increment `total_actions` and the `by_class` counter for the matched class.

#### After the executor completes

When the executor subagent finishes (whether by writing its artifact normally OR by being halted via judge BLOCK or human block):

1. Write `judge-log.yaml` to `.agent-runs/<run-id>/judge-log.yaml`. Top-level key is `actions:` followed by the accumulated `judge_log_actions` list. Example:
   ```yaml
   actions:
     - action_id: "exec-001"
       tool: bash
       arguments: "cat src/auth/models.py"
       class: read_only
       disposition: auto_allow
       timestamp: "2026-05-11T14:30:00Z"
     - action_id: "exec-007"
       tool: bash
       arguments: "git push origin main"
       class: high_risk
       disposition: judged_revise
       judge_verdict: revise
       judge_reason: "Manifest authorizes implementation on feature branch; main push is not in scope."
       revision_instruction: "Push to feature/judge-layer-v0.4 instead of main."
       timestamp: "2026-05-11T14:35:12Z"
   ```

2. Write `judge-metrics.yaml` to `.agent-runs/<run-id>/judge-metrics.yaml`. Compute `escalation_rate` as `(judged_escalate + human_blocked) / max(total_actions, 1)`. Example:
   ```yaml
   total_actions: 23
   by_class:
     read_only: 12
     reversible_write: 7
     external_facing: 3
     high_risk: 1
   by_disposition:
     auto_allow: 19
     judged_allow: 2
     judged_revise: 1
     judged_block: 0
     judged_escalate: 1
     human_confirmed: 1
     human_blocked: 0
   escalation_rate: 0.087
   judge_invocations: 4
   revision_cycles: 1
   ```

3. Print a judge tuning summary in the checkpoint report before continuing:

   ```text
   Judge summary: <total_actions> action(s), <judge_invocations> judged, escalation_rate=<rate>, blocks=<judged_block + human_blocked>, revisions=<judged_revise>.
   ```

   If `escalation_rate` is below `0.02`, add: `Tuning note: judge rules may be too permissive or the run was mostly read-only.`
   If `escalation_rate` is above `0.10`, add: `Tuning note: judge rules may be too broad; review action-classification.yaml before the next run.`
   This is an operator signal only; it does not change gate status.

4. Verify the executor's expected artifact (`implementation-report.md`) exists and is non-empty, exactly as in Handler 3 step 4.

5. If the executor was halted mid-loop (by judge BLOCK or human block), the implementation-report.md may be incomplete or missing. In that case the executor stage is marked BLOCKED in the run log per the verdict-routing rules in Step 5 above; `judge-log.yaml` and `judge-metrics.yaml` are still written so the verifier and manager can see what happened.

6. If the executor completed normally and the artifact exists: append `<TS> | execute | COMPLETE | implementation-report.md written; judge intercepted <N> action(s)` to `run.log` and continue to the next stage.

### Handler 4 - `role: manager` with `auto_promote_aware: true` (v0.5)

This handler replaces both Handler 1 (human gate) and Handler 3 (agent role) for the manager stage when the stage YAML sets `auto_promote_aware: true`. It checks for an auto-promote preset before deciding whether to invoke the manager subagent and whether to fire the human gate.

Steps:

1. **Check for preset.** Use the Read tool: read `.agent-runs/<run-id>/manager-decision.md`. If the read succeeds AND the file's first non-empty line is exactly `**Decision: PROMOTE**`, the auto-promote stage already wrote the verdict. Proceed to step 2. Otherwise, jump to step 4.
2. **Spawn manager subagent in validate-and-append mode.** Use the standard Handler 3 spawn (role file + run context + working directory), but the prompt's tail instructs the agent: "An auto-promote preset already wrote `**Decision: PROMOTE**`. Validate the six citations in the existing file match the artifacts (verifier-report.md, critic-report.md, drift-report.md, policy-report.md, judge-metrics.yaml or 'judge not active', implementation-report.md). Append a `## Manager confirmation` section listing what you validated. DO NOT REWRITE the first line. DO NOT change the verdict."
3. **Skip the human gate.** When the preset is present and the manager subagent appends confirmation cleanly, append `<TS> | manager | COMPLETE | auto-promoted by scripts/policy/auto_promote.py, manager confirmed` to `run.log`. Do NOT use `a structured user question`. The pipeline advances. Report to the user: "Manager stage auto-promoted; the six v0.5 conditions all passed. See `.agent-runs/<run-id>/manager-decision.md` for the citation block."
4. **No preset - fall through to standard handling.** Run Handler 3 (spawn the manager subagent normally) followed by Handler 1's human-approval gate logic (`a structured user question` with APPROVE / Block). If the auto-promote stage wrote `auto-promote-report.md`, include its contents in the manager subagent's context so the manager can see which conditions failed.

The runner uses Handler 4 ONLY when the stage's YAML sets `auto_promote_aware: true`. The pre-v0.5 feature.yaml and bugfix.yaml that don't have this flag continue to route the manager stage through Handler 3 + Handler 1 unchanged.

**Auto-promote eligibility is per-run, not per-pipeline.** Even when `auto_promote_aware: true` is set on the YAML, the eligibility check fires only when `auto_promote.py` produced the preset. If any of the six conditions failed, the human gate fires as usual.

### Stop conditions

The loop stops on the FIRST of:

- A `BLOCKED` outcome at an explicit human approval gate in the pipeline
- A failed gate that needs user direction
- A destructive action is required
- A credential or secret is required
- A scope conflict is detected
- An external system remains unavailable after retry
- The user explicitly says pause or stop
- All stages have `COMPLETE` log entries - fall through to Phase C

Never advance past a non-`COMPLETE` stage. Never rewrite or delete an existing log entry.

Invalid stop conditions:

- Successful push
- Green CI
- Recommended next action
- Open caveats
- Release or tag action after all required review, test, judge, CI, and release gates have passed
- PR draft status by itself
- Unverified blocker or risk

---

## Phase C - Wrap-up

When every stage has a `COMPLETE` log entry:

1. Print to the user:
   ```
   Pipeline stages complete. Control-loop gate still applies.
   Run: .agent-runs/<run-id>/
   ```
2. List every artifact file in `.agent-runs/<run-id>/` with its size (use `ls -la` via the shell tool).
3. If `manager-decision.md` exists, read its first non-empty line and display it. (It should start with `**Decision: PROMOTE**`, `**Decision: BLOCK**`, or `**Decision: REPLAN**`.)
4. Tell the user the pipeline manager decision and the next action based on that decision:
   - `PROMOTE` - continue to the next authorized action. Push, merge, release, and tag are executed when they are inside the authorized slice and all required gates have passed.
   - `BLOCK` - review the manager-decision.md for the smallest fix set; address it and re-run the failing stages.
   - `REPLAN` - the manifest needs to be revised; review the manager's recommended changes.

5. The three manager decisions are interpreted mechanically:
   - `PROMOTE` means continue to the next authorized action. If push has already been authorized, continue into Phase D. If merge, release, or tag is inside the authorized slice and all required review, test, judge, CI, and release gates have passed, execute it instead of stopping.
   - `BLOCK` means review `manager-decision.md` for the smallest fix set, record `failed_gate_needs_user_direction` only when user direction is actually required, then address the fix set and re-run the failing stages.
   - `REPLAN` means the manifest must be revised before further implementation. Record `scope_conflict` when the revision changes authorized scope.
6. Write or update `.agent-runs/<run-id>/active-control-state.md`.
7. Run `python scripts/policy/check_pipeline_control_loop.py --run <run-id>`.
8. Run `python scripts/policy/final_response_gate.py --require-active-run`.
9. Run `python scripts/policy/agent_decision_gate.py --intent final_response --claimed-stop-condition <condition> --write-ledger`.
10. If any command blocks, do not send a final answer. Run `python scripts/policy/pipeline_continue.py` and continue to the printed action.

---

## Phase D - Post-Push CI Follow-Through

Run this phase after every authorized push.

1. Record the pushed branch and head SHA in `.agent-runs/<run-id>/post-push-ci-report.md`.
2. Monitor the remote CI checks for that exact SHA.
3. If any check fails, inspect the logs, fix failures inside the authorized scope, run the local verification required by the manifest, commit, push, and repeat Phase D for the new SHA.
4. If CI is green and no unresolved caveats remain, update `.agent-runs/<run-id>/active-control-state.md` with `stop_condition: none`, `final_response_allowed: false`, and the next required action.
5. If CI is green and the next required action is merge, release, or tag inside the authorized slice after all gates have passed, execute that action and then continue to Phase E.

Green CI is evidence. It is not permission to stop.

---

## Phase E - Active Control State

Before every user-facing final response during an authorized pipeline run, write `.agent-runs/<run-id>/active-control-state.md` with exactly these fields:

```yaml
active_run: true
current_stage: <stage-id-or-post-push-ci>
last_completed_gate: <gate-or-none>
next_required_action: <concrete-action>
stop_condition: none | human_approval_gate | failed_gate_needs_user_direction | destructive_action | credential_or_secret_required | scope_conflict | external_system_unavailable_after_retry | user_explicitly_paused_or_stopped
final_response_allowed: true | false
continuing_to: <concrete-action>
```

Rules:

- `stop_condition: none` requires `final_response_allowed: false` and a non-empty `continuing_to`.
- Any valid stop condition requires `final_response_allowed: true` and a concrete explanation in `next_required_action`.
- These strings are never valid stop conditions: `successful_push`, `green_ci`, `recommended_next_action`, `open_caveats`, `release_or_tag_after_gates_pass`, `pr_draft_status`, `unverified_blocker_or_risk`.
- An `Open Caveats / Release Risks` section blocks completion when it contains any unresolved bullet not prefixed with `INTENTIONAL DEFERRAL:`.
- Run `python scripts/policy/check_pipeline_control_loop.py --run <run-id>` before any final response. If it fails, continue work or fix the control state.
- Run `python scripts/policy/final_response_gate.py --require-active-run` before any final response. If it prints `final_response_gate: BLOCK`, continue to the printed `continuing_to` action.
- Run `python scripts/policy/agent_decision_gate.py --intent <intent> --claimed-stop-condition <condition> --write-ledger` before every stop, defer, skipped push, skipped CI, handoff-and-stop, compact-and-stop, or non-gate question. If it prints `agent_decision_gate: BLOCK`, run `python scripts/policy/pipeline_continue.py` and continue.

---

## Hard rules (apply throughout)

- **Never silently skip a stage.** Either it produces a `COMPLETE` log line or the pipeline halts.
- **Never advance past a `BLOCKED` or `FAILED` stage.** Resuming requires the operator to fix the underlying cause and re-run; the runner will pick up at the right place.
- **Never modify the role files** in `.pipelines/roles/` - those are the contract. If a role is wrong, that's a separate fix the operator must make outside the pipeline.
- **Never modify the manifest** mid-run. The manifest is the contract for the entire run; if it needs to change, the manager returns `REPLAN` and the operator re-issues `new-run`.
- **Never edit `run.log` retroactively.** Append only.
- **Never run agent stages with the same Agent slot you're using.** Always use the Codex `spawn_agent` tool to spawn isolated subagents - they must not see this orchestrator's conversation history.
- **Never invent stages not in the YAML.** The pipeline schema is the source of truth.
- **Never assume tool availability.** If `a structured user question`, `Agent`, or any other tool is in the deferred list, load it via `ToolSearch` before invoking.
- **Never propose autonomous mode.** Every gate is explicit. If the user wants autonomous, they explicitly raise it; the runner does not suggest it.
- **Never end an authorized run without both control-loop gates.** `.agent-runs/<run-id>/active-control-state.md` must exist, `python scripts/policy/check_pipeline_control_loop.py --run <run-id>` must pass, and `python scripts/policy/final_response_gate.py --require-active-run` must print `final_response_gate: ALLOW` before any final response.
- **Never stop on an unverified blocker.** Claimed blockers must pass `python scripts/policy/agent_decision_gate.py --intent <intent> --claimed-stop-condition <condition> --write-ledger`. If the gate blocks, run `python scripts/policy/pipeline_continue.py` and continue.
- **Never treat completion evidence as a stop condition.** Successful push, green CI, draft PR status, and a recommended next action all require continued execution when the next action is authorized.
- **Never leave unresolved caveats behind.** Every `Open Caveats / Release Risks` bullet is blocking until fixed or prefixed with `INTENTIONAL DEFERRAL:` and backed by the manifest or user direction.
- **Never stop for release or tag after gates pass.** If merge, release, or tag is inside the authorized slice and all required review, test, judge, CI, and release gates have passed, execute it.
- **At any failure or stop, give the user the exact resume command:** `run-pipeline <pipeline-type> <run-id>` - re-invoking is safe because the log determines where to start.
- **Never merge in-flight PRs while a halt is active.** If the orchestrator is stopped on any gate or any open question, no other repo state changes happen - including cleanup PRs that "seem safe."
- **Judge layer is opt-in and per-run-determined.** The presence of `.pipelines/action-classification.yaml` at the start of the run decides whether Handler 3a or Handler 3 is used for the executor stage. Do not toggle this mid-run; if the file is added or removed while a run is paused, the resumed run uses whatever is on disk at resume time, which is intentional but worth knowing.
- **Judge subagents are context-isolated by design.** When spawning the judge in Handler 3a, supply only the manifest, action policy, prior judge decisions, and the structured action proposal. Do NOT include the executor's role file, the run-context block, or any prior conversation history. The judge's whole defensive value comes from not seeing the executor's reasoning chain.
