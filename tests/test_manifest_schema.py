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


def test_unsupported_block_scalar_is_rejected(tmp_path) -> None:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        """
pipeline_run:
  goal: |
    Tighten manifest parser behavior for richer YAML syntax.
  expected_outputs:
    - "Unsupported YAML constructs fail loudly."
  definition_of_done: "The validator reports unsupported block scalar syntax clearly rather than silently parsing the wrong value."
  non_goals:
    - "No PyYAML dependency."
  rollback_plan: "Revert the parser validation change."
""",
        encoding="utf-8",
    )

    violations = _check(_read_manifest(manifest))

    assert any("block scalar" in item for item in violations)


def test_unsupported_anchor_and_alias_are_rejected(tmp_path) -> None:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        """
pipeline_run:
  goal: &goal "Tighten manifest parser behavior for aliases."
  expected_outputs:
    - *goal
  definition_of_done: "The validator reports anchor and alias syntax clearly rather than silently parsing the wrong value."
  non_goals:
    - "No PyYAML dependency."
  rollback_plan: "Revert the parser validation change."
""",
        encoding="utf-8",
    )

    violations = _check(_read_manifest(manifest))

    assert any("YAML anchors" in item for item in violations)
    assert any("YAML aliases" in item for item in violations)


def test_anchor_like_characters_inside_quotes_are_allowed(tmp_path) -> None:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        """
pipeline_run:
  goal: "Document the * wildcard and & symbol inside quoted text."
  expected_outputs:
    - "Quoted star and ampersand characters are preserved."
  definition_of_done: "The manifest parser only rejects YAML anchors and aliases outside quotes, while allowing ordinary prose with * and & characters."
  non_goals:
    - "No full YAML parser dependency."
  rollback_plan: "Revert the parser validation change."
  allowed_paths:
    - "scripts/"
  forbidden_paths:
    - "docs/"
""",
        encoding="utf-8",
    )

    violations = _check(_read_manifest(manifest))

    assert not any("YAML anchors" in item or "YAML aliases" in item for item in violations)

