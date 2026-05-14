#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify the Codex plugin install surface, not just repository tests.

This script exists because repository tests and standalone skill copies can pass
while the Codex Desktop plugin registry still cannot see the plugin. Static
checks verify the expected local installation layout. The optional live check
starts a fresh ``codex exec`` process and proves the runtime context exposes the
plugin and all expected namespaced skills.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_JSON = ROOT / ".codex-plugin" / "plugin.json"
EXPECTED_PLUGIN = "agent-pipeline-codex"
EXPECTED_MARKETPLACE = "agent-pipeline-local"
EXPECTED_SKILLS = [
    "agent-pipeline",
    "audit-init",
    "new-run",
    "pipeline-init",
    "run-pipeline",
    "show-run-status",
    "validate-manifest",
]


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _has_utf8_bom(path: Path) -> bool:
    return path.read_bytes().startswith(b"\xef\xbb\xbf")


def _codex_home() -> Path:
    override = os.environ.get("CODEX_HOME")
    if override:
        return Path(override)
    return Path.home() / ".codex"


def plugin_version() -> str:
    return str(_load_json(PLUGIN_JSON)["version"])


def check_source_layout(root: Path) -> list[Check]:
    checks: list[Check] = []
    plugin_json = root / ".codex-plugin" / "plugin.json"
    if not plugin_json.exists():
        return [Check("source plugin.json", False, f"missing {plugin_json}")]

    metadata = _load_json(plugin_json)
    checks.append(
        Check(
            "source plugin.json has no BOM",
            not _has_utf8_bom(plugin_json),
            "no BOM" if not _has_utf8_bom(plugin_json) else "UTF-8 BOM present",
        )
    )
    checks.append(
        Check(
            "source plugin name",
            metadata.get("name") == EXPECTED_PLUGIN,
            f"name={metadata.get('name')!r}",
        )
    )
    checks.append(
        Check(
            "source plugin skills path",
            metadata.get("skills") == "./skills/",
            f"skills={metadata.get('skills')!r}",
        )
    )

    for skill in EXPECTED_SKILLS:
        skill_md = root / "skills" / skill / "SKILL.md"
        if not skill_md.exists():
            checks.append(Check(f"source skill {skill}", False, f"missing {skill_md}"))
            continue
        checks.append(
            Check(
                f"source skill {skill} has no BOM",
                not _has_utf8_bom(skill_md),
                "no BOM" if not _has_utf8_bom(skill_md) else "UTF-8 BOM present",
            )
        )
        text = skill_md.read_text(encoding="utf-8-sig")
        has_frontmatter = text.startswith("---\n") and "\n---\n" in text[4:]
        has_name = f"name: {skill}" in text or f'name: "{skill}"' in text
        checks.append(
            Check(
                f"source skill {skill}",
                has_frontmatter and has_name,
                "frontmatter present" if has_frontmatter and has_name else "invalid frontmatter",
            )
        )

    return checks


def check_installed_layout(codex_home: Path, root: Path, require_installed: bool) -> list[Check]:
    checks: list[Check] = []
    config_path = codex_home / "config.toml"
    plugin_key = f"{EXPECTED_PLUGIN}@{EXPECTED_MARKETPLACE}"
    version = plugin_version()

    if not config_path.exists():
        checks.append(Check("codex config", not require_installed, f"missing {config_path}"))
        return checks

    config = tomllib.loads(config_path.read_text(encoding="utf-8-sig"))
    plugin_config = config.get("plugins", {}).get(plugin_key)
    checks.append(
        Check(
            "plugin enabled in config",
            bool(plugin_config and plugin_config.get("enabled") is True),
            f"plugins.{plugin_key}={plugin_config!r}",
        )
    )

    marketplace_config = config.get("marketplaces", {}).get(EXPECTED_MARKETPLACE)
    checks.append(
        Check(
            "marketplace configured",
            bool(marketplace_config and marketplace_config.get("source_type") == "local"),
            f"marketplaces.{EXPECTED_MARKETPLACE}={marketplace_config!r}",
        )
    )

    marketplace_json = (
        codex_home
        / "local-marketplaces"
        / EXPECTED_MARKETPLACE
        / ".agents"
        / "plugins"
        / "marketplace.json"
    )
    if marketplace_json.exists():
        marketplace = _load_json(marketplace_json)
        names = [entry.get("name") for entry in marketplace.get("plugins", [])]
        checks.append(
            Check(
                "local marketplace lists plugin",
                EXPECTED_PLUGIN in names,
                f"plugins={names!r}",
            )
        )
    else:
        checks.append(Check("local marketplace lists plugin", False, f"missing {marketplace_json}"))

    installed = codex_home / "plugins" / "cache" / EXPECTED_MARKETPLACE / EXPECTED_PLUGIN / version
    installed_plugin_json = installed / ".codex-plugin" / "plugin.json"
    checks.append(
        Check(
            "installed cache version",
            installed_plugin_json.exists(),
            f"expected {installed_plugin_json}",
        )
    )
    if installed_plugin_json.exists():
        installed_metadata = _load_json(installed_plugin_json)
        checks.append(
            Check(
                "installed cache metadata",
                installed_metadata.get("name") == EXPECTED_PLUGIN
                and installed_metadata.get("version") == version,
                f"name={installed_metadata.get('name')!r} version={installed_metadata.get('version')!r}",
            )
        )

    source_metadata = _load_json(root / ".codex-plugin" / "plugin.json")
    if installed_plugin_json.exists():
        installed_metadata = _load_json(installed_plugin_json)
        checks.append(
            Check(
                "installed cache matches source version",
                installed_metadata.get("version") == source_metadata.get("version"),
                f"source={source_metadata.get('version')!r} installed={installed_metadata.get('version')!r}",
            )
        )

    for skill in EXPECTED_SKILLS:
        standalone_skill = codex_home / "skills" / skill / "SKILL.md"
        if not standalone_skill.exists():
            continue
        source_skill = root / "skills" / skill / "SKILL.md"
        standalone_text = standalone_skill.read_text(encoding="utf-8-sig")
        source_text = source_skill.read_text(encoding="utf-8-sig")
        checks.append(
            Check(
                f"standalone skill {skill} matches plugin source",
                standalone_text == source_text,
                f"{standalone_skill}",
            )
        )

    return checks


def run_live_check(root: Path, model: str, timeout: int) -> tuple[list[Check], str]:
    codex = shutil.which("codex")
    if not codex:
        return [Check("live codex executable", False, "codex not found on PATH")], ""

    expected_namespaced = [f"{EXPECTED_PLUGIN}:{skill}" for skill in EXPECTED_SKILLS]
    prompt = (
        "Do not read files or run tools. Inspect only your current system-provided "
        "Skills/Plugins context. Return exactly JSON with keys plugin_visible "
        "(boolean), namespaced_skills (array of strings), standalone_skills "
        "(array of strings), and plugin_loader_warning_visible (boolean). "
        f"The plugin name to check is {EXPECTED_PLUGIN}. Include only skills whose "
        f"name begins with {EXPECTED_PLUGIN}: in namespaced_skills."
    )

    with tempfile.TemporaryDirectory(prefix="agent-pipeline-install-acceptance-") as tmp:
        output_path = Path(tmp) / "last-message.json"
        cmd = [
            codex,
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "-C",
            str(root),
            "-m",
            model,
            "-o",
            str(output_path),
            prompt,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        combined = (proc.stdout or "") + (proc.stderr or "")

        checks = [Check("live codex exec exit", proc.returncode == 0, f"exit={proc.returncode}")]
        if not output_path.exists():
            checks.append(Check("live codex last message", False, f"missing {output_path}"))
            return checks, combined

        raw = output_path.read_text(encoding="utf-8").strip()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            checks.append(Check("live codex JSON", False, f"{exc}: {raw[:200]}"))
            return checks, combined

        namespaced = sorted(str(item) for item in payload.get("namespaced_skills", []))
        missing = [skill for skill in expected_namespaced if skill not in namespaced]
        checks.extend(
            [
                Check(
                    "live plugin visible",
                    bool(payload.get("plugin_visible")),
                    f"plugin_visible={payload.get('plugin_visible')!r}",
                ),
                Check(
                    "live namespaced skills complete",
                    not missing,
                    f"missing={missing!r} seen={namespaced!r}",
                ),
                Check(
                    "live plugin loader clean",
                    f"failed to load skill {EXPECTED_PLUGIN}" not in combined
                    and f"failed to load plugin: {EXPECTED_PLUGIN}" not in combined
                    and not bool(payload.get("plugin_loader_warning_visible")),
                    "no plugin-specific loader warning",
                ),
            ]
        )
        return checks, combined


def print_report(checks: list[Check]) -> None:
    for check in checks:
        status = "PASS" if check.ok else "FAIL"
        print(f"[{status}] {check.name}: {check.detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--codex-home", type=Path, default=_codex_home())
    parser.add_argument("--require-installed", action="store_true")
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--live", action="store_true", help="Launch a fresh codex exec process.")
    parser.add_argument("--model", default="gpt-5.4-mini")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    checks: list[Check] = []
    checks.extend(check_source_layout(args.repo_root))
    if not args.source_only:
        checks.extend(check_installed_layout(args.codex_home, args.repo_root, args.require_installed))
    if args.live:
        live_checks, live_output = run_live_check(args.repo_root, args.model, args.timeout)
        checks.extend(live_checks)
        if live_output:
            print("LIVE-CODEX-OUTPUT-BEGIN")
            print(live_output.rstrip())
            print("LIVE-CODEX-OUTPUT-END")

    print_report(checks)
    failed = [check for check in checks if not check.ok]
    if failed:
        print(f"PLUGIN-INSTALL-ACCEPTANCE: {len(failed)} CHECK(S) FAILED")
        return 1

    print("PLUGIN-INSTALL-ACCEPTANCE: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
