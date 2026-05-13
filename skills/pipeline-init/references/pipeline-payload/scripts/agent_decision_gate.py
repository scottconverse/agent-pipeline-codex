#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate agent stop, defer, skip, and final-response decisions.

This gate is for the agent's immediate decision procedure. It does not trust a
claimed blocker unless the control state and attached evidence support it.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.check_pipeline_control_loop import (
        INVALID_STOP_CONDITIONS,
        VALID_STOP_CONDITIONS,
        parse_control_state,
    )
    from scripts.final_response_gate import discover_state_files, evaluate_final_response_gate
except ModuleNotFoundError:  # pragma: no cover - direct script execution from scripts/
    from check_pipeline_control_loop import (  # type: ignore
        INVALID_STOP_CONDITIONS,
        VALID_STOP_CONDITIONS,
        parse_control_state,
    )
    from final_response_gate import discover_state_files, evaluate_final_response_gate  # type: ignore


INVALID_DECISION_REASONS = INVALID_STOP_CONDITIONS | {
    "could_trigger_ci",
    "inferred_blocker",
    "unverified_blocker",
    "unverified_blocker_or_risk",
    "unverified_actions_budget_risk",
    "successful_ci",
    "remote_ci_green",
}

INTENTS = {
    "final_response",
    "defer",
    "stop",
    "skip_push",
    "skip_ci",
    "pause",
    "ask_user",
    "compact",
    "handoff",
}


@dataclass(frozen=True)
class DecisionResult:
    allowed: bool
    intent: str
    claimed_stop_condition: str
    reason: str
    required_next_action: str = ""
    continuing_to: str = ""
    state_path: str = ""


def _find_repo_root() -> Path:
    script_dir = Path(__file__).resolve().parent
    if script_dir.name == "policy" and script_dir.parent.name == "scripts":
        return script_dir.parents[1]
    return script_dir.parent


def _read_state(path: Path) -> dict[str, str]:
    return parse_control_state(path.read_text(encoding="utf-8-sig"))


def _active_state_paths(run_dir: Path) -> list[Path]:
    paths = []
    for path in discover_state_files(run_dir):
        fields = _read_state(path)
        if fields.get("active_run", "").lower() == "true":
            paths.append(path)
    return paths


def _state_for_run(run_dir: Path, run_id: str | None) -> Path | None:
    if run_id:
        path = run_dir / run_id / "active-control-state.md"
        return path if path.exists() else None

    active = _active_state_paths(run_dir)
    if active:
        return active[0]
    return None


def _evidence_files_exist(evidence_files: list[str]) -> tuple[bool, list[str]]:
    missing = [item for item in evidence_files if not Path(item).exists()]
    return not missing, missing


def _has_evidence(evidence: list[str], evidence_files: list[str]) -> bool:
    return any(item.strip() for item in evidence) or bool(evidence_files)


def evaluate_agent_decision(
    run_dir: Path,
    intent: str,
    claimed_stop_condition: str,
    evidence: list[str] | None = None,
    evidence_files: list[str] | None = None,
    run_id: str | None = None,
    require_active_run: bool = True,
) -> DecisionResult:
    evidence = evidence or []
    evidence_files = evidence_files or []

    if intent not in INTENTS:
        return DecisionResult(False, intent, claimed_stop_condition, f"invalid intent `{intent}`")

    final_results = evaluate_final_response_gate(run_dir, require_active_run=require_active_run)
    blocked_final = [result for result in final_results if not result.allowed]
    if blocked_final:
        result = blocked_final[0]
        return DecisionResult(
            False,
            intent,
            claimed_stop_condition,
            result.reason,
            required_next_action=result.next_required_action,
            continuing_to=result.continuing_to,
            state_path=str(result.state_path or ""),
        )

    if claimed_stop_condition in INVALID_DECISION_REASONS:
        return DecisionResult(
            False,
            intent,
            claimed_stop_condition,
            f"`{claimed_stop_condition}` is not a valid stop condition",
        )

    if claimed_stop_condition not in VALID_STOP_CONDITIONS:
        return DecisionResult(
            False,
            intent,
            claimed_stop_condition,
            f"`claimed_stop_condition` must be one of: {', '.join(sorted(VALID_STOP_CONDITIONS))}",
        )

    state_path = _state_for_run(run_dir, run_id)
    state = _read_state(state_path) if state_path else {}
    recorded_stop = state.get("stop_condition", "")

    files_ok, missing = _evidence_files_exist(evidence_files)
    if not files_ok:
        return DecisionResult(
            False,
            intent,
            claimed_stop_condition,
            "evidence file missing: " + ", ".join(missing),
            state_path=str(state_path or ""),
        )

    if recorded_stop != claimed_stop_condition and not _has_evidence(evidence, evidence_files):
        return DecisionResult(
            False,
            intent,
            claimed_stop_condition,
            "claimed blocker has no evidence and does not match active control state",
            state_path=str(state_path or ""),
        )

    if recorded_stop == claimed_stop_condition:
        reason = f"decision allowed by recorded stop condition `{claimed_stop_condition}`"
    else:
        reason = f"decision allowed by evidence for `{claimed_stop_condition}`"

    return DecisionResult(
        True,
        intent,
        claimed_stop_condition,
        reason,
        required_next_action=state.get("next_required_action", ""),
        continuing_to=state.get("continuing_to", ""),
        state_path=str(state_path or ""),
    )


def write_decision_ledger(run_dir: Path, result: DecisionResult, run_id: str | None = None) -> Path:
    state_path = Path(result.state_path) if result.state_path else _state_for_run(run_dir, run_id)
    if run_id:
        ledger_path = run_dir / run_id / "decision-ledger.ndjson"
    elif state_path:
        ledger_path = state_path.parent / "decision-ledger.ndjson"
    else:
        ledger_path = run_dir / "decision-ledger.ndjson"

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    row = asdict(result) | {"timestamp": datetime.now(timezone.utc).isoformat()}
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
    return ledger_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version="agent-pipeline-codex 0.5.3")
    parser.add_argument(
        "--run-dir",
        default=str(_find_repo_root() / ".agent-runs"),
        help="Directory containing run subdirectories. Defaults to .agent-runs in this repo.",
    )
    parser.add_argument("--run", help="Run id under .agent-runs/.")
    parser.add_argument("--intent", required=True, choices=sorted(INTENTS))
    parser.add_argument("--claimed-stop-condition", required=True)
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--evidence-file", action="append", default=[])
    parser.add_argument("--write-ledger", action="store_true")
    parser.add_argument("--allow-no-active-run", action="store_true")
    args = parser.parse_args()

    result = evaluate_agent_decision(
        Path(args.run_dir),
        intent=args.intent,
        claimed_stop_condition=args.claimed_stop_condition,
        evidence=args.evidence,
        evidence_files=args.evidence_file,
        run_id=args.run,
        require_active_run=not args.allow_no_active_run,
    )

    ledger_path = None
    if args.write_ledger:
        ledger_path = write_decision_ledger(Path(args.run_dir), result, args.run)

    status = "ALLOW" if result.allowed else "BLOCK"
    print(f"agent_decision_gate: {status}")
    print(f"  intent: {result.intent}")
    print(f"  claimed_stop_condition: {result.claimed_stop_condition}")
    print(f"  reason: {result.reason}")
    if result.continuing_to:
        print(f"  continuing_to: {result.continuing_to}")
    if result.required_next_action:
        print(f"  required_next_action: {result.required_next_action}")
    if result.state_path:
        print(f"  state_path: {result.state_path}")
    if ledger_path:
        print(f"  ledger: {ledger_path}")

    return 0 if result.allowed else 1


if __name__ == "__main__":
    sys.exit(main())
