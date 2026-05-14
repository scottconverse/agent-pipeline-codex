# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from scripts import auto_promote
from scripts.agent_decision_gate import evaluate_agent_decision
from scripts.check_decision_ledger import validate_ledger
from scripts.check_pipeline_control_loop import parse_control_state, validate_control_state
from scripts.final_response_gate import evaluate_final_response_gate
from scripts.show_run_status import summarize_run


def _write_green_artifacts(run_dir: Path) -> None:
    run_dir.mkdir(parents=True)
    (run_dir / "manifest.yaml").write_text(
        """
pipeline_run:
  goal: "Exercise the deterministic policy and control-loop fixture."
  expected_outputs:
    - "Auto-promote and control gates agree on the run state."
  definition_of_done: "The fixture contains enough artifacts to prove the deterministic gates work together without relying on an LLM role response."
  non_goals:
    - "No real source edits."
  rollback_plan: "Delete the temporary fixture."
  allowed_paths:
    - "scripts/"
  forbidden_paths:
    - "docs/"
""",
        encoding="utf-8",
    )
    (run_dir / "verifier-report.md").write_text(
        "**Criteria: 1 total, 1 MET, 0 PARTIAL, 0 NOT MET, 0 NOT APPLICABLE**",
        encoding="utf-8",
    )
    (run_dir / "critic-report.md").write_text(
        "**Findings: 0 total, 0 blocker, 0 critical, 0 major, 0 minor**",
        encoding="utf-8",
    )
    (run_dir / "drift-report.md").write_text("**Drift: 0 total, 0 blocker**", encoding="utf-8")
    (run_dir / "policy-report.md").write_text("POLICY: ALL CHECKS PASSED", encoding="utf-8")
    (run_dir / "implementation-report.md").write_text("pytest: 20 passed, 0 failed", encoding="utf-8")
    (run_dir / "active-control-state.md").write_text(
        "active_run: true\n"
        "current_stage: manager\n"
        "last_completed_gate: auto-promote\n"
        "stage_complete: true\n"
        "next_stage_authorized: true\n"
        "next_required_action: continue to next authorized slice\n"
        "continuing_to: next authorized slice\n"
        "stop_condition: none\n"
        "final_response_allowed: false\n",
        encoding="utf-8",
    )
    (run_dir / "run.log").write_text(
        "2026-05-13T00:00:00Z | manifest | COMPLETE | approved\n"
        "2026-05-13T00:01:00Z | manager | COMPLETE | auto-promoted\n",
        encoding="utf-8",
    )


def test_policy_control_fixture_blocks_final_response_until_stop_condition(tmp_path, monkeypatch) -> None:
    run_id = "fixture-run"
    run_base = tmp_path / ".agent-runs"
    run_dir = run_base / run_id
    _write_green_artifacts(run_dir)
    monkeypatch.setattr(auto_promote, "RUN_DIR_BASE", run_base)
    monkeypatch.setattr("sys.argv", ["auto_promote.py", "--run", run_id])

    assert auto_promote.main() == 0
    assert (run_dir / "manager-decision.md").exists()
    fields = parse_control_state((run_dir / "active-control-state.md").read_text(encoding="utf-8"))
    assert validate_control_state(fields) == []
    assert not evaluate_final_response_gate(run_base, require_active_run=True)[0].allowed

    decision = evaluate_agent_decision(
        run_base,
        intent="final_response",
        claimed_stop_condition="successful_ci",
        require_active_run=True,
    )
    assert not decision.allowed

    summary = "\n".join(summarize_run(run_dir))
    assert "current_stage: manager" in summary
    assert "next_required_action: continue to next authorized slice" in summary

    ledger = run_dir / "decision-ledger.ndjson"
    ledger.write_text(
        '{"allowed": false, "claimed_stop_condition": "successful_ci", '
        '"intent": "final_response", "reason": "blocked by active continuation", '
        '"schema_version": "1", "timestamp": "2026-05-13T00:00:00+00:00"}\n',
        encoding="utf-8",
    )
    assert validate_ledger(ledger) == []
