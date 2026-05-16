# vNext Directive Contract Design

## Platform Facts

This design is implementable inside Codex Desktop because the manifest, plan,
and manager prompts are plugin workflow gates, not platform approval gates.
Codex still owns platform approvals for sandbox escapes, MCP/app side effects,
and other protected tool requests.

Documented Codex constraints used by this design:

- The Codex app is a desktop command center with local threads, worktrees,
  automations, terminal/actions, in-app browser, skills, plugins, and built-in
  Git support. Source: OpenAI Codex app docs,
  <https://developers.openai.com/codex/app>.
- Plugins are packaged through `.codex-plugin/plugin.json`; the stable plugin
  `name` is used as the plugin identifier and component namespace. Source:
  OpenAI build-plugins docs, <https://developers.openai.com/codex/plugins/build>.
- Skills are explicitly invokable in the app composer, and enabled skills also
  appear in the slash-command list. Source: OpenAI Codex app commands docs,
  <https://developers.openai.com/codex/app/commands>.
- Subagents are supported in the app and CLI, inherit the parent sandbox policy,
  and approval requests can surface from inactive agent threads. In
  non-interactive flows, actions needing fresh approval fail and surface back to
  the parent workflow. Source: OpenAI subagents docs,
  <https://developers.openai.com/codex/subagents>.
- Codex can run without approval prompts only through user-selected runtime
  configuration such as `--ask-for-approval never` and sandbox choices; granular
  approval policy and auto-review exist at the platform layer. Source: OpenAI
  agent approvals and security docs,
  <https://developers.openai.com/codex/agent-approvals-security>.
- `codex exec` non-interactive mode is for scripted runs with explicit sandbox
  and approval settings; by default it runs read-only and needs explicit
  permissions for edits or broader access. Source: OpenAI non-interactive mode
  docs, <https://developers.openai.com/codex/noninteractive>.

No OpenAI documentation found a plugin-level API for programmatically answering
platform approvals or `AskUserQuestion` prompts. Therefore this design does not
attempt to bypass platform approvals. It removes plugin-authored questions only
when a local policy script proves that the operator already pre-approved the
exact artifact and criteria in `directive.yaml`.

## Namespacing

The plugin keeps the `agent-pipeline-codex:*` skill surface. OpenAI's plugin
docs state that Codex uses the plugin name as the component namespace. This
closes the stale-standalone-skill failure where a session sees `run-pipeline`
from `$CODEX_HOME/skills` and mistakes it for the current installed plugin.
Directive support is added to the same namespaced plugin and does not introduce
unnamespaced skills.

## Directive Artifact

New optional file:

```text
.agent-runs/<run-id>/directive.yaml
```

Opt-in is by file presence at run start. Projects with no directive keep the
current interactive behavior.

Required schema:

- `version: 1`
- `content_hash`: optional self-check SHA-256 of the directive file
- `author`: human/team identity logged with every auto-approval
- `authority`: source of authority such as PR URL, design doc, issue, release
  directive, or operator signature
- `preapproved.manifest`: YAML object that must exactly match
  `manifest.yaml` after parsing
- `preapproved.scope_lock`: YAML object that must exactly match
  `scope-lock.yaml` after parsing
- `acceptance.plan`: assertions over `plan.md`
- `acceptance.manager`: assertions over the final artifact stack, added to the
  six existing auto-promote conditions

Assertion types:

- `regex`: regex match against an artifact, with optional flags and min count
- `contains`: exact substring in an artifact
- `section`: Markdown heading exists and has minimum body length
- `artifact_exists`: artifact exists and is non-empty
- `callable`: registered Python callable by local public name only

Callable assertions are fail-closed. Names with dots or leading underscores are
rejected so a directive cannot import arbitrary modules.

## Flow

1. After `manifest.yaml` and `scope-lock.yaml` exist, before the manifest human
   gate, run `check_directive_conformance.py --run <run-id> --bind`.
2. If the directive is absent, malformed, non-conformant, or has unsupported
   content, fall back to the existing interactive manifest gate.
3. If manifest and scope lock exactly match, bind SHA-256 to `run.log` with a
   `directive-bound` line and auto-complete the manifest gate.
4. After planner writes `plan.md`, run `check_plan_against_directive.py`.
5. If every plan assertion passes, auto-complete the plan gate. If any fails,
   ask the existing plan question with the failing criteria output.
6. `auto_promote.py` keeps the six existing conditions and appends every
   directive manager assertion. Auto-promote fires only when all six plus N are
   green.
7. `manager-decision.md` cites the directive hash, author, authority source,
   and satisfied directive assertions.

## Integrity

`check_directive_conformance.py --bind` writes the directive hash into
`run.log` before gate auto-approval. Later directive-aware checks compare the
current file hash against the bound hash. A mismatch returns a distinct failure
code and requires explicit operator acknowledgment before resume.

The plugin logs provenance but does not cryptographically verify authority. The
evidence chain is stronger than reflexive interactive approval because it has:

- named directive author and authority source;
- exact manifest/scope-lock comparison;
- machine-checked plan and manager assertions;
- immutable hash binding in the append-only run log;
- fail-closed behavior on tampering.

## Preserved Protections

- Manifest schema validation still runs.
- Scope lock validation still runs.
- Policy stage still runs.
- Test-first and execute-readiness gates remain intact.
- Verifier still checks every manifest criterion in fresh context.
- Drift detector still checks manifest-contract drift.
- Critic still performs adversarial cold read.
- Manager still cites verifier evidence.
- Judge layer remains opt-in by `action-classification.yaml`.
- Judge context isolation is unchanged.
- High-risk judge ALLOW still requires human confirmation.
- Judge `escalate` still pauses for a human answer.
- Control-loop stop validation still blocks invalid stops.
- Successful push, green CI, recommended next action, open caveats, and draft PR
  status remain invalid stop conditions.

## Honest Limits

Directive contracts encode machine-checkable assertions. They cannot encode
taste, novel judgment, or unknown future tool calls. Runs needing judgment keep
the human gate cost. Codex platform approvals also remain outside plugin
control; if Codex requires a platform approval for a tool call, this plugin
cannot answer it programmatically.

## Migration

Existing projects do nothing and keep current behavior. Adopting projects copy
`pipelines/directive-template.yaml` to `.agent-runs/<run-id>/directive.yaml`
before starting the run and fill in the preapproved manifest, scope lock, and
assertions. Bisecting is safe because absence of `directive.yaml` preserves the
old path.
