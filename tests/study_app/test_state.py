import json

import pytest

from study_app.state import StateStore


def test_submit_creates_immutable_attempt_and_default_progress(tmp_path):
    store = StateStore(tmp_path)
    attempt = store.submit_attempt("bb84-bases", "bb84-eve-qber-01", "Mi respuesta", "none")

    assert store.load_progress()["current_module"] == "crypto-keys"
    assert store.get_attempt(attempt["attempt_id"])["body"] == "Mi respuesta"
    with pytest.raises(FileExistsError):
        store.create_attempt_file(attempt["attempt_id"], attempt)


def test_transition_requires_valid_state_change(tmp_path):
    store = StateStore(tmp_path)
    store.set_module_status("crypto-keys", "in_progress")
    assert store.set_module_status("crypto-keys", "submitted")["modules"]["crypto-keys"]["status"] == "submitted"
    with pytest.raises(ValueError, match="invalid module transition"):
        store.set_module_status("crypto-keys", "mastered")


def test_export_contains_active_module_and_attempt_count(tmp_path):
    store = StateStore(tmp_path)
    store.submit_attempt("bb84-bases", "bb84-eve-qber-01", "Texto", "none")

    export = store.export_summary()

    assert "# Resumen de progreso QKD" in export
    assert "bb84-bases" in export
    assert "Intentos registrados: 1" in export
    assert (tmp_path / "exports/progress-summary.md").read_text(encoding="utf-8") == export


def test_draft_is_replaced_and_json_is_valid(tmp_path):
    store = StateStore(tmp_path)
    store.save_draft({"module_id": "crypto-keys", "body": "uno"})
    store.save_draft({"module_id": "crypto-keys", "body": "dos"})

    assert store.load_draft()["body"] == "dos"
    json.loads((tmp_path / "session.json").read_text(encoding="utf-8"))


def test_record_error_deduplicates_by_module_and_concept(tmp_path):
    store = StateStore(tmp_path)
    store.record_error("bb84-bases", "confunde detectar con localizar", "yellow")
    store.record_error("bb84-bases", "confunde detectar con localizar", "yellow")

    items = store.load_errors()["items"]
    assert len(items) == 1
    assert items[0]["count"] == 2
