from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from app.database import Database, DatabaseError, utc_now_iso


@dataclass(slots=True)
class ExportOptions:
    notes: bool = True
    decisions: bool = True
    architecture: bool = True
    repositories: bool = True
    links: bool = True
    review_history: bool = True
    tags: bool = True
    activity: bool = True

    def as_dict(self) -> dict[str, bool]:
        return {name: bool(getattr(self, name)) for name in self.__dataclass_fields__}


class BackupManager:
    def __init__(self, database: Database, backup_dir: Path) -> None:
        self.database = database
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, label: str = "manual") -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe = "".join(ch for ch in label if ch.isalnum() or ch in {"-", "_"}) or "manual"
        path = self.backup_dir / f"devnest-{safe}-{stamp}.db"
        destination = sqlite3.connect(path)
        try:
            self.database.connection.backup(destination)
        finally:
            destination.close()
        return path

    def list_backups(self) -> list[Path]:
        return sorted(self.backup_dir.glob("devnest-*.db"), key=lambda p: p.stat().st_mtime, reverse=True)

    def restore_backup(self, path: Path) -> None:
        path = Path(path)
        if not path.is_file():
            raise DatabaseError("Backup file does not exist.")
        self.create_backup("before-restore")
        source = sqlite3.connect(path)
        try:
            source.backup(self.database.connection)
        except sqlite3.Error as exc:
            raise DatabaseError(f"Backup could not be restored: {exc}") from exc
        finally:
            source.close()
        self.database.connection.row_factory = sqlite3.Row
        self.database.connection.execute("PRAGMA foreign_keys = ON")
        self.database._migrate()


class ProjectTransferService:
    FORMAT_VERSION = 1

    def __init__(self, database: Database) -> None:
        self.database = database

    def _resource_links_payload(self, project_id: int) -> list[dict[str, object]]:
        return [
            {
                "id": link.id,
                "project_id": link.project_id,
                "resource_type": link.resource_type,
                "resource_id": link.resource_id,
                "resource_parent_id": link.resource_parent_id,
                "repository_id": link.repository_id,
                "target_type": link.target_type,
                "target_value": link.target_value,
                "github_node_id": link.github_node_id,
                "metadata": link.metadata,
                "created_at": link.created_at,
            }
            for link in self.database.list_resource_links(project_id=project_id)
        ]

    def build_manifest(self, project_id: int, options: ExportOptions) -> dict[str, object]:
        project = self.database.get_project(project_id)
        if project is None:
            raise DatabaseError("Project not found.")
        decision_note_ids = {d.note_id for d in self.database.list_decisions(project_id)}
        notes = []
        if options.notes:
            for note in self.database.list_notes(project_id=project_id):
                if note.id in decision_note_ids:
                    continue
                full = self.database.get_note(note.id)
                if full:
                    notes.append({
                        "id": full.id,
                        "title": full.title,
                        "content_html": full.content_html,
                        "content_plain": full.content_plain,
                        "created_at": full.created_at,
                        "updated_at": full.updated_at,
                        "favorite": self.database.is_favorite("note", full.id),
                        "tags": self.database.get_tags("note", full.id) if options.tags else [],
                    })

        decisions = []
        if options.decisions:
            for d in self.database.list_decisions(project_id):
                decisions.append({
                    "id": d.id,
                    "note_id": d.note_id,
                    "decision_key": d.decision_key,
                    "status": d.status,
                    "title": d.title,
                    "content_html": d.content_html,
                    "content_plain": d.content_plain,
                    "created_at": d.created_at,
                    "updated_at": d.updated_at,
                    "favorite": self.database.is_favorite("decision", d.id),
                    "tags": self.database.get_tags("decision", d.id) if options.tags else [],
                    "history": [dict(r) for r in self.database.list_decision_history(d.id)] if options.review_history else [],
                })

        architectures = []
        if options.architecture:
            rows = self.database.connection.execute(
                """SELECT dg.note_id,dg.data_json,dg.updated_at,n.title FROM diagrams dg
                   JOIN notes n ON n.id=dg.note_id WHERE n.project_id=?""", (project_id,)
            ).fetchall()
            for row in rows:
                try:
                    data = json.loads(str(row["data_json"] or "{}"))
                except json.JSONDecodeError:
                    data = {}
                architectures.append({"note_id": int(row["note_id"]), "title": str(row["title"]), "data": data, "updated_at": str(row["updated_at"])})

        repositories = []
        if options.repositories:
            for r in self.database.list_repositories(project_id):
                mapping = self.database.project_repository(project_id, r.id)
                repositories.append({
                    "id": r.id,
                    "github_repo_id": r.github_repo_id,
                    "github_node_id": r.github_node_id,
                    "owner": r.owner,
                    "name": r.name,
                    "full_name": r.full_name,
                    "html_url": r.html_url,
                    "clone_url": r.clone_url,
                    "default_branch": r.default_branch,
                    "is_private": r.is_private,
                    "installation_id": r.installation_id,
                    "local_path": r.local_path,
                    "local_git_root": r.local_git_root,
                    "remote_name": r.remote_name,
                    "language": r.language,
                    "description": r.description,
                    "last_pushed_at": r.last_pushed_at,
                    "github_access_state": r.github_access_state,
                    "monitored_branch": mapping.monitored_branch if mapping else None,
                    "favorite": self.database.is_favorite("repository", r.id),
                })

        payload: dict[str, object] = {
            "format": "DevNestProject",
            "format_version": self.FORMAT_VERSION,
            "exported_at": utc_now_iso(),
            "options": options.as_dict(),
            "project": {
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
                "favorite": self.database.is_favorite("project", project.id),
            },
            "notes": notes,
            "decisions": decisions,
            "architecture": architectures,
            "repositories": repositories,
            "resource_links": [
                raw for raw in self._resource_links_payload(project_id)
                if options.links and options.repositories and (
                    (raw["resource_type"] == "note" and options.notes)
                    or (raw["resource_type"] == "decision" and options.decisions)
                    or (raw["resource_type"] == "diagram_item" and options.architecture)
                )
            ],
            "review_history": [
                dict(r) for r in self.database.connection.execute(
                    "SELECT * FROM review_history WHERE project_id=? ORDER BY reviewed_at", (project_id,)
                ).fetchall()
                if options.review_history and options.repositories and (
                    (str(r["resource_type"]) == "note" and options.notes)
                    or (str(r["resource_type"]) == "decision" and options.decisions)
                    or (str(r["resource_type"]) == "diagram_item" and options.architecture)
                )
            ],
            "activity": [dict(r) for r in reversed(self.database.list_activity(project_id, limit=5000))] if options.activity else [],
        }
        return payload

    @staticmethod
    def _safe_name(value: str) -> str:
        cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", ".", " "} else "_" for ch in value).strip()
        return cleaned or "item"

    def export_project(self, project_id: int, destination: Path, options: ExportOptions, *, as_zip: bool = True) -> Path:
        manifest = self.build_manifest(project_id, options)
        destination = Path(destination)
        project_name = str((manifest.get("project") or {}).get("name") or "project")
        with tempfile.TemporaryDirectory(prefix="devnest-export-") as tmp:
            root = Path(tmp) / self._safe_name(project_name)
            root.mkdir(parents=True, exist_ok=True)
            (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            if options.notes:
                note_dir = root / "Notes"; note_dir.mkdir(exist_ok=True)
                for note in manifest.get("notes", []):
                    title = str(note.get("title") or "Note")
                    body = str(note.get("content_plain") or "")
                    tags = note.get("tags") or []
                    front = f"# {title}\n\n" + (("Tags: " + ", ".join(tags) + "\n\n") if tags else "")
                    (note_dir / f"{int(note['id']):04d}-{self._safe_name(title)}.md").write_text(front + body, encoding="utf-8")
            if options.decisions:
                dec_dir = root / "Decisions"; dec_dir.mkdir(exist_ok=True)
                for dec in manifest.get("decisions", []):
                    title = str(dec.get("title") or "Decision")
                    head = f"# {dec.get('decision_key')} — {title}\n\nStatus: {dec.get('status')}\n"
                    tags = dec.get("tags") or []
                    if tags:
                        head += "Tags: " + ", ".join(tags) + "\n"
                    (dec_dir / f"{dec.get('decision_key')}-{self._safe_name(title)}.md").write_text(head + "\n" + str(dec.get("content_plain") or ""), encoding="utf-8")
            if options.architecture:
                arch_dir = root / "Architecture"; arch_dir.mkdir(exist_ok=True)
                for arch in manifest.get("architecture", []):
                    name = f"{int(arch['note_id']):04d}-{self._safe_name(str(arch.get('title') or 'Architecture'))}.json"
                    (arch_dir / name).write_text(json.dumps(arch.get("data") or {}, ensure_ascii=False, indent=2), encoding="utf-8")
            if as_zip:
                if destination.suffix.lower() != ".zip":
                    destination = destination.with_suffix(".zip")
                destination.parent.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                    for file in root.rglob("*"):
                        if file.is_file():
                            zf.write(file, file.relative_to(root.parent))
            else:
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.copytree(root, destination)
        return destination

    def read_manifest(self, source: Path) -> dict[str, object]:
        source = Path(source)
        if source.is_dir():
            manifest_path = source / "manifest.json"
            if not manifest_path.exists():
                candidates = list(source.glob("*/manifest.json"))
                manifest_path = candidates[0] if candidates else manifest_path
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        else:
            with zipfile.ZipFile(source) as zf:
                names = [n for n in zf.namelist() if n.endswith("manifest.json")]
                if not names:
                    raise DatabaseError("This ZIP does not contain a DevNest manifest.")
                data = json.loads(zf.read(names[0]).decode("utf-8"))
        if data.get("format") != "DevNestProject":
            raise DatabaseError("This is not a DevNest project export.")
        return data

    def import_project(self, source: Path, options: ExportOptions) -> int:
        manifest = self.read_manifest(source)
        project_meta = manifest.get("project") or {}
        project = self.database.create_project(str(project_meta.get("name") or "Imported Project"), str(project_meta.get("description") or ""))
        project_id = project.id
        with self.database.connection:
            self.database.connection.execute(
                "UPDATE projects SET created_at=?,updated_at=? WHERE id=?",
                (str(project_meta.get("created_at") or project.created_at), str(project_meta.get("updated_at") or project.updated_at), project_id),
            )
        if bool(project_meta.get("favorite")):
            self.database.set_favorite("project", project_id, True, project_id)
        repo_map: dict[int, int] = {}
        note_map: dict[int, int] = {}
        decision_map: dict[int, int] = {}

        if options.repositories:
            for raw in manifest.get("repositories", []):
                repo = self.database.upsert_repository(
                    name=str(raw.get("name") or "repository"), github_repo_id=raw.get("github_repo_id"), github_node_id=raw.get("github_node_id"),
                    owner=raw.get("owner"), full_name=raw.get("full_name"), html_url=raw.get("html_url"), clone_url=raw.get("clone_url"),
                    default_branch=raw.get("default_branch"), is_private=bool(raw.get("is_private")), installation_id=raw.get("installation_id"),
                    local_path=raw.get("local_path"), local_git_root=raw.get("local_git_root"), remote_name=raw.get("remote_name"), language=raw.get("language"),
                    description=raw.get("description"), last_pushed_at=raw.get("last_pushed_at"), github_access_state=str(raw.get("github_access_state") or "unknown"),
                )
                old_id = int(raw.get("id") or 0)
                repo_map[old_id] = repo.id
                self.database.link_repository_to_project(project_id, repo.id, raw.get("monitored_branch"))
                if bool(raw.get("favorite")):
                    self.database.set_favorite("repository", repo.id, True, project_id)

        if options.notes:
            for raw in manifest.get("notes", []):
                note = self.database.create_note(str(raw.get("title") or "Untitled Note"), str(raw.get("content_html") or ""), str(raw.get("content_plain") or ""), project_id)
                note_map[int(raw.get("id") or 0)] = note.id
                with self.database.connection:
                    self.database.connection.execute(
                        "UPDATE notes SET created_at=?,updated_at=? WHERE id=?",
                        (str(raw.get("created_at") or note.created_at), str(raw.get("updated_at") or note.updated_at), note.id),
                    )
                if bool(raw.get("favorite")):
                    self.database.set_favorite("note", note.id, True, project_id)
                if options.tags:
                    self.database.set_tags("note", note.id, raw.get("tags") or [])

        if options.decisions:
            for raw in manifest.get("decisions", []):
                d = self.database.create_decision(project_id, str(raw.get("title") or "Untitled Decision"), str(raw.get("status") or "proposed"))
                self.database.update_decision(d.id, str(raw.get("title") or d.title), str(raw.get("content_html") or ""), str(raw.get("content_plain") or ""), str(raw.get("status") or "proposed"))
                desired_key = str(raw.get("decision_key") or "")
                if desired_key:
                    try:
                        with self.database.connection:
                            self.database.connection.execute("UPDATE decisions SET decision_key=? WHERE id=?", (desired_key, d.id))
                    except sqlite3.IntegrityError:
                        pass
                old_decision_id = int(raw.get("id") or 0)
                decision_map[old_decision_id] = d.id
                old_note_id = int(raw.get("note_id") or 0)
                if old_note_id:
                    note_map[old_note_id] = d.note_id
                with self.database.connection:
                    created_at = str(raw.get("created_at") or d.created_at)
                    updated_at = str(raw.get("updated_at") or d.updated_at)
                    self.database.connection.execute(
                        "UPDATE decisions SET created_at=?,updated_at=? WHERE id=?", (created_at, updated_at, d.id)
                    )
                    self.database.connection.execute(
                        "UPDATE notes SET created_at=?,updated_at=? WHERE id=?", (created_at, updated_at, d.note_id)
                    )
                if bool(raw.get("favorite")):
                    self.database.set_favorite("decision", d.id, True, project_id)
                if options.tags:
                    self.database.set_tags("decision", d.id, raw.get("tags") or [])

        if options.review_history and options.decisions:
            with self.database.connection:
                for raw in manifest.get("decisions", []):
                    new_decision_id = decision_map.get(int(raw.get("id") or 0))
                    if not new_decision_id:
                        continue
                    self.database.connection.execute("DELETE FROM decision_history WHERE decision_id=?", (new_decision_id,))
                    for history in reversed(list(raw.get("history") or [])):
                        self.database.connection.execute(
                            "INSERT INTO decision_history(decision_id,event_type,title,detail,metadata_json,created_at) VALUES (?,?,?,?,?,?)",
                            (new_decision_id, str(history.get("event_type") or "imported"), str(history.get("title") or ""),
                             str(history.get("detail") or ""), str(history.get("metadata_json") or "{}"),
                             str(history.get("created_at") or utc_now_iso())),
                        )

        if options.architecture:
            for raw in manifest.get("architecture", []):
                old_note_id = int(raw.get("note_id") or 0)
                new_note_id = note_map.get(old_note_id)
                if not new_note_id:
                    backing = self.database.create_note(str(raw.get("title") or "Architecture"), "", "", project_id)
                    new_note_id = backing.id
                    note_map[old_note_id] = new_note_id
                self.database.save_diagram(new_note_id, raw.get("data") or {})
                if raw.get("updated_at"):
                    with self.database.connection:
                        self.database.connection.execute(
                            "UPDATE diagrams SET updated_at=? WHERE note_id=?", (str(raw.get("updated_at")), new_note_id)
                        )

        if options.links:
            for raw in manifest.get("resource_links", []):
                old_repo = int(raw.get("repository_id") or 0)
                new_repo = repo_map.get(old_repo)
                if not new_repo:
                    continue
                resource_type = str(raw.get("resource_type") or "")
                old_resource_id = int(raw.get("resource_id") or 0) if str(raw.get("resource_id") or "").isdigit() else raw.get("resource_id")
                resource_id = decision_map.get(old_resource_id, old_resource_id) if resource_type == "decision" else note_map.get(old_resource_id, old_resource_id) if resource_type == "note" else raw.get("resource_id")
                parent = raw.get("resource_parent_id")
                if resource_type == "diagram_item" and str(parent or "").isdigit():
                    parent = note_map.get(int(parent), parent)
                try:
                    self.database.add_resource_link(project_id, resource_type, resource_id, new_repo, str(raw.get("target_type") or "repository"), str(raw.get("target_value") or ""), resource_parent_id=parent, github_node_id=raw.get("github_node_id"), metadata=raw.get("metadata") or {})
                except DatabaseError:
                    continue

        if options.review_history:
            latest: dict[tuple[str, str, str, int], tuple[str, str | None, str]] = {}
            with self.database.connection:
                for raw in manifest.get("review_history", []):
                    old_repo = int(raw.get("repository_id") or 0)
                    new_repo = repo_map.get(old_repo)
                    if not new_repo:
                        continue
                    resource_type = str(raw.get("resource_type") or "")
                    raw_id = str(raw.get("resource_id") or "")
                    if resource_type == "decision" and raw_id.isdigit():
                        resource_id = str(decision_map.get(int(raw_id), raw_id))
                    elif resource_type == "note" and raw_id.isdigit():
                        resource_id = str(note_map.get(int(raw_id), raw_id))
                    else:
                        resource_id = raw_id
                    parent = str(raw.get("resource_parent_id") or "")
                    if resource_type == "diagram_item" and parent.isdigit():
                        parent = str(note_map.get(int(parent), parent))
                    reviewed_at = str(raw.get("reviewed_at") or utc_now_iso())
                    baseline_sha = str(raw.get("baseline_sha") or "")
                    branch = raw.get("branch")
                    self.database.connection.execute(
                        "INSERT INTO review_history(project_id,resource_type,resource_id,resource_parent_id,repository_id,baseline_sha,branch,reviewed_at) VALUES (?,?,?,?,?,?,?,?)",
                        (project_id, resource_type, resource_id, parent, new_repo, baseline_sha, branch, reviewed_at),
                    )
                    key = (resource_type, resource_id, parent, new_repo)
                    if key not in latest or reviewed_at > latest[key][2]:
                        latest[key] = (baseline_sha, branch, reviewed_at)
                for (resource_type, resource_id, parent, new_repo), (sha, branch, reviewed_at) in latest.items():
                    self.database.connection.execute(
                        """INSERT INTO review_baselines(resource_type,resource_id,resource_parent_id,repository_id,baseline_sha,branch,reviewed_at,created_at,updated_at)
                           VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(resource_type,resource_id,resource_parent_id,repository_id)
                           DO UPDATE SET baseline_sha=excluded.baseline_sha,branch=excluded.branch,reviewed_at=excluded.reviewed_at,updated_at=excluded.updated_at""",
                        (resource_type, resource_id, parent, new_repo, sha, branch, reviewed_at, reviewed_at, reviewed_at),
                    )

        if options.activity:
            with self.database.connection:
                self.database.connection.execute("DELETE FROM activity_events WHERE project_id=?", (project_id,))
                for raw in manifest.get("activity", []):
                    old_repo = raw.get("repository_id")
                    new_repo = repo_map.get(int(old_repo)) if old_repo not in (None, "") else None
                    resource_type = str(raw.get("resource_type") or "")
                    raw_id = str(raw.get("resource_id") or "")
                    if resource_type == "decision" and raw_id.isdigit():
                        resource_id = str(decision_map.get(int(raw_id), raw_id))
                    elif resource_type in {"note", "architecture"} and raw_id.isdigit():
                        resource_id = str(note_map.get(int(raw_id), raw_id))
                    else:
                        resource_id = raw_id or None
                    self.database.connection.execute(
                        "INSERT INTO activity_events(project_id,event_type,title,detail,created_at,repository_id,resource_type,resource_id,metadata_json) VALUES (?,?,?,?,?,?,?,?,?)",
                        (project_id, str(raw.get("event_type") or "imported"), str(raw.get("title") or ""), str(raw.get("detail") or ""),
                         str(raw.get("created_at") or utc_now_iso()), new_repo, resource_type or None, resource_id, str(raw.get("metadata_json") or "{}")),
                    )

        self.database.add_activity(project_id, "project_imported", "Project imported", Path(source).name)
        return project_id
