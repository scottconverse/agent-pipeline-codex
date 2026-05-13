# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
import subprocess

from scripts import check_actions_budget
from scripts.check_actions_budget import validate_workflow


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_good_pr_workflow_passes_cost_directives() -> None:
    text = """
name: CI
on:
  pull_request:
    branches: [main]
    paths:
      - "src/**"
      - "tests/**"
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - uses: actions/upload-artifact@v4
        with:
          name: report
          path: report.txt
          retention-days: 7
"""
    assert validate_workflow(Path(".github/workflows/ci.yml"), text) == []


def test_daily_cron_duplicate_trigger_and_missing_concurrency_fail() -> None:
    text = """
name: Expensive CI
on:
  schedule:
    - cron: "30 3 * * *"
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - run: playwright install
      - uses: actions/upload-artifact@v4
        with:
          name: e2e-report
          path: report
"""
    violations = validate_workflow(Path(".github/workflows/ci-e2e.yml"), text)
    assert "daily cron `30 3 * * *` is forbidden; weekly is the maximum default" in violations
    assert "missing required concurrency block with cancel-in-progress: true" in violations
    assert "duplicates pull_request main and push main for the same validation workflow" in violations
    assert "heavy workflow is missing paths filters" in violations
    assert "heavy workflow is missing cache coverage for expensive installs/downloads" in violations
    assert "upload-artifact step is missing retention-days: 7" in violations


def test_pr_runner_and_python_matrix_cost_rules_fail() -> None:
    text = """
name: Matrix
on:
  pull_request:
    branches: [main]
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    runs-on: ${{ matrix.os }}
    steps:
      - run: echo ok
  mac:
    runs-on: macos-latest
    steps:
      - run: echo ok
  win:
    runs-on: windows-latest
    steps:
      - run: echo ok
"""
    violations = validate_workflow(Path(".github/workflows/matrix.yml"), text)
    assert "macOS jobs are forbidden on PR-fired workflows without explicit Scott approval" in violations
    assert "Windows PR jobs require workflow-cost: windows-pr-justification evidence" in violations
    assert "PR CI must use one production Python version by default, currently Python 3.12" in violations


def test_pipeline_scaffold_contains_workflow_cost_policy() -> None:
    payload = REPO_ROOT / "skills" / "pipeline-init" / "references" / "pipeline-payload"
    run_all = (payload / "scripts" / "run_all.py").read_text(encoding="utf-8")
    ag = (payload / "pipelines" / "templates" / "AGENTS.md").read_text(encoding="utf-8")
    planner = (payload / "pipelines" / "roles" / "planner.md").read_text(encoding="utf-8")
    directives = (
        payload / "pipelines" / "templates" / "workflow-cost-directives.md"
    ).read_text(encoding="utf-8")

    assert "check_actions_budget" in run_all
    assert "GitHub Actions Workflow-Cost Directives" in ag
    assert "workflow-cost-directives.md" in ag
    assert "Never add a daily cron without explicit Scott approval" in directives
    assert "Every `upload-artifact` step must set `retention-days: 7`" in directives
    assert "Workflow-cost plan" in planner


def test_run_mode_includes_committed_workflow_diff(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(args, **kwargs):
        calls.append(args)
        if args[:2] == ["git", "status"]:
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        if args[:3] == ["git", "rev-parse", "--abbrev-ref"]:
            return subprocess.CompletedProcess(args, 0, stdout="origin/main\n", stderr="")
        if args[:3] == ["git", "diff", "--name-only"]:
            return subprocess.CompletedProcess(
                args, 0, stdout=".github/workflows/ci.yml\nREADME.md\n", stderr=""
            )
        raise AssertionError(args)

    monkeypatch.setattr(check_actions_budget.subprocess, "run", fake_run)

    paths, base = check_actions_budget._changed_workflows_for_run(None)

    assert base == "origin/main"
    assert [path.as_posix() for path in paths] == [
        (check_actions_budget.REPO_ROOT / ".github/workflows/ci.yml").as_posix()
    ]
