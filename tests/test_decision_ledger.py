# SPDX-License-Identifier: Apache-2.0

from scripts.check_decision_ledger import validate_ledger


def test_decision_ledger_accepts_schema_v1_rows(tmp_path) -> None:
    ledger = tmp_path / "decision-ledger.ndjson"
    ledger.write_text(
        '{"allowed": true, "claimed_stop_condition": "user_explicitly_says_pause_or_stop", '
        '"intent": "pause", "reason": "user asked", "schema_version": "1", '
        '"timestamp": "2026-05-13T00:00:00+00:00"}\n',
        encoding="utf-8",
    )

    assert validate_ledger(ledger) == []


def test_decision_ledger_rejects_invalid_rows(tmp_path) -> None:
    ledger = tmp_path / "decision-ledger.ndjson"
    ledger.write_text('{"allowed": "yes"}\n', encoding="utf-8")

    violations = validate_ledger(ledger)

    assert any("`allowed` must be bool" in item for item in violations)
    assert any("`intent` must be str" in item for item in violations)
