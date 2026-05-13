# SPDX-License-Identifier: Apache-2.0

from scripts.check_manifest_schema import _check, _read_manifest


def test_hash_inside_quoted_manifest_value_is_not_treated_as_comment(tmp_path) -> None:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        """
pipeline_run:
  goal: "Fix issue #123 by tightening manifest parsing behavior"
  expected_outputs:
    - "Parser keeps hash characters inside quoted scalar values."
  definition_of_done: "The schema parser preserves quoted hash values, validates all required fields, and reports no truncation-related violations."
  non_goals:
    - "No full YAML parser dependency."
  rollback_plan: "Revert the parser helper change."
  allowed_paths:
    - "scripts/"
  forbidden_paths:
    - "docs/"
""",
        encoding="utf-8",
    )

    fields = _read_manifest(manifest)

    assert fields["goal"] == "Fix issue #123 by tightening manifest parsing behavior"
    assert _check(fields) == []


def test_forbidden_status_words_are_rejected() -> None:
    violations = _check(
        {
            "goal": "Make the release ready by changing enough files",
            "expected_outputs": ["One clear output."],
            "definition_of_done": "This long definition explains what evidence must be generated without leaving ambiguity for verifier or critic stages.",
            "non_goals": ["No release tagging."],
            "rollback_plan": "git revert",
        }
    )

    assert any("forbidden status word `ready`" in item for item in violations)


def test_broad_allowed_path_requires_forbidden_paths() -> None:
    violations = _check(
        {
            "goal": "Tighten project policy across a broad source tree",
            "expected_outputs": ["Policy script behavior is updated."],
            "definition_of_done": "The manifest explicitly bounds blast radius whenever a broad top-level directory is allowed for an implementation run.",
            "non_goals": ["No unrelated source edits."],
            "rollback_plan": "git revert",
            "allowed_paths": ["src/"],
            "forbidden_paths": [],
        }
    )

    assert any("broad top-level prefix" in item for item in violations)

