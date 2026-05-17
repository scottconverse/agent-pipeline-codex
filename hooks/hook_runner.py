#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Codex lifecycle hook entrypoint for Agent Pipeline for Codex."""

from __future__ import annotations

import sys

try:
    from hook_utils import (
        append_hook_event,
        classify_tool_risk,
        discover_active_runs,
        permission_decision,
        prompt_bypass_context,
        read_hook_input,
        repo_root_from_event,
        session_context,
        stale_skill_context,
        stop_continuation,
        tool_failure_context,
        write_json,
    )
except ModuleNotFoundError:  # pragma: no cover - package import from tests
    from hooks.hook_utils import (
        append_hook_event,
        classify_tool_risk,
        discover_active_runs,
        permission_decision,
        prompt_bypass_context,
        read_hook_input,
        repo_root_from_event,
        session_context,
        stale_skill_context,
        stop_continuation,
        tool_failure_context,
        write_json,
    )


def _context_payload(event_name: str, context: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context,
        }
    }


def handle_session_start(event: dict) -> int:
    if event.get("source") not in {"startup", "resume"}:
        return 0
    root = repo_root_from_event(event)
    context = session_context(discover_active_runs(root))
    if not context:
        return 0
    append_hook_event(root, "SessionStart", "added active run context")
    return write_json(_context_payload("SessionStart", context))


def handle_user_prompt_submit(event: dict) -> int:
    root = repo_root_from_event(event)
    runs = discover_active_runs(root)
    prompt = str(event.get("prompt") or "")
    contexts = [item for item in (stale_skill_context(prompt),) if item]
    blocked, bypass = prompt_bypass_context(prompt, runs)
    if blocked:
        append_hook_event(root, "UserPromptSubmit", "blocked pipeline bypass prompt")
        return write_json({"decision": "block", "reason": bypass})
    if not contexts:
        return 0
    context = "\n".join(contexts)
    append_hook_event(root, "UserPromptSubmit", context)
    return write_json(_context_payload("UserPromptSubmit", context))


def handle_pre_tool_use(event: dict) -> int:
    root = repo_root_from_event(event)
    severity, reasons = classify_tool_risk(event, discover_active_runs(root))
    if severity == "deny":
        reason = "Agent Pipeline hook denied tool call: " + "; ".join(reasons)
        append_hook_event(root, "PreToolUse", reason)
        return write_json(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    if severity == "warn":
        context = "Agent Pipeline hook warning: " + "; ".join(reasons) + ". Confirm manifest, scope-lock, directive, and judge policy before treating this action as authorized."
        append_hook_event(root, "PreToolUse", context)
        return write_json(_context_payload("PreToolUse", context))
    return 0


def handle_permission_request(event: dict) -> int:
    root = repo_root_from_event(event)
    decision = permission_decision(event, discover_active_runs(root))
    if decision is None:
        return 0
    append_hook_event(root, "PermissionRequest", "returned approval decision")
    return write_json(decision)


def handle_post_tool_use(event: dict) -> int:
    root = repo_root_from_event(event)
    context = tool_failure_context(event)
    if not context:
        return 0
    append_hook_event(root, "PostToolUse", context)
    return write_json(
        {
            "decision": "block",
            "reason": "Agent Pipeline hook is replacing the tool result with pipeline continuation guidance.",
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": context,
            },
        }
    )


def handle_stop(event: dict) -> int:
    if event.get("stop_hook_active") is True:
        return 0
    root = repo_root_from_event(event)
    continuation = stop_continuation(root)
    if not continuation:
        return 0
    append_hook_event(root, "Stop", "continued invalid pipeline stop")
    return write_json({"decision": "block", "reason": continuation})


HANDLERS = {
    "SessionStart": handle_session_start,
    "UserPromptSubmit": handle_user_prompt_submit,
    "PreToolUse": handle_pre_tool_use,
    "PermissionRequest": handle_permission_request,
    "PostToolUse": handle_post_tool_use,
    "Stop": handle_stop,
}


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    event_name = argv[0] if argv else ""
    event = read_hook_input()
    event_name = event_name or str(event.get("hook_event_name") or "")
    handler = HANDLERS.get(event_name)
    if handler is None:
        return 0
    return handler(event)


if __name__ == "__main__":
    sys.exit(main())
