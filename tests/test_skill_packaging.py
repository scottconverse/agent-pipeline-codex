# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from scripts.check_skill_packaging import check_skill


ROOT = Path(__file__).resolve().parents[1]


def test_all_installable_skills_are_self_contained() -> None:
    errors: list[str] = []
    for skill_md in sorted((ROOT / "skills").glob("*/SKILL.md")):
        errors.extend(check_skill(skill_md.parent))

    assert errors == []
