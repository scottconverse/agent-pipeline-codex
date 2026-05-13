#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run the release gate for the Agent Pipeline for Codex plugin.

This is the command that proves the install surface, not only the source tree.
Use ``--live`` before any plugin release or handoff that claims the slash/plugin
surface is working in Codex Desktop.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Step:
    name: str
    cmd: list[str]


def run_step(step: Step) -> tuple[bool, str]:
    proc = subprocess.run(step.cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, output.rstrip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Also launch a fresh codex exec process to prove the plugin runtime surface.",
    )
    parser.add_argument(
        "--skip-pytest",
        action="store_true",
        help="Skip pytest; intended only for narrow packaging debug loops.",
    )
    args = parser.parse_args()

    steps: list[Step] = []
    if not args.skip_pytest:
        steps.append(Step("pytest", [sys.executable, "-m", "pytest", "-q"]))
    steps.extend(
        [
            Step("skill packaging", [sys.executable, "scripts/check_skill_packaging.py"]),
            Step(
                "plugin install acceptance",
                [
                    sys.executable,
                    "scripts/check_plugin_install_acceptance.py",
                    "--require-installed",
                ],
            ),
        ]
    )
    if args.live:
        steps.append(
            Step(
                "live plugin install acceptance",
                [
                    sys.executable,
                    "scripts/check_plugin_install_acceptance.py",
                    "--require-installed",
                    "--live",
                ],
            )
        )

    results: list[tuple[str, bool, str]] = []
    for step in steps:
        ok, output = run_step(step)
        results.append((step.name, ok, output))

    print("=" * 72)
    print("Agent Pipeline plugin release verification")
    print("=" * 72)
    for name, ok, output in results:
        print(f"\n[{'PASS' if ok else 'FAIL'}] {name}")
        if output:
            for line in output.splitlines():
                print(f"  {line}")

    failed = [name for name, ok, _ in results if not ok]
    print()
    print("-" * 72)
    if failed:
        print(f"PLUGIN-RELEASE-VERIFY: {len(failed)} CHECK(S) FAILED")
        for name in failed:
            print(f"  - {name}")
        return 1

    print("PLUGIN-RELEASE-VERIFY: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
