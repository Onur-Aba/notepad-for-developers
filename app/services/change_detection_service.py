from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.database import Database
from app.models import ChangedFile, CommitInfo, Repository, ResourceLink, ReviewStatus, ReviewSummary
from app.services.local_git_service import GitRepositoryError, LocalGitService, path_matches

if TYPE_CHECKING:
    from app.integrations.github.client import GitHubClient

logger = logging.getLogger(__name__)


class BaselineComparisonError(RuntimeError):
    pass


def dedupe_changed_files(items: list[ChangedFile]) -> list[ChangedFile]:
    """Return changed files once, preserving Git's original order."""
    result: list[ChangedFile] = []
    seen: set[tuple[str, str, str | None]] = set()
    for item in items:
        key = ((item.status or "M").upper(), item.path, item.previous_path)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def dedupe_commits(items: list[CommitInfo]) -> list[CommitInfo]:
    """Deduplicate commit rows by SHA. Old caches may contain repeated rows."""
    result: list[CommitInfo] = []
    seen: set[str] = set()
    for item in items:
        key = (item.sha or f"{item.message}|{item.authored_at or ''}").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def merge_review_summaries(items: list[ReviewSummary]) -> list[ReviewSummary]:
    """Merge multiple monitored paths for one knowledge item/repository.

    A decision can be connected to several files in the same repository. Showing one
    card per link makes the same commit look duplicated. The review UI should instead
    show one knowledge item per repository and merge its linked paths.
    """
    groups: dict[tuple[str, str, str, int], list[ReviewSummary]] = {}
    for item in items:
        link = item.resource_link
        key = (link.resource_type, link.resource_id, link.resource_parent_id, link.repository_id)
        groups.setdefault(key, []).append(item)

    priority = {
        ReviewStatus.NEEDS_REVIEW: 4,
        ReviewStatus.CANNOT_COMPARE: 3,
        ReviewStatus.NOT_REVIEWED: 2,
        ReviewStatus.CURRENT: 1,
    }
    merged: list[ReviewSummary] = []
    for values in groups.values():
        representative = max(values, key=lambda value: priority.get(value.status, 0))
        changed = dedupe_changed_files([file for value in values for file in value.changed_files])
        linked = dedupe_changed_files([file for value in values for file in value.linked_changed_files])
        commits = dedupe_commits([commit for value in values for commit in value.commits])
        prs = []
        seen_prs: set[tuple[int, str]] = set()
        for value in values:
            for pr in value.pull_requests:
                key = (pr.number, pr.html_url or "")
                if key not in seen_prs:
                    seen_prs.add(key)
                    prs.append(pr)
        reported_count = max([value.commit_count for value in values] + [len(commits)])
        # GitHub/local commit lists are complete for normal (<100 commit) review
        # windows. If an old cache accidentally repeated a commit row/count, prefer
        # the number of unique SHAs so the UI never says "2 commits" for one commit.
        commit_count = len(commits) if commits and reported_count <= 100 else reported_count
        merged.append(ReviewSummary(
            resource_link=representative.resource_link,
            status=representative.status,
            baseline_sha=representative.baseline_sha,
            current_sha=representative.current_sha,
            branch=representative.branch,
            commit_count=commit_count,
            changed_files=changed,
            linked_changed_files=linked,
            commits=commits,
            pull_requests=prs,
            message=representative.message,
        ))
    return merged


class ChangeDetectionService:
    def __init__(self, database: Database, local_git: LocalGitService | None = None,
                 github_client: "GitHubClient | None" = None) -> None:
        self.database = database
        self.local_git = local_git or LocalGitService()
        self.github_client = github_client

    @staticmethod
    def status_from_comparison(has_baseline: bool, comparable: bool, linked_files_changed: bool) -> ReviewStatus:
        if not has_baseline:
            return ReviewStatus.NOT_REVIEWED
        if not comparable:
            return ReviewStatus.CANNOT_COMPARE
        return ReviewStatus.NEEDS_REVIEW if linked_files_changed else ReviewStatus.CURRENT

    def evaluate_local(self, link: ResourceLink, repository: Repository) -> ReviewSummary:
        baseline = self.database.get_review_baseline(
            link.resource_type, link.resource_id, link.repository_id, link.resource_parent_id
        )
        if baseline is None:
            return ReviewSummary(link, ReviewStatus.NOT_REVIEWED, message="No review baseline has been created yet.")
        root = repository.local_git_root or repository.local_path
        if not root:
            return ReviewSummary(link, ReviewStatus.CANNOT_COMPARE, baseline_sha=baseline.baseline_sha,
                                 message="Local repository is unavailable.")
        try:
            if not self.local_git.is_commit_available(root, baseline.baseline_sha):
                return ReviewSummary(link, ReviewStatus.CANNOT_COMPARE, baseline_sha=baseline.baseline_sha,
                                     message="Repository history changed or baseline commit is unavailable.")
            head = self.local_git.get_head_sha(root)
            branch = self.local_git.get_current_branch(root)
            if baseline.branch and branch and baseline.branch != branch:
                return ReviewSummary(link, ReviewStatus.CANNOT_COMPARE, baseline_sha=baseline.baseline_sha,
                                     current_sha=head, branch=branch,
                                     message=f"Baseline belongs to branch {baseline.branch}; current branch is {branch}.")
            if baseline.baseline_sha == head:
                self.database.update_repository_sync(repository.id, head, "local_git", branch=branch)
                return ReviewSummary(link, ReviewStatus.CURRENT, baseline_sha=head, current_sha=head, branch=branch)
            cached = self.database.get_repository_change(repository.id, baseline.baseline_sha, head, "local_git")
            if cached:
                changed_files, commits, commit_count = cached.changed_files, cached.commits, cached.commit_count
            else:
                changed_files = self.local_git.get_changed_files(root, baseline.baseline_sha, head)
                commit_count = self.local_git.get_commit_count(root, baseline.baseline_sha, head)
                commits = self.local_git.get_commits(root, baseline.baseline_sha, head)
                self.database.save_repository_change(repository.id, baseline.baseline_sha, head, "local_git",
                                                     commit_count, changed_files, commits)
            changed_files = dedupe_changed_files(changed_files)
            commits = dedupe_commits(commits)
            linked = [item for item in changed_files if path_matches(link.target_type, link.target_value, item.path)]
            status = ReviewStatus.NEEDS_REVIEW if linked else ReviewStatus.CURRENT
            self.database.update_repository_sync(repository.id, head, "local_git", branch=branch)
            return ReviewSummary(link, status, baseline.baseline_sha, head, branch, commit_count,
                                 changed_files, linked, commits, [],
                                 "Linked code changed since the last human review." if linked else "Linked code has not changed since review.")
        except GitRepositoryError as exc:
            logger.warning("Local comparison unavailable for repository %s: %s", repository.id, exc)
            return ReviewSummary(link, ReviewStatus.CANNOT_COMPARE, baseline_sha=baseline.baseline_sha, message=str(exc))

    def evaluate_github(self, link: ResourceLink, repository: Repository) -> ReviewSummary:
        baseline = self.database.get_review_baseline(link.resource_type, link.resource_id, link.repository_id, link.resource_parent_id)
        if baseline is None:
            return ReviewSummary(link, ReviewStatus.NOT_REVIEWED, message="No review baseline has been created yet.")
        if self.github_client is None or not repository.full_name:
            return ReviewSummary(link, ReviewStatus.CANNOT_COMPARE, baseline_sha=baseline.baseline_sha,
                                 message="GitHub comparison is unavailable.")
        owner, name = repository.full_name.split("/", 1)
        branch = baseline.branch or repository.default_branch or "main"
        try:
            branch_data = self.github_client.get_branch(owner, name, branch)
            head = str(branch_data.get("commit", {}).get("sha", ""))
            if not head:
                raise BaselineComparisonError("GitHub did not return a branch HEAD.")
            if head == baseline.baseline_sha:
                return ReviewSummary(link, ReviewStatus.CURRENT, baseline.baseline_sha, head, branch)
            cached = self.database.get_repository_change(repository.id, baseline.baseline_sha, head, "github_api")
            if cached:
                changed, commits, count = cached.changed_files, cached.commits, cached.commit_count
            else:
                compare = self.github_client.compare_commits(owner, name, baseline.baseline_sha, head)
                changed = [ChangedFile(str(f.get("status", "modified"))[:1].upper(), str(f.get("filename", "")),
                                       str(f.get("previous_filename")) if f.get("previous_filename") else None)
                           for f in compare.get("files", [])]
                commits = [CommitInfo(
                    sha=str(c.get("sha", "")), message=str(c.get("commit", {}).get("message", "")).splitlines()[0],
                    author=(c.get("author") or {}).get("login") or c.get("commit", {}).get("author", {}).get("name"),
                    authored_at=c.get("commit", {}).get("author", {}).get("date"), html_url=c.get("html_url"),
                ) for c in compare.get("commits", [])]
                count = int(compare.get("total_commits", len(commits)))
                self.database.save_repository_change(repository.id, baseline.baseline_sha, head, "github_api", count, changed, commits)
            changed = dedupe_changed_files(changed)
            commits = dedupe_commits(commits)
            linked = [item for item in changed if path_matches(link.target_type, link.target_value, item.path)]
            status = ReviewStatus.NEEDS_REVIEW if linked else ReviewStatus.CURRENT
            return ReviewSummary(link, status, baseline.baseline_sha, head, branch, count, changed, linked, commits, [],
                                 "Linked code changed since the last human review." if linked else "Linked code has not changed since review.")
        except Exception as exc:
            logger.warning("GitHub comparison unavailable for repository %s: %s", repository.id, exc)
            return ReviewSummary(link, ReviewStatus.CANNOT_COMPARE, baseline_sha=baseline.baseline_sha, branch=branch, message=str(exc))

    def evaluate(self, link: ResourceLink) -> ReviewSummary:
        repository = self.database.get_repository(link.repository_id)
        if repository is None:
            return ReviewSummary(link, ReviewStatus.CANNOT_COMPARE, message="Repository mapping no longer exists.")
        if repository.local_git_root or repository.local_path:
            local = self.evaluate_local(link, repository)
            if local.status != ReviewStatus.CANNOT_COMPARE or self.github_client is None:
                return local
        if repository.full_name and self.github_client is not None:
            return self.evaluate_github(link, repository)
        baseline = self.database.get_review_baseline(link.resource_type, link.resource_id, link.repository_id, link.resource_parent_id)
        return ReviewSummary(link, ReviewStatus.CANNOT_COMPARE if baseline else ReviewStatus.NOT_REVIEWED,
                             baseline_sha=baseline.baseline_sha if baseline else None,
                             message="No repository history source is currently available.")
