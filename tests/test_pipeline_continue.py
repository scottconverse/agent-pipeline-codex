# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from scripts.pipeline_continue import next_action


def _write_state(run_dir: Path, run_id: str, **overrides: str) -> None:
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


def test_pipeline_continue_prints_next_action(tmp_path: Path) -> None:
    _write_state(tmp_path, "run-1")

    code, message = next_action(tmp_path)

    assert code == 1
    assert "pipeline_continue: CONTINUE" in message
    assert "slice gap audit" in message


def test_pipeline_continue_allows_stop_for_valid_gate(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        "run-1",
        current_stage="manifest",
        stop_condition="human_approval_gate",
        final_response_allowed="true",
        continuing_to="none",
    )

    code, message = next_action(tmp_path)

    assert code == 0
    assert "pipeline_continue: STOP_ALLOWED" in message
    assert "human_approval_gate" in message


def test_pipeline_continue_rejects_stale_human_gate(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        "run-1",
        current_stage="execute",
        stop_condition="human_approval_gate",
        final_response_allowed="true",
        continuing_to="none",
    )

    code, message = next_action(tmp_path)

    assert code == 1
    assert "pipeline_continue: CONTINUE" in message
    assert "human_approval_gate is only valid" in message
