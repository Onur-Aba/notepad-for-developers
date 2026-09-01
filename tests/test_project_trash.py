from pathlib import Path

from app.database import Database


def test_project_trash_groups_contents_and_restores_previous_note_state(tmp_path: Path) -> None:
    db = Database(tmp_path / "devnest.db")
    project = db.create_project("Payment API", "Test workspace")
    active_note = db.create_note("Architecture notes", project_id=project.id)
    already_deleted = db.create_note("Old scratch note", project_id=project.id)
    db.soft_delete_note(already_deleted.id)
    decision = db.create_decision(project.id, "Use SQLite")
    db.save_diagram(active_note.id, {"items": [{"id": "n1", "type": "rect"}], "edges": [], "paths": []})
    repo = db.upsert_repository(name="payment-api", owner="acme", full_name="acme/payment-api")
    db.link_repository_to_project(project.id, repo.id, "main")
    db.add_resource_link(project.id, "decision", decision.id, repo.id, "file", "app/database.py")
    db.upsert_review_baseline("decision", decision.id, repo.id, "abc123", "main")

    db.trash_project(project.id)

    assert db.get_project(project.id) is None
    assert db.get_project(project.id, include_trashed=True) is not None
    assert [p.id for p in db.list_trashed_projects()] == [project.id]
    assert db.list_notes(project_id=project.id) == []
    # Notes moved with a project are grouped under that project and do not also
    # appear as standalone Trash entries.
    assert db.list_trash() == []

    details = db.project_trash_contents(project.id)
    assert "Architecture notes" in details["notes"]
    assert any("Use SQLite" in value for value in details["decisions"])
    assert "Architecture notes" in details["diagrams"]
    assert "acme/payment-api" in details["repositories"]
    assert details["resource_links"] == 1
    assert details["review_baselines"] == 1

    db.restore_project(project.id)

    assert db.get_project(project.id) is not None
    assert db.get_note(active_note.id) is not None
    # This note was already in Trash before the whole project was removed; the
    # project restore must not resurrect it.
    assert db.get_note(already_deleted.id) is None
    assert [item.id for item in db.list_trash()] == [already_deleted.id]
    assert db.get_decision(decision.id) is not None
    assert db.project_repository(project.id, repo.id) is not None


def test_permanent_project_delete_keeps_repository_cache_but_removes_workspace(tmp_path: Path) -> None:
    db = Database(tmp_path / "devnest.db")
    project = db.create_project("Disposable")
    note = db.create_note("Note", project_id=project.id)
    decision = db.create_decision(project.id, "Decision")
    repo = db.upsert_repository(name="repo", owner="acme", full_name="acme/repo")
    db.link_repository_to_project(project.id, repo.id, "main")
    db.add_resource_link(project.id, "note", note.id, repo.id, "repository", "")
    db.upsert_review_baseline("note", note.id, repo.id, "deadbeef", "main")

    db.trash_project(project.id)
    db.permanently_delete_project(project.id)

    assert db.get_project(project.id, include_trashed=True) is None
    assert db.get_note(note.id, include_deleted=True) is None
    assert db.get_decision(decision.id) is None
    assert db.list_resource_links(project_id=project.id) == []
    # Repository metadata may be shared by other projects, so deleting a DevNest
    # project must not delete the repository cache itself.
    assert db.get_repository(repo.id) is not None


def test_schema7_migration_adds_reversible_project_trash_columns(tmp_path: Path) -> None:
    path = tmp_path / "devnest.db"
    db = Database(path)
    assert db.connection.execute("PRAGMA user_version").fetchone()[0] == Database.SCHEMA_VERSION == 7
    project_columns = {row[1] for row in db.connection.execute("PRAGMA table_info(projects)").fetchall()}
    note_columns = {row[1] for row in db.connection.execute("PRAGMA table_info(notes)").fetchall()}
    assert "trashed_at" in project_columns
    assert "trashed_with_project_id" in note_columns
    assert "project_trash_was_deleted" in note_columns
