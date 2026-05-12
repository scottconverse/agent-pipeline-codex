# SPDX-License-Identifier: Apache-2.0

from scripts.check_pipeline_control_loop import (
    unresolved_caveats,
    validate_control_state,
)


def _valid_state(**overrides: str) -> dict[str, str]:
    state = {
        "active_run": "true",
        "current_stage": "post-push-ci",
        "last_completed_gate": "ci-cleanroom-e2e",
        "next_required_action": "fix caveats",
        "stop_condition": "none",
        "final_response_allowed": "false",
        "continuing_to": "docs glyph cleanup",
    }
    state.update(overrides)
    return state


def test_none_stop_condition_requires_continuation() -> None:
    assert validate_control_state(_valid_state()) == []


def test_final_response_forbidden_without_stop_condition() -> None:
    violations = validate_control_state(_valid_state(final_response_allowed="true"))
    assert "`final_response_allowed` must be `false` when `stop_condition` is `none`" in violations


def test_green_ci_is_not_a_stop_condition() -> None:
    violations = validate_control_state(
        _valid_state(stop_condition="green_ci", final_response_allowed="true")
    )
    assert "`stop_condition` uses invalid stop condition `green_ci`" in violations


def test_push_is_not_a_stop_condition() -> None:
    violations = validate_control_state(
        _valid_state(stop_condition="successful_push", final_response_allowed="true")
    )
    assert "`stop_condition` uses invalid stop condition `successful_push`" in violations


def test_release_tag_after_gates_is_not_a_stop_condition() -> None:
    violations = validate_control_state(
        _valid_state(stop_condition="release_or_tag_after_gates_pass", final_response_allowed="true")
    )
    assert (
        "`stop_condition` uses invalid stop condition `release_or_tag_after_gates_pass`"
        in violations
    )


def test_valid_human_gate_allows_final_response() -> None:
    violations = validate_control_state(
        _valid_state(stop_condition="human_approval_gate", final_response_allowed="true")
    )
    assert violations == []


def test_open_caveats_are_blocking_unless_explicitly_deferred() -> None:
    text = """# Report

## Open Caveats / Release Risks

- Node.js 20 warning remains.
- INTENTIONAL DEFERRAL: bundle size tuning is scheduled for v0.7.
"""
    assert unresolved_caveats(text) == ["Node.js 20 warning remains."]
