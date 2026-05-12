"""Validate installable Codex skills are self-contained.

The GitHub skill installer copies each ``skills/<name>/`` directory into
``$CODEX_HOME/skills/<name>``. A skill that references repo-root files such as
``../../commands/...`` works in the source tree but breaks after installation.
This check verifies every installable skill only points at bundled references
inside its own folder.
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
BACKTICK = re.compile(r"`([^`]+)`")


def referenced_paths(text: str) -> list[str]:
    refs: list[str] = []
    for match in BACKTICK.finditer(text):
        value = match.group(1).strip()
        if value.startswith("references/") or value.startswith("references\\"):
            refs.append(value)
    return refs


def check_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")

    if "../" in text or "..\\" in text:
        errors.append(f"{skill_md}: contains parent-directory traversal")

    for ref in referenced_paths(text):
        target = skill_dir / Path(ref)
        if not target.exists():
            errors.append(f"{skill_md}: missing bundled reference {ref}")

    return errors


def check_installed_copy(skill_dir: Path) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="agent-pipeline-skill-install-") as tmp:
        install_root = Path(tmp) / "skills" / skill_dir.name
        shutil.copytree(skill_dir, install_root)
        return check_skill(install_root)


def main() -> int:
    errors: list[str] = []
    for skill_md in sorted(SKILLS.glob("*/SKILL.md")):
        skill_dir = skill_md.parent
        errors.extend(check_skill(skill_dir))
        errors.extend(check_installed_copy(skill_dir))

    if errors:
        print("SKILL-PACKAGING: FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("SKILL-PACKAGING: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
