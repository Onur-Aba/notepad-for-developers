from __future__ import annotations

from pathlib import Path

from app.database import Database
from app.models import Repository
from app.services.local_git_service import LocalGitService


class RepositoryService:
    def __init__(self, database: Database, local_git: LocalGitService | None = None) -> None:
        self.database = database
        self.local_git = local_git or LocalGitService()

    def inspect_local_repository(self, path: str | Path):
        return self.local_git.discover_repository(path)

    def persist_local_repository(self, project_id: int, path: str | Path, info) -> Repository:
        matched = self.local_git.github_full_name_from_remotes(info.remotes)
        remote_name, full_name = matched if matched else (None, None)
        cached = self.database.get_repository_by_full_name(full_name) if full_name else None
        if cached:
            repo = self.database.upsert_repository(
                name=cached.name,
                github_repo_id=cached.github_repo_id,
                github_node_id=cached.github_node_id,
                owner=cached.owner,
                full_name=cached.full_name,
                html_url=cached.html_url,
                clone_url=cached.clone_url,
                default_branch=cached.default_branch or info.branch,
                is_private=cached.is_private,
                installation_id=cached.installation_id,
                local_path=str(Path(path).resolve()),
                local_git_root=info.root,
                remote_name=remote_name,
                language=cached.language,
                description=cached.description,
                last_pushed_at=cached.last_pushed_at,
                github_access_state=cached.github_access_state,
            )
        else:
            name = full_name.split("/", 1)[1] if full_name else Path(info.root).name
            owner = full_name.split("/", 1)[0] if full_name else None
            repo = self.database.upsert_repository(
                name=name, owner=owner, full_name=full_name,
                local_path=str(Path(path).resolve()), local_git_root=info.root,
                remote_name=remote_name, default_branch=info.branch,
                github_access_state="unknown" if full_name else "local_only",
            )
        self.database.link_repository_to_project(project_id, repo.id, info.branch)
        self.database.update_repository_sync(repo.id, info.head_sha, "local_git", branch=info.branch)
        return self.database.get_repository(repo.id) or repo

    def add_local_repository(self, project_id: int, path: str | Path) -> Repository:
        info = self.inspect_local_repository(path)
        return self.persist_local_repository(project_id, path, info)
