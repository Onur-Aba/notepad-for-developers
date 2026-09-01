from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ResourceType(StrEnum):
    NOTE = "note"
    DECISION = "decision"
    DIAGRAM_ITEM = "diagram_item"


class TargetType(StrEnum):
    REPOSITORY = "repository"
    DIRECTORY = "directory"
    FILE = "file"
    BRANCH = "branch"
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"


class ReviewStatus(StrEnum):
    CURRENT = "current"
    NEEDS_REVIEW = "needs_review"
    NOT_REVIEWED = "not_reviewed"
    CANNOT_COMPARE = "cannot_compare"


class RepositorySource(StrEnum):
    LOCAL_GIT = "local_git"
    GITHUB_API = "github_api"


class DecisionStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


@dataclass(slots=True)
class Note:
    id: int
    title: str
    content_html: str
    content_plain: str
    created_at: str
    updated_at: str
    is_deleted: bool
    project_id: int | None = None


@dataclass(slots=True)
class NoteSummary:
    id: int
    title: str
    preview: str
    created_at: str
    updated_at: str
    is_deleted: bool
    project_id: int | None = None


@dataclass(slots=True)
class Project:
    id: int
    name: str
    description: str
    created_at: str
    updated_at: str
    archived_at: str | None = None
    trashed_at: str | None = None


@dataclass(slots=True)
class ProjectSummary(Project):
    repository_count: int = 0
    note_count: int = 0
    decision_count: int = 0
    diagram_count: int = 0
    needs_review_count: int = 0
    last_activity: str | None = None


@dataclass(slots=True)
class Repository:
    id: int
    github_repo_id: int | None
    github_node_id: str | None
    owner: str | None
    name: str
    full_name: str | None
    html_url: str | None
    clone_url: str | None
    default_branch: str | None
    is_private: bool
    installation_id: int | None
    local_path: str | None
    local_git_root: str | None
    remote_name: str | None
    language: str | None
    description: str | None
    last_pushed_at: str | None
    last_seen_sha: str | None
    last_checked_at: str | None
    last_successful_check_at: str | None
    last_check_source: str | None
    github_access_state: str
    created_at: str
    updated_at: str


@dataclass(slots=True)
class ProjectRepository:
    project_id: int
    repository_id: int
    monitored_branch: str | None
    created_at: str


@dataclass(slots=True)
class Decision:
    id: int
    project_id: int
    note_id: int
    decision_key: str
    status: str
    title: str
    content_html: str
    content_plain: str
    created_at: str
    updated_at: str


@dataclass(slots=True)
class ResourceLink:
    id: int
    project_id: int
    resource_type: str
    resource_id: str
    resource_parent_id: str
    repository_id: int
    target_type: str
    target_value: str
    github_node_id: str | None
    metadata: dict[str, Any]
    created_at: str


@dataclass(slots=True)
class ReviewBaseline:
    id: int
    resource_type: str
    resource_id: str
    resource_parent_id: str
    repository_id: int
    baseline_sha: str
    branch: str | None
    reviewed_at: str
    created_at: str
    updated_at: str


@dataclass(slots=True)
class ChangedFile:
    status: str
    path: str
    previous_path: str | None = None


@dataclass(slots=True)
class CommitInfo:
    sha: str
    message: str
    author: str | None = None
    authored_at: str | None = None
    html_url: str | None = None

    @property
    def short_sha(self) -> str:
        return self.sha[:8]


@dataclass(slots=True)
class CommitHistoryEntry:
    repository_id: int
    repository_name: str
    commit: CommitInfo
    changed_files: list[ChangedFile] = field(default_factory=list)
    source: str = "local_git"
    files_loaded: bool = True


@dataclass(slots=True)
class PullRequestInfo:
    number: int
    title: str
    state: str
    html_url: str
    merged_at: str | None = None
    updated_at: str | None = None


@dataclass(slots=True)
class RepositoryChange:
    id: int
    repository_id: int
    from_sha: str
    to_sha: str
    source: str
    commit_count: int
    changed_files: list[ChangedFile]
    commits: list[CommitInfo]
    pull_requests: list[PullRequestInfo]
    detected_at: str


@dataclass(slots=True)
class ReviewSummary:
    resource_link: ResourceLink
    status: ReviewStatus
    baseline_sha: str | None = None
    current_sha: str | None = None
    branch: str | None = None
    commit_count: int = 0
    changed_files: list[ChangedFile] = field(default_factory=list)
    linked_changed_files: list[ChangedFile] = field(default_factory=list)
    commits: list[CommitInfo] = field(default_factory=list)
    pull_requests: list[PullRequestInfo] = field(default_factory=list)
    message: str = ""


@dataclass(slots=True)
class GitHubAccount:
    github_user_id: int
    login: str
    avatar_url: str | None
    connected_at: str
    last_validated_at: str | None = None


@dataclass(slots=True)
class GitHubInstallation:
    id: int
    account_login: str
    account_type: str
    account_avatar_url: str | None
    target_type: str | None
    last_synced_at: str


@dataclass(slots=True)
class GitRepositoryInfo:
    root: str
    head_sha: str
    branch: str | None
    remotes: dict[str, str]
