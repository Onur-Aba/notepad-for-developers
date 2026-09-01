from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.database import Database, utc_now_iso
from app.models import Repository, ResourceLink
from app.services.github_client import GitHubClient, GitHubError
from app.services.local_git import GitError, changed_files as local_changed_files, commit_count as local_commit_count, current_head


@dataclass(slots=True)
class ScanResult:
    repository_id: int
    head_sha: str | None
    changed_links: int
    checked_links: int
    changed_files: int
    commit_count: int
    source: str
    error: str | None = None


def _normalize(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def resource_is_affected(link: ResourceLink, files: list[str]) -> bool:
    if not files: return False
    if link.resource_type == "repository": return True
    value = _normalize(link.resource_value)
    normalized = [_normalize(item) for item in files]
    if link.resource_type == "directory" and not value:
        return True
    if link.resource_type == "file": return value in normalized
    prefix = value.rstrip("/") + "/"
    return any(item == value or item.startswith(prefix) for item in normalized)


class RepositoryScanner:
    def __init__(self, database: Database, github: GitHubClient | None = None) -> None:
        self.database = database
        self.github = github

    def _head(self, repo: Repository) -> tuple[str, str]:
        if repo.local_path and Path(repo.local_path).exists():
            return current_head(repo.local_path), "local"
        if repo.github_owner and repo.github_repo and self.github:
            sha, branch = self.github.branch_head(repo.github_owner, repo.github_repo, repo.default_branch)
            if branch != repo.default_branch: self.database.update_repository(repo.id, default_branch=branch)
            return sha, "github"
        raise GitError("Repository has neither an available local checkout nor a usable GitHub connection.")

    def _compare(self, repo: Repository, base: str, head: str, source: str) -> tuple[list[str], int]:
        if base == head: return [], 0
        if source == "local" and repo.local_path:
            return local_changed_files(repo.local_path, base, head), local_commit_count(repo.local_path, base, head)
        if repo.github_owner and repo.github_repo and self.github:
            return self.github.compare_commits(repo.github_owner, repo.github_repo, base, head)
        raise GitError("Cannot compare repository revisions.")

    def scan_repository(self, repository_id: int) -> ScanResult:
        repo = self.database.get_repository(repository_id)
        if repo is None: return ScanResult(repository_id, None, 0, 0, 0, 0, "none", "Repository not found")
        try:
            head, source = self._head(repo)
            if repo.last_seen_sha == head:
                checked = int(self.database.connection.execute(
                    "SELECT COUNT(*) FROM resource_links WHERE repository_id=?", (repo.id,)
                ).fetchone()[0])
                self.database.update_repository(repo.id, last_scanned_at=utc_now_iso())
                return ScanResult(repo.id, head, 0, checked, 0, 0, source)
            links = self.database.connection.execute("SELECT DISTINCT note_id FROM resource_links WHERE repository_id=?", (repo.id,)).fetchall()
            all_resource_links: list[ResourceLink] = []
            for row in links: all_resource_links.extend(self.database.list_resource_links(int(row["note_id"])))
            all_resource_links = [link for link in all_resource_links if link.repository_id == repo.id]
            comparison_cache: dict[str, tuple[list[str], int]] = {}
            changed_links = 0; max_files: set[str] = set(); max_commits = 0
            for link in all_resource_links:
                base = link.baseline_sha
                if not base:
                    self.database.mark_note_reviewed(link.note_id, repo.id, head)
                    continue
                if base not in comparison_cache:
                    comparison_cache[base] = self._compare(repo, base, head, source)
                files, commits = comparison_cache[base]
                max_files.update(files); max_commits = max(max_commits, commits)
                if resource_is_affected(link, files):
                    self.database.mark_link_changed(link.id, head, commits)
                    changed_links += 1
                else:
                    self.database.mark_link_checked(link.id, head)
            previous = repo.last_seen_sha
            if previous != head and max_files:
                self.database.record_repository_change(repo.id, previous, head, sorted(max_files), max_commits)
            self.database.update_repository(repo.id, last_seen_sha=head, last_scanned_at=utc_now_iso())
            return ScanResult(repo.id, head, changed_links, len(all_resource_links), len(max_files), max_commits, source)
        except (GitError, GitHubError) as exc:
            return ScanResult(repo.id, None, 0, 0, 0, 0, "error", str(exc))

    def scan_project(self, project_id: int) -> list[ScanResult]:
        return [self.scan_repository(repo.id) for repo in self.database.list_repositories(project_id)]
