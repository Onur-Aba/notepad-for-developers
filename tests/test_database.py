from __future__ import annotations

from pathlib import Path

from app.database import Database


def test_database_crud_and_search(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    try:
        note = db.create_note("API Plan", "<p>Hello</p>", "Hello endpoint")
        loaded = db.get_note(note.id)
        assert loaded is not None
        assert loaded.title == "API Plan"

        db.update_note(note.id, "API Plan v2", "<p>Updated</p>", "Database Redis")
        loaded = db.get_note(note.id)
        assert loaded is not None
        assert loaded.title == "API Plan v2"
        assert loaded.content_plain == "Database Redis"
        assert [item.id for item in db.list_notes("redis")] == [note.id]
    finally:
        db.close()


def test_soft_delete_restore_and_permanent_delete_cascade(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    try:
        note = db.create_note("Disposable")
        db.save_diagram(note.id, {"items": [{"id": "n1"}], "edges": [], "paths": []})

        db.soft_delete_note(note.id)
        assert db.get_note(note.id) is None
        assert db.get_note(note.id, include_deleted=True) is not None
        assert [item.id for item in db.list_trash()] == [note.id]

        db.restore_note(note.id)
        assert db.get_note(note.id) is not None
        assert db.get_diagram(note.id)["items"] == [{"id": "n1"}]

        db.soft_delete_note(note.id)
        db.permanently_delete_note(note.id)
        assert db.get_note(note.id, include_deleted=True) is None
        count = db.connection.execute("SELECT COUNT(*) FROM diagrams WHERE note_id = ?", (note.id,)).fetchone()[0]
        assert count == 0
    finally:
        db.close()


def test_duplicate_copies_diagram(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    try:
        note = db.create_note("Original", "<p>Body</p>", "Body")
        diagram = {"items": [{"type": "node", "id": "a", "x": 1, "y": 2, "text": "API"}], "edges": [], "paths": []}
        db.save_diagram(note.id, diagram)
        copy = db.duplicate_note(note.id)
        assert copy.title == "Original Copy"
        assert copy.content_html == note.content_html
        assert db.get_diagram(copy.id) == diagram
    finally:
        db.close()


def test_empty_trash_returns_deleted_count(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    try:
        a = db.create_note("A")
        b = db.create_note("B")
        db.soft_delete_note(a.id)
        db.soft_delete_note(b.id)
        assert db.empty_trash() == 2
        assert db.list_trash() == []
    finally:
        db.close()


def test_repeated_note_updates_coalesce_activity_rows(tmp_path: Path) -> None:
    db = Database(tmp_path / "test.db")
    try:
        note = db.create_note("Autosave")
        db.update_note(note.id, "Autosave", "<p>a</p>", "a")
        db.update_note(note.id, "Autosave", "<p>ab</p>", "ab")
        count = db.connection.execute(
            "SELECT COUNT(*) FROM activity_events WHERE event_type='note_updated' AND resource_type='note' AND resource_id=?",
            (str(note.id),),
        ).fetchone()[0]
        assert count == 1
        summary = db.get_note_summary(note.id)
        assert summary is not None
        assert summary.preview == "ab"
    finally:
        db.close()
