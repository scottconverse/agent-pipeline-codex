#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Fail closed when an authorized Agent Pipeline run must continue.

This is the executable pre-final gate. Unlike
``check_pipeline_control_loop.py --run <run-id>``, this script discovers active
control-state files on its own and blocks a final response whenever any active
run records ``final_response_allowed: false``.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from scripts.policy_utils import find_repo_root
    from scripts.check_pipeline_control_loop import parse_control_state, validate_control_state
except ModuleNotFoundError:  # pragma: no cover - direct script execution from scripts/
    from policy_utils import find_repo_root
    from check_pipeline_control_loop import parse_control_state, validate_control_state


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    reason: str
    state_path: Path | None = None
    next_required_action: str = ""
    continuing_to: str = ""


def discover_state_files(run_dir: Path) -> list[Path]:
    if not run_dir.exists():
        return []
    return sorted(run_dir.glob("*/active-control-state.md"))


def evaluate_state_file(state_path: Path) -> GateResult:
    fields = parse_control_state(state_path.read_text(encoding="utf-8-sig"))
    violations = validate_control_state(fields)
    if violations:
        return GateResult(
            allowed=False,
            reason="control-state validation failed: " + "; ".join(violations),
            state_path=state_path,
        )

    if fields.get("active_run", "").lower() != "true":
        return GateResult(allowed=True, reason="inactive run", state_path=state_path)

    final_allowed = fields.get("final_response_allowed", "").lower()
    stop_condition = fields.get("stop_condition", "")
    next_required_action = fields.get("next_required_action", "")
    continuing_to = fields.get("continuing_to", "")

    if final_allowed == "false":
        return GateResult(
            allowed=False,
            reason=f"active run must continue; stop_condition={stop_condition}",
            state_path=state_path,
            next_required_action=next_required_action,
            continuing_to=continuing_to,
        )

    return GateResult(
        allowed=True,
        reason=f"valid stop condition recorded: {stop_condition}",
        state_path=state_path,
        next_required_action=next_required_action,
        continuing_to=continuing_to,
    )


def evaluate_final_response_gate(run_dir: Path, require_active_run: bool = False) -> list[GateResult]:
    states = discover_state_files(run_dir)
    if not states:
        if require_active_run:
            return [
                GateResult(
                    allowed=False,
                    reason=f"no active-control-state.md files found under {run_dir}",
                )
            ]
        return [GateResult(allowed=True, reason="no pipeline control state found")]

    results = [evaluate_state_file(path) for path in states]
    active_results = [
        result
        for result in results
        if result.state_path
        and parse_control_state(result.state_path.read_text(encoding="utf-8-sig")).get(
            "active_run", ""
        ).lower()
        == "true"
    ]

    if require_active_run and not active_results:
        return [
            GateResult(
                allowed=False,
                reason=f"no active run found in {run_dir}",
            )
        ]

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version="agent-pipeline-codex 0.5.6")
    parser.add_argument(
        "--run-dir",
        default=str(find_repo_root(__file__) / ".agent-runs"),
        help="Directory containing run subdirectories. Defaults to .agent-runs in this repo.",
    )
    parser.add_argument(
        "--require-active-run",
        action="store_true",
        help="Fail if no active pipeline run is found.",
    )
    args = parser.parse_args()

    results = evaluate_final_response_gate(Path(args.run_dir), args.require_active_run)
    blocked = [result for result in results if not result.allowed]

    if blocked:
        print("final_response_gate: BLOCK")
        for result in blocked:
            location = f" ({result.state_path})" if result.state_path else ""
            print(f"  - {result.reason}{location}")
            if result.continuing_to:
                print(f"    continuing_to: {result.continuing_to}")
            if result.next_required_action:
                print(f"    next_required_action: {result.next_required_action}")
        return 1

    print("final_response_gate: ALLOW")
    for result in results:
        location = f" ({result.state_path})" if result.state_path else ""
        print(f"  - {result.reason}{location}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
