from __future__ import annotations

import difflib
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable

from app.database import Database
from app.integrations.supabase.client import SupabaseClient, SupabaseError
from app.settings import SettingsManager
from app.services.team_permissions import permissions_strictly_dominate

PERMISSIONS: tuple[str, ...] = (
    "view_project",
    "edit_project",
    "delete_project",
    "create_note",
    "edit_note",
    "delete_note",
    "create_decision",
    "edit_decision",
    "delete_decision",
    "edit_architecture",
    "manage_access",
    "manage_roles",
    "invite_members",
)

PERMISSION_LABELS = {
    "en": {
        "view_project": "View team projects",
        "edit_project": "Edit project metadata",
        "delete_project": "Delete team project data",
        "create_note": "Create notes",
        "edit_note": "Edit notes",
        "delete_note": "Delete notes",
        "create_decision": "Create decisions",
        "edit_decision": "Edit decisions",
        "delete_decision": "Delete decisions",
        "edit_architecture": "Edit architecture",
        "manage_access": "Manage private-resource access",
        "manage_roles": "Manage lower roles/members",
        "invite_members": "Invite team members",
    },
    "tr": {
        "view_project": "Ekip projelerini görüntüleme",
        "edit_project": "Proje bilgisini düzenleme",
        "delete_project": "Ekip proje verisini silme",
        "create_note": "Not oluşturma",
        "edit_note": "Not düzenleme",
        "delete_note": "Not silme",
        "create_decision": "Karar oluşturma",
        "edit_decision": "Karar düzenleme",
        "delete_decision": "Karar silme",
        "edit_architecture": "Mimariyi düzenleme",
        "manage_access": "Özel içerik erişimini yönetme",
        "manage_roles": "Alt rolleri/üyeleri yönetme",
        "invite_members": "Ekibe kullanıcı davet etme",
    },
}

ProgressCallback = Callable[[int, int, str], None]


@dataclass(slots=True)
class CloudConflict:
    """A note/decision changed online since this device last synchronized it."""

    key: str
    project_id: int
    remote_project_id: str
    resource_type: str
    local_key: str
    title: str
    local_title: str
    remote_title: str
    local_payload: dict[str, Any]
    remote_payload: dict[str, Any]
    baseline_payload: dict[str, Any]
    remote_row_id: str
    remote_revision: int
    remote_updated_at: str
    remote_updated_by: str
    changed_summary: list[str]
    remote_updated_by_name: str = ""


@dataclass(slots=True)
class CloudPreflight:
    conflicts: list[CloudConflict]
    remote_projects: dict[str, dict[str, Any]]
    remote_resources: dict[str, dict[str, Any]]


class CloudService:
    """Coordinates local-first online backup and team calls.

    The desktop app only talks to Supabase using the signed-in user's JWT. It
    never sends local filesystem paths, credentials, GitHub tokens, Supabase
    keys, or passwords to the database.

    Online backup is deliberately manual. Local changes are not uploaded until
    the user presses the backup button. This keeps local-first behavior clear
    and makes optimistic-concurrency conflicts visible instead of silently
    overwriting another team member's edit.
    """

    def __init__(self, database: Database, settings: SettingsManager, client: SupabaseClient) -> None:
        self.database = database
        self.settings = settings
        self.client = client
        device_id = str(self.settings.value("cloud/device_id", "") or "")
        if not device_id:
            device_id = str(uuid.uuid4())
            self.settings.set_value("cloud/device_id", device_id)
            self.settings.sync()
        self.device_id = device_id
        self._overview_cache: tuple[float, dict[str, Any]] | None = None

    # ------------------------------------------------------------------
    # Selection persistence / local tree
    # ------------------------------------------------------------------
    def saved_selection(self) -> dict[str, dict[str, list[str]]]:
        raw = str(self.settings.value("cloud/selection_json", "") or "")
        if not raw:
            return {}
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if not isinstance(value, dict):
            return {}
        clean: dict[str, dict[str, list[str]]] = {}
        for project_id, groups in value.items():
            if not isinstance(groups, dict):
                continue
            clean[str(project_id)] = {
                str(group): [str(item) for item in items if isinstance(item, (str, int))]
                for group, items in groups.items() if isinstance(items, list)
            }
        return clean

    def save_selection(self, selection: dict[str, dict[str, list[str]]], auto_sync: bool = False) -> None:
        self.settings.set_value("cloud/selection_json", json.dumps(selection, ensure_ascii=False, separators=(",", ":")))
        # v2 intentionally disables background upload. Keep the setting for
        # backwards compatibility, but force it off so an older preference can
        # never start uploading silently.
        self.settings.set_value("cloud/auto_sync", False)
        self.settings.sync()

    def disable_auto_sync(self) -> None:
        self.settings.set_value("cloud/auto_sync", False)
        self.settings.sync()

    def auto_sync_enabled(self) -> bool:
        return False

    def project_tree(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for project in self.database.list_projects():
            notes = self.database.list_notes(project_id=project.id)
            decisions = self.database.list_decisions(project_id=project.id)
            diagrams = self.database.list_diagram_notes(project.id)
            repositories = self.database.list_repositories(project.id)
            result.append({
                "project": project,
                "notes": [(n.id, n.title or f"Note {n.id}") for n in notes],
                "decisions": [(d.id, f"{d.decision_key} · {d.title or f'Decision {d.id}'}") for d in decisions],
                "architecture": [(n.id, n.title or f"Architecture {n.id}") for n in diagrams],
                "repositories": [(r.id, r.full_name or r.name or f"Repository {r.id}") for r in repositories],
            })
        return result

    # ------------------------------------------------------------------
    # Local sync baselines / payload helpers
    # ------------------------------------------------------------------
    def _baselines(self) -> dict[str, dict[str, Any]]:
        raw = str(self.settings.value("cloud/baselines_json", "") or "")
        if not raw:
            return {}
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    def _save_baselines(self, baselines: dict[str, dict[str, Any]]) -> None:
        # Limit the persisted snapshot to the data needed for conflict diffs.
        self.settings.set_value("cloud/baselines_json", json.dumps(baselines, ensure_ascii=False, separators=(",", ":")))
        self.settings.sync()

    @staticmethod
    def _baseline_key(project_id: int | str, resource_type: str, local_key: str) -> str:
        return f"{project_id}:{resource_type}:{local_key}"

    def _note_payload(self, note) -> dict[str, Any]:
        return {
            "title": note.title,
            "content_html": note.content_html,
            "content_plain": note.content_plain,
            "created_at": note.created_at,
            "updated_at": note.updated_at,
            "tags": self.database.get_tags("note", note.id),
            "favorite": self.database.is_favorite("note", note.id),
            "links": self._links_payload("note", note.id),
        }

    def _decision_payload(self, decision) -> dict[str, Any]:
        return {
            "decision_key": decision.decision_key,
            "status": decision.status,
            "title": decision.title,
            "content_html": decision.content_html,
            "content_plain": decision.content_plain,
            "created_at": decision.created_at,
            "updated_at": decision.updated_at,
            "tags": self.database.get_tags("decision", decision.id),
            "favorite": self.database.is_favorite("decision", decision.id),
            "links": self._links_payload("decision", decision.id),
        }

    def _architecture_payload(self, note) -> dict[str, Any]:
        return {
            "note_id": note.id,
            "note_title": note.title,
            "diagram": self.database.get_diagram(note.id),
            "links": self._architecture_links_payload(note.id),
        }

    @staticmethod
    def _repository_payload(repo) -> dict[str, Any]:
        return {
            "github_repo_id": repo.github_repo_id,
            "owner": repo.owner,
            "name": repo.name,
            "full_name": repo.full_name,
            "html_url": repo.html_url,
            "default_branch": repo.default_branch,
            "is_private": repo.is_private,
            "language": repo.language,
            "description": repo.description,
            "last_pushed_at": repo.last_pushed_at,
            "last_seen_sha": repo.last_seen_sha,
        }

    def _selected_resource_payloads(self, project, groups: dict[str, list[str]]) -> list[tuple[str, str, str, dict[str, Any]]]:
        resources: list[tuple[str, str, str, dict[str, Any]]] = []
        for note_id in groups.get("notes", []):
            try:
                note = self.database.get_note(int(note_id))
            except (TypeError, ValueError):
                note = None
            if note is not None and note.project_id == project.id:
                resources.append(("note", str(note.id), note.title, self._note_payload(note)))
        for decision_id in groups.get("decisions", []):
            try:
                decision = self.database.get_decision(int(decision_id))
            except (TypeError, ValueError):
                decision = None
            if decision is not None and decision.project_id == project.id:
                resources.append(("decision", str(decision.id), decision.title, self._decision_payload(decision)))
        for note_id in groups.get("architecture", []):
            try:
                note = self.database.get_note(int(note_id))
            except (TypeError, ValueError):
                note = None
            if note is not None and note.project_id == project.id:
                resources.append(("architecture", str(note.id), note.title, self._architecture_payload(note)))
        for repository_id in groups.get("repositories", []):
            try:
                repo = self.database.get_repository(int(repository_id))
            except (TypeError, ValueError):
                repo = None
            if repo is not None and self.database.project_repository(project.id, repo.id):
                resources.append(("repository", str(repo.id), repo.full_name or repo.name, self._repository_payload(repo)))
        return resources

    @staticmethod
    def _payload_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
        # updated_at is expected to differ as users work. Everything else is
        # significant for a backup conflict.
        def normalized(value: dict[str, Any]) -> dict[str, Any]:
            result = dict(value or {})
            result.pop("updated_at", None)
            return result
        return normalized(a) == normalized(b)

    @staticmethod
    def _text_diff_summary(before: str, after: str) -> str:
        before_lines = str(before or "").splitlines()
        after_lines = str(after or "").splitlines()
        added = removed = 0
        for line in difflib.ndiff(before_lines, after_lines):
            if line.startswith("+ "):
                added += 1
            elif line.startswith("- "):
                removed += 1
        return f"+{added} / -{removed} lines"

    def _describe_changes(self, resource_type: str, baseline: dict[str, Any], remote: dict[str, Any], local: dict[str, Any]) -> list[str]:
        result: list[str] = []
        source = baseline or local
        if str(source.get("title") or "") != str(remote.get("title") or ""):
            result.append(f"Title: {source.get('title') or '—'} → {remote.get('title') or '—'}")
        if resource_type == "decision" and str(source.get("status") or "") != str(remote.get("status") or ""):
            result.append(f"Status: {source.get('status') or '—'} → {remote.get('status') or '—'}")
        before_text = str(source.get("content_plain") or "")
        remote_text = str(remote.get("content_plain") or "")
        if before_text != remote_text:
            result.append("Content: " + self._text_diff_summary(before_text, remote_text))
        if source.get("tags") != remote.get("tags"):
            result.append("Tags changed")
        if bool(source.get("favorite")) != bool(remote.get("favorite")):
            result.append("Favorite changed")
        if not result and not self._payload_equal(remote, local):
            result.append("Online metadata changed")
        return result

    # ------------------------------------------------------------------
    # Conflict preflight
    # ------------------------------------------------------------------
    def preflight_sync(self, selection: dict[str, dict[str, list[str]]], progress: ProgressCallback | None = None) -> CloudPreflight:
        session = self.client.ensure_session()
        local_projects = {str(p.id): p for p in self.database.list_projects()}
        baselines = self._baselines()
        selected = [(pid, groups) for pid, groups in selection.items() if any(bool(v) for v in groups.values())]
        total = max(1, len(selected))
        remote_projects: dict[str, dict[str, Any]] = {}
        remote_resources: dict[str, dict[str, Any]] = {}
        conflicts: list[CloudConflict] = []

        for index, (project_id, groups) in enumerate(selected, start=1):
            project = local_projects.get(str(project_id))
            if project is None:
                continue
            if progress:
                progress(index - 1, total, f"Checking {project.name}")
            rows = self.client.table_select("cloud_projects", {
                "owner_id": f"eq.{session.user_id}",
                "device_id": f"eq.{self.device_id}",
                "local_project_id": f"eq.{project.id}",
                "select": "id,owner_id,device_id,local_project_id,name,description,source_updated_at,revision,updated_at,updated_by",
                "limit": "1",
            })
            if not rows:
                if progress:
                    progress(index, total, f"Checked {project.name}")
                continue
            remote_project = rows[0]
            remote_projects[str(project.id)] = remote_project
            remote_id = str(remote_project["id"])
            rows = self.client.table_select("cloud_resources", {
                "project_id": f"eq.{remote_id}",
                "select": "id,project_id,resource_type,local_key,title,payload,revision,updated_at,updated_by",
            })
            by_identity = {(str(r.get("resource_type")), str(r.get("local_key"))): r for r in rows}
            for typ, local_key, title, payload in self._selected_resource_payloads(project, groups):
                remote = by_identity.get((typ, local_key))
                snapshot_key = self._baseline_key(project.id, typ, local_key)
                if remote:
                    remote_resources[snapshot_key] = remote
                if typ not in {"note", "decision"} or not remote:
                    continue
                remote_payload = remote.get("payload") if isinstance(remote.get("payload"), dict) else {}
                baseline = baselines.get(snapshot_key) if isinstance(baselines.get(snapshot_key), dict) else {}
                baseline_payload = baseline.get("payload") if isinstance(baseline.get("payload"), dict) else {}
                baseline_revision = int(baseline.get("revision") or 0)
                remote_revision = int(remote.get("revision") or 1)
                changed_by_other = bool(remote.get("updated_by")) and str(remote.get("updated_by")) != session.user_id
                remote_changed_since_baseline = (not baseline_revision) or remote_revision != baseline_revision
                local_differs = str(remote.get("title") or "") != str(title or "") or not self._payload_equal(remote_payload, payload)
                if changed_by_other and remote_changed_since_baseline and local_differs:
                    conflicts.append(CloudConflict(
                        key=snapshot_key,
                        project_id=int(project.id),
                        remote_project_id=remote_id,
                        resource_type=typ,
                        local_key=local_key,
                        title=title,
                        local_title=title,
                        remote_title=str(remote.get("title") or ""),
                        local_payload=payload,
                        remote_payload=remote_payload,
                        baseline_payload=baseline_payload,
                        remote_row_id=str(remote.get("id") or ""),
                        remote_revision=remote_revision,
                        remote_updated_at=str(remote.get("updated_at") or ""),
                        remote_updated_by=str(remote.get("updated_by") or ""),
                        changed_summary=self._describe_changes(typ, baseline_payload, remote_payload, payload),
                    ))
            if progress:
                progress(index, total, f"Checked {project.name}")

        editor_ids = sorted({c.remote_updated_by for c in conflicts if c.remote_updated_by})
        if editor_ids:
            profiles = self.client.table_select("profiles", {
                "id": "in.(" + ",".join(editor_ids) + ")",
                "select": "id,username,first_name,last_name",
            })
            names = {
                str(profile.get("id")): ("@" + str(profile.get("username")))
                for profile in profiles if profile.get("id") and profile.get("username")
            }
            for conflict in conflicts:
                conflict.remote_updated_by_name = names.get(conflict.remote_updated_by, "")
        return CloudPreflight(conflicts=conflicts, remote_projects=remote_projects, remote_resources=remote_resources)

    # ------------------------------------------------------------------
    # Cloud backup
    # ------------------------------------------------------------------
    def sync_saved_selection(self) -> dict[str, Any]:
        selection = self.saved_selection()
        if not selection:
            return {"projects": 0, "resources": 0, "removed": 0, "skipped": 0}
        preflight = self.preflight_sync(selection)
        # Background/legacy callers never overwrite another user's conflict.
        resolutions = {conflict.key: "skip" for conflict in preflight.conflicts}
        return self.sync_selection(selection, preflight=preflight, conflict_resolutions=resolutions)

    def sync_selection(
        self,
        selection: dict[str, dict[str, list[str]]],
        *,
        preflight: CloudPreflight | None = None,
        conflict_resolutions: dict[str, str] | None = None,
        progress: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        session = self.client.ensure_session()
        self.save_selection(selection, False)
        preflight = preflight or self.preflight_sync(selection)
        resolutions = conflict_resolutions or {}
        conflicts_by_key = {c.key: c for c in preflight.conflicts}
        baselines = self._baselines()
        counts: dict[str, Any] = {"projects": 0, "resources": 0, "removed": 0, "skipped": 0, "pulled": 0}
        local_projects = {str(p.id): p for p in self.database.list_projects()}
        active: list[tuple[Any, dict[str, list[str]], list[tuple[str, str, str, dict[str, Any]]]]] = []
        for project_id, groups in selection.items():
            project = local_projects.get(str(project_id))
            if project is None or not any(bool(v) for v in groups.values()):
                continue
            active.append((project, groups, self._selected_resource_payloads(project, groups)))
        total_steps = max(1, sum(1 + len(resources) for _p, _g, resources in active))
        done = 0

        selected_project_ids: set[str] = set()
        for project, groups, resources in active:
            if progress:
                progress(done, total_steps, f"Uploading project · {project.name}")
            selected_project_ids.add(str(project.id))
            remote_hint = preflight.remote_projects.get(str(project.id))
            remote = self._ensure_cloud_project(project, session.user_id, remote_hint)
            remote_id = str(remote["id"])
            counts["projects"] += 1
            done += 1
            if progress:
                progress(done, total_steps, f"Project ready · {project.name}")
            selected_keys: dict[str, set[str]] = {"note": set(), "decision": set(), "architecture": set(), "repository": set()}

            for typ, local_key, title, payload in resources:
                selected_keys[typ].add(local_key)
                baseline_key = self._baseline_key(project.id, typ, local_key)
                conflict = conflicts_by_key.get(baseline_key)
                resolution = resolutions.get(baseline_key, "skip" if conflict else "local")
                if conflict and resolution == "remote":
                    self.apply_remote_conflict(conflict)
                    self._set_baseline_from_row(baselines, baseline_key, {
                        "id": conflict.remote_row_id,
                        "revision": conflict.remote_revision,
                        "updated_at": conflict.remote_updated_at,
                        "updated_by": conflict.remote_updated_by,
                        "title": conflict.remote_title,
                        "payload": conflict.remote_payload,
                    })
                    counts["pulled"] += 1
                    done += 1
                    if progress:
                        progress(done, total_steps, f"Used online version · {title}")
                    continue
                if conflict and resolution != "local":
                    counts["skipped"] += 1
                    done += 1
                    if progress:
                        progress(done, total_steps, f"Skipped conflict · {title}")
                    continue

                remote_hint = preflight.remote_resources.get(baseline_key)
                if conflict and resolution == "local":
                    # The conflict dialog explicitly authorized overwriting the
                    # revision the user inspected. A later revision still fails
                    # the optimistic update and asks the user to retry.
                    remote_hint = {
                        "id": conflict.remote_row_id,
                        "revision": conflict.remote_revision,
                        "updated_at": conflict.remote_updated_at,
                        "updated_by": conflict.remote_updated_by,
                        "title": conflict.remote_title,
                        "payload": conflict.remote_payload,
                    }
                row = self._upsert_resource(remote_id, session.user_id, typ, local_key, title, payload, remote_hint)
                self._set_baseline_from_row(baselines, baseline_key, row)
                counts["resources"] += 1
                done += 1
                if progress:
                    progress(done, total_steps, f"Uploaded · {title}")

            counts["removed"] += self._remove_unselected_resources(remote_id, selected_keys)

        # Unchecked personal backups are removed only when they are not assigned
        # to a team. Team data is never silently destroyed by a checkbox.
        for project_id, groups in selection.items():
            if str(project_id) in selected_project_ids or any(bool(v) for v in groups.values()):
                continue
            try:
                local_project_id = int(project_id)
            except (TypeError, ValueError):
                continue
            rows = self.client.table_select("cloud_projects", {
                "owner_id": f"eq.{session.user_id}", "device_id": f"eq.{self.device_id}",
                "local_project_id": f"eq.{local_project_id}", "select": "id"
            })
            for row in rows:
                remote_id = str(row["id"])
                assigned = self.client.table_select("team_projects", {"project_id": f"eq.{remote_id}", "select": "team_id", "limit": "1"})
                if not assigned:
                    deleted = self.client.table_delete("cloud_projects", {"id": f"eq.{remote_id}"})
                    counts["removed"] += len(deleted)
        self._save_baselines(baselines)
        return counts

    def _ensure_cloud_project(self, project, owner_id: str, existing: dict[str, Any] | None = None) -> dict[str, Any]:
        if existing is None:
            rows = self.client.table_select("cloud_projects", {
                "owner_id": f"eq.{owner_id}", "device_id": f"eq.{self.device_id}",
                "local_project_id": f"eq.{project.id}",
                "select": "id,owner_id,device_id,local_project_id,name,description,source_updated_at,revision,updated_at,updated_by",
                "limit": "1",
            })
            existing = rows[0] if rows else None
        body = {
            "name": project.name,
            "description": project.description,
            "source_updated_at": project.updated_at,
        }
        if existing:
            if (str(existing.get("name") or "") == str(project.name or "")
                    and str(existing.get("description") or "") == str(project.description or "")
                    and str(existing.get("source_updated_at") or "") == str(project.updated_at or "")):
                return existing
            revision = int(existing.get("revision") or 1)
            rows = self.client.table_update("cloud_projects", {
                "id": f"eq.{existing['id']}", "revision": f"eq.{revision}"
            }, body)
            if not rows:
                raise SupabaseError("Online project changed while backup was running. Please retry so DevNest can compare the newest version.", code="DEVNEST_CONFLICT")
            return rows[0]
        rows = self.client.table_insert("cloud_projects", {
            "owner_id": owner_id,
            "device_id": self.device_id,
            "local_project_id": project.id,
            **body,
        })
        if not rows:
            raise SupabaseError("Cloud project could not be created.")
        return rows[0]

    def _upsert_resource(
        self,
        project_id: str,
        owner_id: str,
        resource_type: str,
        local_key: str,
        title: str,
        payload: dict[str, Any],
        existing: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if existing is None:
            rows = self.client.table_select("cloud_resources", {
                "project_id": f"eq.{project_id}", "resource_type": f"eq.{resource_type}",
                "local_key": f"eq.{local_key}",
                "select": "id,project_id,resource_type,local_key,title,payload,revision,updated_at,updated_by",
                "limit": "1",
            })
            existing = rows[0] if rows else None
        if existing:
            remote_payload = existing.get("payload") if isinstance(existing.get("payload"), dict) else {}
            if str(existing.get("title") or "") == str(title or "") and self._payload_equal(remote_payload, payload):
                return existing
            revision = int(existing.get("revision") or 1)
            rows = self.client.table_update("cloud_resources", {
                "id": f"eq.{existing['id']}", "revision": f"eq.{revision}"
            }, {"title": title, "payload": payload})
            if not rows:
                raise SupabaseError(
                    "This online item changed again while backup was running. Nothing was overwritten; reopen Online Backup and compare the newest version.",
                    code="DEVNEST_CONFLICT",
                )
            return rows[0]
        try:
            rows = self.client.table_insert("cloud_resources", {
                "owner_id": owner_id,
                "project_id": project_id,
                "resource_type": resource_type,
                "local_key": local_key,
                "title": title,
                "payload": payload,
            })
        except SupabaseError as exc:
            # A concurrent insert can win the unique(project,type,key) race.
            if exc.status in {400, 409}:
                raise SupabaseError("This online item appeared while backup was running. Reopen Online Backup to compare it safely.", code="DEVNEST_CONFLICT") from exc
            raise
        if not rows:
            raise SupabaseError("Cloud resource could not be created.")
        return rows[0]

    @staticmethod
    def _set_baseline_from_row(baselines: dict[str, dict[str, Any]], key: str, row: dict[str, Any]) -> None:
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        # Do not duplicate entire HTML documents/link metadata in QSettings. A
        # compact snapshot is sufficient to explain what changed; the revision
        # number is the actual optimistic-concurrency boundary.
        compact_payload = {
            field: payload.get(field)
            for field in ("title", "status", "content_plain", "tags", "favorite")
            if field in payload
        }
        baselines[key] = {
            "id": str(row.get("id") or ""),
            "revision": int(row.get("revision") or 1),
            "updated_at": str(row.get("updated_at") or ""),
            "updated_by": str(row.get("updated_by") or ""),
            "title": str(row.get("title") or ""),
            "payload": compact_payload,
        }

    def apply_remote_conflict(self, conflict: CloudConflict) -> None:
        payload = conflict.remote_payload
        if conflict.resource_type == "note":
            note = self.database.get_note(int(conflict.local_key))
            if note is None:
                return
            self.database.update_note(
                note.id,
                str(conflict.remote_title or payload.get("title") or note.title),
                str(payload.get("content_html") or ""),
                str(payload.get("content_plain") or ""),
            )
            if isinstance(payload.get("tags"), list):
                self.database.set_tags("note", note.id, [str(x) for x in payload["tags"]])
            if "favorite" in payload:
                self.database.set_favorite("note", note.id, bool(payload.get("favorite")), project_id=note.project_id)
        elif conflict.resource_type == "decision":
            decision = self.database.get_decision(int(conflict.local_key))
            if decision is None:
                return
            self.database.update_decision(
                decision.id,
                str(conflict.remote_title or payload.get("title") or decision.title),
                str(payload.get("content_html") or ""),
                str(payload.get("content_plain") or ""),
                str(payload.get("status") or decision.status),
            )
            if isinstance(payload.get("tags"), list):
                self.database.set_tags("decision", decision.id, [str(x) for x in payload["tags"]])
            if "favorite" in payload:
                self.database.set_favorite("decision", decision.id, bool(payload.get("favorite")), project_id=decision.project_id)

    def _remove_unselected_resources(self, remote_project_id: str, selected: dict[str, set[str]]) -> int:
        assigned = self.client.table_select("team_projects", {
            "project_id": f"eq.{remote_project_id}", "select": "team_id", "limit": "1"
        })
        if assigned:
            return 0
        removed = 0
        for resource_type, wanted in selected.items():
            existing = self.client.table_select("cloud_resources", {
                "project_id": f"eq.{remote_project_id}", "resource_type": f"eq.{resource_type}",
                "select": "id,local_key"
            })
            for row in existing:
                if str(row.get("local_key")) not in wanted:
                    removed += len(self.client.table_delete("cloud_resources", {"id": f"eq.{row['id']}"}))
        return removed

    def _links_payload(self, resource_type: str, resource_id: int) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for link in self.database.list_resource_links(resource_type=resource_type, resource_id=resource_id):
            repo = self.database.get_repository(link.repository_id)
            result.append({
                "repository": (repo.full_name or repo.name) if repo else str(link.repository_id),
                "target_type": link.target_type,
                "target_value": link.target_value,
                "metadata": link.metadata,
            })
        return result

    def _architecture_links_payload(self, note_id: int) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for link in self.database.list_resource_links(resource_type="diagram_item", resource_parent_id=note_id):
            repo = self.database.get_repository(link.repository_id)
            result.append({
                "item_id": link.resource_id,
                "repository": (repo.full_name or repo.name) if repo else str(link.repository_id),
                "target_type": link.target_type,
                "target_value": link.target_value,
                "metadata": link.metadata,
            })
        return result

    # ------------------------------------------------------------------
    # Account / notifications
    # ------------------------------------------------------------------
    def profile(self) -> dict[str, Any] | None:
        return self.client.refresh_profile() if self.client.signed_in else None

    def cloud_notifications(self, unread_only: bool = True) -> list[dict[str, Any]]:
        if not self.client.signed_in:
            return []
        query = {"select": "id,event_type,title,detail,metadata,is_read,created_at", "order": "created_at.desc"}
        if unread_only:
            query["is_read"] = "eq.false"
        return self.client.table_select("user_notifications", query)

    def mark_cloud_notifications_read(self) -> None:
        if self.client.signed_in:
            self.client.table_update("user_notifications", {"is_read": "eq.false"}, {"is_read": True})

    # ------------------------------------------------------------------
    # Team API
    # ------------------------------------------------------------------
    def invalidate_team_cache(self) -> None:
        self._overview_cache = None

    def team_overview(self, *, force: bool = False) -> dict[str, Any]:
        now = time.monotonic()
        if not force and self._overview_cache and now - self._overview_cache[0] < 20:
            return self._overview_cache[1]
        value = self.client.rpc("team_overview")
        if isinstance(value, list) and value:
            value = value[0]
        if not isinstance(value, dict):
            value = {"teams": [], "invitations": []}
        value.setdefault("teams", [])
        value.setdefault("invitations", [])
        self._overview_cache = (now, value)
        return value

    def list_teams(self) -> list[dict[str, Any]]:
        value = self.team_overview()
        teams = value.get("teams")
        return teams if isinstance(teams, list) else []

    def create_team(self, name: str) -> dict[str, Any]:
        clean = name.strip()
        if not (2 <= len(clean) <= 80):
            raise SupabaseError("Team name must be 2-80 characters.")
        value = self.client.rpc("team_create", {"p_name": clean})
        self.invalidate_team_cache()
        if isinstance(value, dict):
            return value
        if isinstance(value, list) and value:
            return value[0]
        return {"id": str(value), "name": clean}

    def pending_invitations(self) -> list[dict[str, Any]]:
        value = self.team_overview()
        invitations = value.get("invitations")
        return invitations if isinstance(invitations, list) else []

    def invite_username(self, team_id: str, username: str) -> Any:
        username = username.strip()
        if not username or len(username) > 32:
            raise SupabaseError("Enter a valid username.")
        value = self.client.rpc("team_invite_username", {"p_team_id": team_id, "p_username": username})
        self.invalidate_team_cache()
        return value

    def respond_invitation(self, invitation_id: str, accept: bool) -> Any:
        value = self.client.rpc("team_respond_invitation", {"p_invitation_id": invitation_id, "p_accept": bool(accept)})
        self.invalidate_team_cache()
        return value

    def team_detail_snapshot(self, team_id: str) -> dict[str, Any]:
        value = self.client.rpc("team_detail_snapshot", {"p_team_id": team_id})
        if isinstance(value, list) and value:
            value = value[0]
        if not isinstance(value, dict):
            return {"projects": [], "members": [], "roles": [], "activity": [], "viewer": {}}
        for key in ("projects", "members", "roles", "activity"):
            if not isinstance(value.get(key), list):
                value[key] = []
        if not isinstance(value.get("viewer"), dict):
            value["viewer"] = {}
        return value

    def team_members(self, team_id: str) -> list[dict[str, Any]]:
        return self.team_detail_snapshot(team_id)["members"]

    def team_activity(self, team_id: str, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.team_detail_snapshot(team_id)["activity"]
        return rows[:max(1, min(500, int(limit)))]

    def team_roles(self, team_id: str) -> list[dict[str, Any]]:
        return self.team_detail_snapshot(team_id)["roles"]

    def create_role(self, team_id: str, name: str, permissions: dict[str, bool]) -> Any:
        value = self.client.rpc("team_create_role", {
            "p_team_id": team_id, "p_name": name.strip(), "p_permissions": permissions
        })
        self.invalidate_team_cache()
        return value

    def update_role(self, role_id: str, name: str, permissions: dict[str, bool]) -> Any:
        value = self.client.rpc("team_update_role", {
            "p_role_id": role_id, "p_name": name.strip(), "p_permissions": permissions
        })
        self.invalidate_team_cache()
        return value

    def assign_role(self, team_id: str, user_id: str, role_id: str) -> Any:
        value = self.client.rpc("team_assign_role", {"p_team_id": team_id, "p_user_id": user_id, "p_role_id": role_id})
        self.invalidate_team_cache()
        return value

    def set_member_override(self, team_id: str, user_id: str, permission: str, value: bool | None) -> Any:
        if permission not in PERMISSIONS:
            raise SupabaseError("Unknown permission.")
        result = self.client.rpc("team_set_member_permission", {
            "p_team_id": team_id, "p_user_id": user_id, "p_permission": permission, "p_allow": value
        })
        self.invalidate_team_cache()
        return result

    def member_overrides(self, team_id: str, user_id: str) -> dict[str, bool]:
        rows = self.client.table_select("team_member_permission_overrides", {
            "team_id": f"eq.{team_id}", "user_id": f"eq.{user_id}", "select": "permission_key,allow"
        })
        return {str(r["permission_key"]): bool(r["allow"]) for r in rows}

    def owned_cloud_projects(self) -> list[dict[str, Any]]:
        session = self.client.ensure_session()
        return self.client.table_select("cloud_projects", {
            "owner_id": f"eq.{session.user_id}",
            "select": "id,name,description,local_project_id,device_id,revision,updated_at,updated_by",
            "order": "updated_at.desc",
        })

    def team_projects(self, team_id: str) -> list[dict[str, Any]]:
        return self.team_detail_snapshot(team_id)["projects"]

    def assign_team_project(self, team_id: str, project_id: str) -> Any:
        value = self.client.rpc("team_assign_project", {"p_team_id": team_id, "p_project_id": project_id})
        self.invalidate_team_cache()
        return value

    def unassign_team_project(self, team_id: str, project_id: str) -> Any:
        value = self.client.rpc("team_unassign_project", {"p_team_id": team_id, "p_project_id": project_id})
        self.invalidate_team_cache()
        return value

    def cloud_resources(self, project_id: str, resource_type: str | None = None) -> list[dict[str, Any]]:
        query = {
            "project_id": f"eq.{project_id}",
            "select": "id,project_id,resource_type,local_key,title,payload,revision,updated_at,updated_by",
            "order": "resource_type.asc,title.asc",
        }
        if resource_type:
            query["resource_type"] = f"eq.{resource_type}"
        return self.client.table_select("cloud_resources", query)

    def update_cloud_resource(self, row: dict[str, Any], title: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Optimistically update an online team resource.

        RLS still decides whether the signed-in member may edit it. The revision
        filter prevents a stale team editor from overwriting a newer edit.
        """
        row_id = str(row.get("id") or "")
        revision = int(row.get("revision") or 1)
        if not row_id:
            raise SupabaseError("Online resource id is missing.")
        rows = self.client.table_update("cloud_resources", {
            "id": f"eq.{row_id}", "revision": f"eq.{revision}"
        }, {"title": title[:500], "payload": payload})
        if not rows:
            current = self.client.table_select("cloud_resources", {
                "id": f"eq.{row_id}", "select": "id,revision,updated_at,updated_by", "limit": "1"
            })
            if current and int(current[0].get("revision") or 1) != revision:
                raise SupabaseError("Someone changed this item while you were editing it. Reopen it to compare the newest version.", code="DEVNEST_CONFLICT")
            raise SupabaseError("Your team role does not allow editing this online item, or the item is no longer available.", code="DEVNEST_PERMISSION")
        return rows[0]

    def set_resource_allowed_users(self, team_id: str, project_id: str, resource_type: str,
                                   resource_key: str, user_ids: list[str], *, restricted: bool = True) -> Any:
        return self.client.rpc("team_replace_resource_user_acl", {
            "p_team_id": team_id, "p_project_id": project_id, "p_resource_type": resource_type,
            "p_resource_key": resource_key, "p_allowed_users": user_ids, "p_restricted": bool(restricted),
        })

    def resource_access_state(self, team_id: str, project_id: str, resource_type: str, resource_key: str) -> dict[str, object]:
        policies = self.client.table_select("team_resource_policies", {
            "team_id": f"eq.{team_id}", "project_id": f"eq.{project_id}",
            "resource_type": f"eq.{resource_type}", "resource_key": f"eq.{resource_key}",
            "select": "restricted", "limit": "1",
        })
        return {"restricted": bool(policies and policies[0].get("restricted")),
                "users": self.resource_allowed_users(team_id, project_id, resource_type, resource_key)}

    def resource_allowed_users(self, team_id: str, project_id: str, resource_type: str, resource_key: str) -> set[str]:
        rows = self.client.table_select("team_resource_acl", {
            "team_id": f"eq.{team_id}", "project_id": f"eq.{project_id}",
            "resource_type": f"eq.{resource_type}", "resource_key": f"eq.{resource_key}",
            "subject_user_id": "not.is.null", "can_view": "eq.true", "select": "subject_user_id"
        })
        return {str(r["subject_user_id"]) for r in rows if r.get("subject_user_id")}

    def role_visibility(self, team_id: str, viewer_role_id: str) -> set[str]:
        rows = self.client.table_select("team_role_visibility", {
            "team_id": f"eq.{team_id}", "viewer_role_id": f"eq.{viewer_role_id}", "can_view": "eq.true", "select": "target_role_id"
        })
        return {str(r["target_role_id"]) for r in rows}

    def set_role_visibility(self, team_id: str, viewer_role_id: str, target_role_ids: list[str]) -> Any:
        return self.client.rpc("team_replace_role_visibility", {
            "p_team_id": team_id, "p_viewer_role_id": viewer_role_id, "p_target_role_ids": target_role_ids
        })
