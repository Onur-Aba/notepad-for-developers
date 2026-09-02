from pathlib import Path

from app.database import Database
from app.services.workspace_transfer import ExportOptions, ProjectTransferService


def test_tags_history_backlinks_and_global_search(tmp_path: Path) -> None:
    db = Database(tmp_path / "devnest.db")
    project = db.create_project("Alpha", "Searchable project")
    repo = db.upsert_repository(name="repo", full_name="acme/repo", default_branch="main")
    db.link_repository_to_project(project.id, repo.id, "main")
    note = db.create_note("Security notes", "", "token database plan", project.id)
    decision = db.create_decision(project.id, "Use SQLite", "accepted")
    db.set_tags("note", note.id, ["security", "backend"])
    db.set_tags("decision", decision.id, ["database"])
    link = db.add_resource_link(project.id, "decision", decision.id, repo.id, "file", "app/database.py")
    db.upsert_review_baseline("decision", decision.id, repo.id, "abc123", "main")

    assert any(kind == "note" and item_id == note.id for kind, item_id, *_ in db.global_search("security"))
    assert any(kind == "decision" and item_id == decision.id for kind, item_id, *_ in db.global_search("database"))
    assert any(kind == "code" and item_id == link.id for kind, item_id, *_ in db.global_search("database.py"))
    assert db.list_review_history("decision", decision.id)[0]["baseline_sha"] == "abc123"
    assert db.list_decision_history(decision.id)
    backlinks = db.resource_links_for_path(repo.id, "app/database.py")
    assert backlinks and backlinks[0][2] == "decision"
    db.close()


def test_project_export_import_roundtrip(tmp_path: Path) -> None:
    source_db = Database(tmp_path / "source.db")
    project = source_db.create_project("Transfer Me", "portable")
    repo = source_db.upsert_repository(name="repo", full_name="acme/repo", default_branch="main")
    source_db.link_repository_to_project(project.id, repo.id, "main")
    note = source_db.create_note("Runbook", "<p>hello</p>", "hello", project.id)
    decision = source_db.create_decision(project.id, "Keep local", "accepted")
    source_db.set_tags("decision", decision.id, ["backend"])
    source_db.add_resource_link(project.id, "decision", decision.id, repo.id, "file", "app/main.py")
    source_db.upsert_review_baseline("decision", decision.id, repo.id, "deadbeef", "main")
    source_db.save_diagram(note.id, {"items": [{"id": "n1", "text": "API"}], "edges": [], "paths": []})

    export_zip = tmp_path / "project.zip"
    ProjectTransferService(source_db).export_project(project.id, export_zip, ExportOptions(), as_zip=True)
    assert export_zip.is_file()
    source_db.close()

    target_db = Database(tmp_path / "target.db")
    imported_id = ProjectTransferService(target_db).import_project(export_zip, ExportOptions())
    imported = target_db.get_project(imported_id)
    assert imported and imported.name == "Transfer Me"
    assert any(n.title == "Runbook" for n in target_db.list_notes(project_id=imported_id))
    imported_decisions = target_db.list_decisions(imported_id)
    assert len(imported_decisions) == 1
    assert target_db.get_tags("decision", imported_decisions[0].id) == ["backend"]
    assert target_db.list_review_history("decision", imported_decisions[0].id)
    assert target_db.list_activity(imported_id)
    target_db.close()


def test_recent_items_are_project_scoped_and_deleted_notes_are_removed(tmp_path: Path) -> None:
    db = Database(tmp_path / "recent.db")
    p1 = db.create_project("One", "")
    p2 = db.create_project("Two", "")
    n1 = db.create_note("One note", "", "", p1.id)
    n2 = db.create_note("Two note", "", "", p2.id)

    db.touch_recent("note", n1.id, n1.title, p1.id)
    db.touch_recent("note", n2.id, n2.title, p2.id)

    assert [int(row["resource_id"]) for row in db.list_recent(project_id=p1.id)] == [n1.id]
    assert [int(row["resource_id"]) for row in db.list_recent(project_id=p2.id)] == [n2.id]

    db.soft_delete_note(n1.id)
    assert db.list_recent(project_id=p1.id) == []
    db.close()


def test_recent_items_hide_trashed_or_deleted_projects(tmp_path: Path) -> None:
    db = Database(tmp_path / "recent_projects.db")
    project = db.create_project("Temporary", "")
    note = db.create_note("Work item", "", "", project.id)

    db.touch_recent("project", project.id, project.name, project.id)
    db.touch_recent("note", note.id, note.title, project.id)
    assert len(db.list_recent(project_id=project.id)) == 2

    # Moving a project to Trash must remove the whole project from Continue
    # Working immediately, without requiring the stale recent rows to be deleted.
    db.trash_project(project.id)
    assert db.list_recent(project_id=project.id) == []
    assert all(int(row["project_id"]) != project.id for row in db.list_recent())

    # Restoring makes the still-valid history visible again. Permanent deletion
    # then keeps it hidden even though recent_items is intentionally non-cascading.
    db.restore_project(project.id)
    assert len(db.list_recent(project_id=project.id)) == 2
    db.trash_project(project.id)
    db.permanently_delete_project(project.id)
    assert db.list_recent(project_id=project.id) == []
    assert all(int(row["project_id"]) != project.id for row in db.list_recent())
    db.close()
