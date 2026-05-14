---
description: Initialize a new pipeline run (creates manifest and scope-lock skeletons). Run pipeline-init first if the project isn't initialized.
argument-hint: <pipeline-type> <slug>
---

# new-run - initialize a pipeline run

You are initializing a new agentic pipeline run. Do not start the pipeline. Do not validate semantic content of the manifest or scope lock. Just initialize the directory, the manifest skeleton, and the scope-lock skeleton, then hand off to the user.

## Prerequisite

The user's project must have been initialized with `pipeline-init` first. Verify by checking that `.pipelines/<pipeline-type>.yaml`, `.pipelines/manifest-template.yaml`, and `.pipelines/scope-lock-template.yaml` exist. If not, stop and tell the user to run `pipeline-init` first.

## Arguments

`$ARGUMENTS` is one line containing two whitespace-separated tokens:

- **`<pipeline-type>`** - must match a YAML in `.pipelines/` (typically `feature` or `bugfix`).
- **`<slug>`** - kebab-case task name, e.g. `auth-timeout`. Lowercase ASCII, hyphens only.

Example: `feature auth-timeout`

If `$ARGUMENTS` does not contain exactly two tokens, stop and tell the user the correct usage: `new-run <pipeline-type> <slug>`.

## What to do

Execute these steps in order. Do not skip any. Do not run a Bash subshell loop - perform each step as its own tool call.

### 1. Parse arguments

Split `$ARGUMENTS` into `pipeline_type` and `slug`. Trim whitespace.

Validate `pipeline_type` matches a `.pipelines/<pipeline_type>.yaml` file. If not, list available pipelines (every `.yaml` under `.pipelines/` except `manifest-template.yaml`) and stop.

Validate `slug` matches `^[a-z0-9][a-z0-9-]*$`. If not, stop and report the format requirement.

### 2. Generate run id

`run_id = "{today_iso_date}-{slug}"` where `today_iso_date` is `YYYY-MM-DD` from the system date. Use the shell tool to get today's date: `date +%Y-%m-%d`.

### 3. Verify the pipeline definition exists

Read `.pipelines/<pipeline_type>.yaml`. If the Read tool fails, stop with a usage message listing the YAMLs that DO exist under `.pipelines/`.

### 4. Create the run directory

Use Bash: `mkdir -p .agent-runs/<run_id>`.

If the directory already exists AND already contains a `manifest.yaml` or `scope-lock.yaml`, stop and tell the user the run already exists. Do not overwrite.

### 5. Read the templates

Read `.pipelines/manifest-template.yaml` in full. You will use its content as the starting point, modifying only the `id` and `type` fields.

Read `.pipelines/scope-lock-template.yaml` in full. You will copy its content verbatim.

### 6. Write the manifest and scope lock

Write `.agent-runs/<run_id>/manifest.yaml`. Take the template content verbatim and replace exactly two values:

- The `id: ""` line becomes `id: "<run_id>"`.
- The `type: feature` line becomes `type: <pipeline_type>` (only change if `pipeline_type` differs from the template default).

Preserve every other line of the template, including all comments. The user fills in the rest.

Write `.agent-runs/<run_id>/scope-lock.yaml` from `.pipelines/scope-lock-template.yaml` verbatim. The user fills in the current rung, canonical source, title, proof, module list, allowed terms, forbidden terms, scope bullets, and exit criteria from the canonical release plan.

### 7. Display the manifest and scope lock to the user

Read both files you just wrote and print their contents to the user verbatim inside fenced code blocks, so they can see exactly what fields they need to fill in.

### 8. Hand off via a structured user question

Use `a structured user question` to present this question:

- **Question:** `Run initialized at .agent-runs/<run_id>/manifest.yaml and scope-lock.yaml`
- **Header:** `Next step`
- **Options:**
  - Label: `I'll fill them in now` - Description: `Open both files in your editor, complete every field, then run run-pipeline <pipeline_type> <run_id>.`
  - Label: `What goes in each field?` - Description: `Read .pipelines/manifest-template.yaml and .pipelines/scope-lock-template.yaml - every field has an inline comment explaining what it expects.`

Do not start the pipeline. Do not validate the manifest content. The pipeline runner (`run-pipeline`) does that as its first step.

## Hard rules

- Do not modify `.pipelines/manifest-template.yaml` itself.
- Do not write to any path other than the new `.agent-runs/<run_id>/manifest.yaml` and `.agent-runs/<run_id>/scope-lock.yaml`.
- Do not invoke any agent.
- Do not run policy checks, tests, or builds.
- If any validation fails, stop and report - do not paper over the failure with defaults.
