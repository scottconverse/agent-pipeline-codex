# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import subprocess
import sys

from scripts import verify_plugin_release


def test_release_verifier_includes_live_install_gate_when_requested(monkeypatch) -> None:
    commands: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        commands.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["verify_plugin_release.py", "--live"])

    assert verify_plugin_release.main() == 0

    assert [sys.executable, "-m", "pytest", "-q"] in commands
    assert [sys.executable, "scripts/check_skill_packaging.py"] in commands
    assert [
        sys.executable,
        "scripts/check_plugin_install_acceptance.py",
        "--require-installed",
    ] in commands
    assert [
        sys.executable,
        "scripts/check_plugin_install_acceptance.py",
        "--require-installed",
        "--live",
    ] in commands


def test_release_verifier_fails_when_any_gate_fails(monkeypatch) -> None:
    def fake_run(cmd, **kwargs):
        code = 1 if any(str(part).endswith("check_skill_packaging.py") for part in cmd) else 0
        return subprocess.CompletedProcess(cmd, code, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["verify_plugin_release.py"])

    assert verify_plugin_release.main() == 1


def test_release_verifier_source_only_skips_installed_cache_requirement(monkeypatch) -> None:
    commands: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        commands.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["verify_plugin_release.py", "--source-only"])

    assert verify_plugin_release.main() == 0
    assert [
        sys.executable,
        "scripts/check_plugin_install_acceptance.py",
        "--source-only",
    ] in commands
