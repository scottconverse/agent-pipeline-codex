# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

from scripts.agent_decision_gate import evaluate_agent_decision, write_decision_ledger


def _write_state(run_dir: Path, run_id: str, **overrides: str) -> Path:
    state = {
        "active_run": "true",
        "current_stage": "post-push-ci",
        "last_completed_gate": "ci-cleanroom-e2e",
        "next_required_action": "continue the next authorized slice",
        "stop_condition": "none",
        "final_response_allowed": "false",
        "continuing_to": "slice gap audit",
    }
    state.update(overrides)
    path = run_dir / run_id / "active-control-state.md"
    path.parent.mkdir(parents=True)
    path.write_text("\n".join(f"{key}: {value}" for key, value in state.items()), encoding="utf-8")
    return path


def test_active_continuation_blocks_any_final_decision(tmp_path: Path) -> None:
    _write_state(tmp_path, "run-1")

    result = evaluate_agent_decision(
        tmp_path,
        intent="final_response",
        claimed_stop_condition="human_approval_gate",
        run_id="run-1",
    )

    assert result.allowed is False
    assert result.continuing_to == "slice gap audit"


def test_unverified_actions_budget_risk_cannot_skip_push(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        "run-1",
        stop_condition="human_approval_gate",
        final_response_allowed="true",
    )

    result = evaluate_agent_decision(
        tmp_path,
        intent="skip_push",
        claimed_stop_condition="unverified_actions_budget_risk",
        run_id="run-1",
    )

    assert result.allowed is False
    assert "not a valid stop condition" in result.reason


def test_valid_recorded_stop_allows_decision(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        "run-1",
        stop_condition="human_approval_gate",
        final_response_allowed="true",
    )

    result = evaluate_agent_decision(
        tmp_path,
        intent="final_response",
        claimed_stop_condition="human_approval_gate",
        run_id="run-1",
    )

    assert result.allowed is True


def test_claimed_blocker_requires_evidence_when_not_recorded(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        "run-1",
        stop_condition="human_approval_gate",
        final_response_allowed="true",
    )

    result = evaluate_agent_decision(
        tmp_path,
        intent="stop",
        claimed_stop_condition="credential_or_secret_required",
        run_id="run-1",
    )

    assert result.allowed is False
    assert "no evidence" in result.reason


def test_claimed_blocker_with_evidence_is_allowed(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        "run-1",
        stop_condition="human_approval_gate",
        final_response_allowed="true",
    )

    result = evaluate_agent_decision(
        tmp_path,
        intent="stop",
        claimed_stop_condition="credential_or_secret_required",
        evidence=["secret name required: GH_TOKEN_FOR_PRIVATE_REPO"],
        run_id="run-1",
    )

    assert result.allowed is True
    assert result.reason == "decision allowed by evidence for `credential_or_secret_required`"


def test_decision_ledger_records_blocked_decision(tmp_path: Path) -> None:
    _write_state(tmp_path, "run-1")
    result = evaluate_agent_decision(
        tmp_path,
        intent="final_response",
        claimed_stop_condition="human_approval_gate",
        run_id="run-1",
    )

    ledger = write_decision_ledger(tmp_path, result, run_id="run-1")

    row = json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])
    assert row["allowed"] is False
    assert row["continuing_to"] == "slice gap audit"
