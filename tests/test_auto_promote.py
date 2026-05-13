# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from scripts.auto_promote import _check_tests, main


def write_green_run(run_dir: Path) -> None:
    run_dir.mkdir(parents=True)
    (run_dir / "verifier-report.md").write_text(
        "**Criteria: 2 total, 2 MET, 0 PARTIAL, 0 NOT MET, 0 NOT APPLICABLE**",
        encoding="utf-8",
    )
    (run_dir / "critic-report.md").write_text(
        "**Findings: 1 total, 0 blocker, 0 critical, 1 major, 0 minor**",
        encoding="utf-8",
    )
    (run_dir / "drift-report.md").write_text(
        "**Drift: 0 total, 0 blocker**",
        encoding="utf-8",
    )
    (run_dir / "policy-report.md").write_text(
        "POLICY: ALL CHECKS PASSED",
        encoding="utf-8",
    )
    (run_dir / "implementation-report.md").write_text(
        "pytest output: 12 passed, 0 failed",
        encoding="utf-8",
    )


def test_check_tests_rejects_mixed_pass_fail_output(tmp_path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "implementation-report.md").write_text(
        "pytest output: 5 passed, 2 failed",
        encoding="utf-8",
    )

    result = _check_tests(run_dir)

    assert not result.passed
    assert "non-zero failure count" in result.evidence


def test_auto_promote_writes_decision_for_full_green_artifact_set(tmp_path, monkeypatch) -> None:
    run_id = "green-run"
    run_base = tmp_path / ".agent-runs"
    write_green_run(run_base / run_id)
    monkeypatch.setattr("scripts.auto_promote.RUN_DIR_BASE", run_base)
    monkeypatch.setattr("sys.argv", ["auto_promote.py", "--run", run_id])

    assert main() == 0
    decision = (run_base / run_id / "manager-decision.md").read_text(encoding="utf-8")
    assert "**Decision: PROMOTE**" in decision

