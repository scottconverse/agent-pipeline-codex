# SPDX-License-Identifier: Apache-2.0

from scripts.policy_utils import find_repo_root, strip_yaml_comment


def test_strip_yaml_comment_preserves_hash_inside_quotes() -> None:
    assert strip_yaml_comment('goal: "ship #123 safely" # comment') == 'goal: "ship #123 safely"'
    assert strip_yaml_comment("goal: 'ship #123 safely' # comment") == "goal: 'ship #123 safely'"


def test_find_repo_root_handles_installed_policy_layout(tmp_path) -> None:
    repo = tmp_path / "project"
    script = repo / "scripts" / "policy" / "check_example.py"
    script.parent.mkdir(parents=True)
    script.write_text("# placeholder", encoding="utf-8")

    assert find_repo_root(str(script)) == repo


def test_find_repo_root_falls_back_to_source_layout_parent(tmp_path) -> None:
    repo = tmp_path / "plugin"
    script = repo / "scripts" / "check_example.py"
    script.parent.mkdir(parents=True)
    script.write_text("# placeholder", encoding="utf-8")

    assert find_repo_root(str(script)) == repo
