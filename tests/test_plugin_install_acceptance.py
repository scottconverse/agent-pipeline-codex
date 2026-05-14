# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
from pathlib import Path

from scripts.check_plugin_install_acceptance import (
    EXPECTED_MARKETPLACE,
    EXPECTED_PLUGIN,
    EXPECTED_SKILLS,
    check_installed_layout,
    check_source_layout,
    plugin_version,
    run_live_check,
)


ROOT = Path(__file__).resolve().parents[1]


def test_source_layout_has_all_expected_plugin_skills() -> None:
    failures = [check for check in check_source_layout(ROOT) if not check.ok]

    assert failures == []


def test_installed_layout_static_check_accepts_valid_codex_home(tmp_path: Path) -> None:
    version = plugin_version()
    codex_home = tmp_path / ".codex"
    marketplace = codex_home / "local-marketplaces" / EXPECTED_MARKETPLACE
    marketplace_json = marketplace / ".agents" / "plugins" / "marketplace.json"
    cache = codex_home / "plugins" / "cache" / EXPECTED_MARKETPLACE / EXPECTED_PLUGIN / version
    marketplace_json.parent.mkdir(parents=True)
    (cache / ".codex-plugin").mkdir(parents=True)

    (codex_home / "config.toml").write_text(
        f"""
[plugins."{EXPECTED_PLUGIN}@{EXPECTED_MARKETPLACE}"]
enabled = true

[marketplaces.{EXPECTED_MARKETPLACE}]
source_type = "local"
source = 'C:\\Users\\scott\\.codex\\local-marketplaces\\agent-pipeline-local'
""".strip(),
        encoding="utf-8",
    )
    marketplace_json.write_text(
        json.dumps(
            {
                "name": EXPECTED_MARKETPLACE,
                "plugins": [{"name": EXPECTED_PLUGIN, "source": {"source": "local"}}],
            }
        ),
        encoding="utf-8",
    )
    (cache / ".codex-plugin" / "plugin.json").write_text(
        json.dumps({"name": EXPECTED_PLUGIN, "version": version}),
        encoding="utf-8",
    )

    failures = [check for check in check_installed_layout(codex_home, ROOT, True) if not check.ok]

    assert failures == []


def test_installed_layout_static_check_fails_when_plugin_not_enabled(tmp_path: Path) -> None:
    codex_home = tmp_path / ".codex"
    codex_home.mkdir()
    (codex_home / "config.toml").write_text("", encoding="utf-8")

    failures = [check.name for check in check_installed_layout(codex_home, ROOT, True) if not check.ok]

    assert "plugin enabled in config" in failures


def test_installed_layout_flags_stale_standalone_skill_copy(tmp_path: Path) -> None:
    version = plugin_version()
    codex_home = tmp_path / ".codex"
    marketplace_json = (
        codex_home
        / "local-marketplaces"
        / EXPECTED_MARKETPLACE
        / ".agents"
        / "plugins"
        / "marketplace.json"
    )
    cache = codex_home / "plugins" / "cache" / EXPECTED_MARKETPLACE / EXPECTED_PLUGIN / version
    standalone = codex_home / "skills" / EXPECTED_SKILLS[0] / "SKILL.md"
    marketplace_json.parent.mkdir(parents=True)
    (cache / ".codex-plugin").mkdir(parents=True)
    standalone.parent.mkdir(parents=True)

    (codex_home / "config.toml").write_text(
        f"""
[plugins."{EXPECTED_PLUGIN}@{EXPECTED_MARKETPLACE}"]
enabled = true

[marketplaces.{EXPECTED_MARKETPLACE}]
source_type = "local"
source = 'C:\\Users\\scott\\.codex\\local-marketplaces\\agent-pipeline-local'
""".strip(),
        encoding="utf-8",
    )
    marketplace_json.write_text(
        json.dumps(
            {
                "name": EXPECTED_MARKETPLACE,
                "plugins": [{"name": EXPECTED_PLUGIN, "source": {"source": "local"}}],
            }
        ),
        encoding="utf-8",
    )
    (cache / ".codex-plugin" / "plugin.json").write_text(
        json.dumps({"name": EXPECTED_PLUGIN, "version": version}),
        encoding="utf-8",
    )
    standalone.write_text("stale standalone skill", encoding="utf-8")

    failures = [check.name for check in check_installed_layout(codex_home, ROOT, True) if not check.ok]

    assert f"standalone skill {EXPECTED_SKILLS[0]} matches plugin source" in failures


def test_live_check_retries_transient_missing_skill(monkeypatch) -> None:
    calls = 0

    def fake_which(name: str) -> str | None:
        assert name == "codex"
        return "codex"

    def fake_run(cmd, **kwargs):
        nonlocal calls
        calls += 1
        output_path = Path(cmd[cmd.index("-o") + 1])
        seen_skills = [f"{EXPECTED_PLUGIN}:{skill}" for skill in EXPECTED_SKILLS]
        if calls == 1:
            seen_skills.remove(f"{EXPECTED_PLUGIN}:pipeline-init")
        output_path.write_text(
            json.dumps(
                {
                    "plugin_visible": True,
                    "namespaced_skills": seen_skills,
                    "standalone_skills": [],
                    "plugin_loader_warning_visible": False,
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(cmd, 0, stdout=f"attempt {calls}", stderr="")

    monkeypatch.setattr("scripts.check_plugin_install_acceptance.shutil.which", fake_which)
    monkeypatch.setattr("scripts.check_plugin_install_acceptance.subprocess.run", fake_run)

    checks, transcript = run_live_check(ROOT, "test-model", 10, attempts=2)

    assert calls == 2
    assert [check for check in checks if not check.ok] == []
    assert "LIVE-CODEX-ATTEMPT 1 BEGIN" in transcript
    assert "LIVE-CODEX-ATTEMPT 2 BEGIN" in transcript


def test_live_check_fails_repeated_missing_skill(monkeypatch) -> None:
    def fake_which(name: str) -> str | None:
        assert name == "codex"
        return "codex"

    def fake_run(cmd, **kwargs):
        output_path = Path(cmd[cmd.index("-o") + 1])
        seen_skills = [f"{EXPECTED_PLUGIN}:{skill}" for skill in EXPECTED_SKILLS]
        seen_skills.remove(f"{EXPECTED_PLUGIN}:pipeline-init")
        output_path.write_text(
            json.dumps(
                {
                    "plugin_visible": True,
                    "namespaced_skills": seen_skills,
                    "standalone_skills": [],
                    "plugin_loader_warning_visible": False,
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(cmd, 0, stdout="missing pipeline-init", stderr="")

    monkeypatch.setattr("scripts.check_plugin_install_acceptance.shutil.which", fake_which)
    monkeypatch.setattr("scripts.check_plugin_install_acceptance.subprocess.run", fake_run)

    checks, _ = run_live_check(ROOT, "test-model", 10, attempts=2)

    failures = [check.name for check in checks if not check.ok]
    assert "live codex probe attempts" in failures
    assert "attempt 1: live namespaced skills complete" in failures
    assert "attempt 2: live namespaced skills complete" in failures


def test_live_check_fails_plugin_specific_loader_warning(monkeypatch) -> None:
    calls = 0

    def fake_which(name: str) -> str | None:
        assert name == "codex"
        return "codex"

    def fake_run(cmd, **kwargs):
        nonlocal calls
        calls += 1
        output_path = Path(cmd[cmd.index("-o") + 1])
        output_path.write_text(
            json.dumps(
                {
                    "plugin_visible": True,
                    "namespaced_skills": [f"{EXPECTED_PLUGIN}:{skill}" for skill in EXPECTED_SKILLS],
                    "standalone_skills": [],
                    "plugin_loader_warning_visible": calls == 1,
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(cmd, 0, stdout="all skills visible", stderr="")

    monkeypatch.setattr("scripts.check_plugin_install_acceptance.shutil.which", fake_which)
    monkeypatch.setattr("scripts.check_plugin_install_acceptance.subprocess.run", fake_run)

    checks, _ = run_live_check(ROOT, "test-model", 10, attempts=2)

    failures = [check.name for check in checks if not check.ok]
    assert "live codex probe attempts" in failures
    assert "live plugin loader clean" in failures
