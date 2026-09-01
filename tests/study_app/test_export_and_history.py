from study_app.state import StateStore


def test_history_preserves_attempt_order_and_deduplicates_errors(tmp_path):
    store = StateStore(tmp_path)
    first = store.submit_attempt("bb84-bases", "bb84-eve-qber-01", "primera", "none")
    second = store.submit_attempt("bb84-bases", "bb84-eve-qber-01", "segunda", "hint-1")
    store.record_error("bb84-bases", "confunde detectar con localizar", "yellow")
    store.record_error("bb84-bases", "confunde detectar con localizar", "yellow")

    assert [item["attempt_id"] for item in store.list_attempts("bb84-bases")] == [first["attempt_id"], second["attempt_id"]]
    assert len(store.load_errors()["items"]) == 1


def test_defense_export_has_30_plus_15_structure(tmp_path):
    store = StateStore(tmp_path)
    export = store.export_summary()

    assert "30 minutos" in export
    assert "15 minutos" in export


def test_backup_contains_dynamic_state_and_import_restores_draft(tmp_path):
    store = StateStore(tmp_path)
    store.save_draft({"module_id": "bb84-bases", "body": "borrador"})
    backup = store.create_backup()

    assert backup["schema_version"] == 1
    assert backup["draft"]["body"] == "borrador"

    other = StateStore(tmp_path / "other")
    other.import_draft(backup)
    assert other.load_draft()["body"] == "borrador"
