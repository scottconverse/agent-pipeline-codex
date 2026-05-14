# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from scripts.final_response_gate import evaluate_final_response_gate


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
    path.write_text(
        "\n".join(f"{key}: {value}" for key, value in state.items()), encoding="utf-8"
    )
    return path


def test_gate_blocks_active_run_that_must_continue(tmp_path: Path) -> None:
    _write_state(tmp_path, "run-1")

    results = evaluate_final_response_gate(tmp_path, require_active_run=True)

    assert len(results) == 1
    assert results[0].allowed is False
    assert results[0].continuing_to == "slice gap audit"


def test_gate_allows_valid_stop_condition(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        "run-1",
        current_stage="manifest",
        stop_condition="human_approval_gate",
        final_response_allowed="true",
    )

    results = evaluate_final_response_gate(tmp_path, require_active_run=True)

    assert len(results) == 1
    assert results[0].allowed is True


def test_gate_fails_closed_when_active_run_missing(tmp_path: Path) -> None:
    results = evaluate_final_response_gate(tmp_path, require_active_run=True)

    assert len(results) == 1
    assert results[0].allowed is False
    assert "no active-control-state.md" in results[0].reason


def test_gate_blocks_if_any_active_run_must_continue(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        "run-1",
        current_stage="manifest",
        stop_condition="human_approval_gate",
        final_response_allowed="true",
    )
    _write_state(tmp_path, "run-2")

    results = evaluate_final_response_gate(tmp_path, require_active_run=True)

    assert any(result.allowed is False for result in results)
    assert any(result.continuing_to == "slice gap audit" for result in results)


def test_gate_blocks_human_gate_outside_real_human_stage(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        "run-1",
        current_stage="post-push-ci",
        stop_condition="human_approval_gate",
        final_response_allowed="true",
    )

    results = evaluate_final_response_gate(tmp_path, require_active_run=True)

    assert results[0].allowed is False
    assert "human_approval_gate is only valid" in results[0].reason
