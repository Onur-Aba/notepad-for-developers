from __future__ import annotations

import logging
import os
import re
import subprocess
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from app.models import ChangedFile, CommitInfo, GitRepositoryInfo

logger = logging.getLogger(__name__)


class GitRepositoryError(RuntimeError):
    pass


class LocalGitService:
    def __init__(self, git_executable: str = "git", timeout: float = 12.0) -> None:
        self.git_executable = git_executable
        self.timeout = timeout

    def _run(self, path: str | Path, *args: str) -> str:
        cwd = str(Path(path).expanduser().resolve())
        command = [self.git_executable, *args]
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
            )
        except FileNotFoundError as exc:
            raise GitRepositoryError("Git executable was not found.") from exc
        except subprocess.TimeoutExpired as exc:
            raise GitRepositoryError("Git command timed out.") from exc
        except OSError as exc:
            raise GitRepositoryError(f"Git command could not start: {exc}") from exc
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "Git command failed.").strip()
            raise GitRepositoryError(detail[:800])
        return result.stdout.strip()

    def discover_repository(self, path: str | Path) -> GitRepositoryInfo:
        root = self.get_root(path)
        head = self.get_head_sha(root)
        branch = self.get_current_branch(root)
        remotes = self.get_remotes(root)
        logger.info("Discovered local Git repository at %s", root)
        return GitRepositoryInfo(root=root, head_sha=head, branch=branch, remotes=remotes)

    def get_root(self, path: str | Path) -> str:
        root = self._run(path, "rev-parse", "--show-toplevel")
        if not root:
            raise GitRepositoryError("This folder is not a Git repository.")
        return str(Path(root).resolve())

    def get_head_sha(self, path: str | Path) -> str:
        value = self._run(path, "rev-parse", "HEAD")
        if not re.fullmatch(r"[0-9a-fA-F]{40,64}", value):
            raise GitRepositoryError("Git returned an invalid HEAD commit.")
        return value.lower()

    def get_current_branch(self, path: str | Path) -> str | None:
        value = self._run(path, "branch", "--show-current")
        return value or None

    def get_remotes(self, path: str | Path) -> dict[str, str]:
        output = self._run(path, "remote", "-v")
        remotes: dict[str, str] = {}
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[2] == "(fetch)":
                remotes.setdefault(parts[0], parts[1])
        return remotes

    def get_changed_files(self, path: str | Path, base_sha: str, head_sha: str) -> list[ChangedFile]:
        output = self._run(path, "diff", "--name-status", "--find-renames", f"{base_sha}..{head_sha}")
        changed: list[ChangedFile] = []
        for line in output.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            status = parts[0]
            if status.startswith("R") and len(parts) >= 3:
                changed.append(ChangedFile(status="R", path=normalize_repo_path(parts[2]), previous_path=normalize_repo_path(parts[1])))
            elif len(parts) >= 2:
                changed.append(ChangedFile(status=status[:1], path=normalize_repo_path(parts[1])))
        return changed

    def get_commit_count(self, path: str | Path, base_sha: str, head_sha: str) -> int:
        output = self._run(path, "rev-list", "--count", f"{base_sha}..{head_sha}")
        try:
            return int(output)
        except ValueError as exc:
            raise GitRepositoryError("Git returned an invalid commit count.") from exc

    def get_commits(self, path: str | Path, base_sha: str, head_sha: str, limit: int = 100) -> list[CommitInfo]:
        fmt = "%H%x1f%an%x1f%aI%x1f%s"
        output = self._run(path, "log", f"--max-count={max(1, limit)}", f"--format={fmt}", f"{base_sha}..{head_sha}")
        commits: list[CommitInfo] = []
        for line in output.splitlines():
            parts = line.split("\x1f", 3)
            if len(parts) == 4:
                commits.append(CommitInfo(sha=parts[0], author=parts[1], authored_at=parts[2], message=parts[3]))
        return commits

    def get_commit_history(self, path: str | Path, limit: int | None = None) -> list[tuple[CommitInfo, list[ChangedFile]]]:
        """Return repository history newest-first with the files changed by each commit.

        This intentionally uses one read-only ``git log --name-status`` command instead
        of one subprocess per commit, so even long project histories can be loaded in a
        background worker without hammering the repository.
        """
        fmt = "%x1e%H%x1f%an%x1f%aI%x1f%s"
        args = ["log", "--date=iso-strict", f"--format={fmt}", "--name-status", "--find-renames", "--root"]
        if limit is not None:
            args.insert(1, f"--max-count={max(1, int(limit))}")
        output = self._run(path, *args)
        history: list[tuple[CommitInfo, list[ChangedFile]]] = []
        for record in output.split("\x1e"):
            record = record.strip("\n\r ")
            if not record:
                continue
            lines = record.splitlines()
            header = lines[0].split("\x1f", 3)
            if len(header) != 4:
                continue
            commit = CommitInfo(sha=header[0].strip(), author=header[1].strip() or None,
                                authored_at=header[2].strip() or None, message=header[3].strip())
            changed: list[ChangedFile] = []
            for line in lines[1:]:
                if not line.strip():
                    continue
                parts = line.split("\t")
                status = parts[0].strip()
                if status.startswith("R") and len(parts) >= 3:
                    changed.append(ChangedFile(status="R", path=normalize_repo_path(parts[2]),
                                               previous_path=normalize_repo_path(parts[1])))
                elif len(parts) >= 2:
                    changed.append(ChangedFile(status=status[:1], path=normalize_repo_path(parts[1])))
            history.append((commit, changed))
        return history

    def get_commit_changed_files(self, path: str | Path, sha: str) -> list[ChangedFile]:
        output = self._run(path, "diff-tree", "--no-commit-id", "--name-status", "-r", "--root", "--find-renames", sha)
        changed: list[ChangedFile] = []
        for line in output.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            status = parts[0].strip()
            if status.startswith("R") and len(parts) >= 3:
                changed.append(ChangedFile(status="R", path=normalize_repo_path(parts[2]), previous_path=normalize_repo_path(parts[1])))
            elif len(parts) >= 2:
                changed.append(ChangedFile(status=status[:1], path=normalize_repo_path(parts[1])))
        return changed

    def is_commit_available(self, path: str | Path, sha: str) -> bool:
        try:
            self._run(path, "cat-file", "-e", f"{sha}^{{commit}}")
            return True
        except GitRepositoryError:
            return False

    def status_porcelain(self, path: str | Path) -> str:
        return self._run(path, "status", "--porcelain")

    @staticmethod
    def github_full_name_from_remotes(remotes: dict[str, str]) -> tuple[str, str] | None:
        preferred = ["origin", *[name for name in remotes if name != "origin"]]
        for name in preferred:
            url = remotes.get(name)
            if not url:
                continue
            full_name = parse_github_remote(url)
            if full_name:
                return name, full_name
        return None


def normalize_repo_path(value: str) -> str:
    raw = value.strip().replace("\\", "/")
    while raw.startswith("./"):
        raw = raw[2:]
    raw = raw.lstrip("/")
    normalized = str(PurePosixPath(raw)) if raw else ""
    return "" if normalized == "." else normalized


def path_matches(target_type: str, target_value: str, changed_path: str) -> bool:
    changed = normalize_repo_path(changed_path)
    target = normalize_repo_path(target_value)
    if target_type == "repository":
        return bool(changed)
    if target_type == "file":
        return changed == target
    if target_type == "directory":
        if not target:
            return bool(changed)
        prefix = target.rstrip("/") + "/"
        return changed == target.rstrip("/") or changed.startswith(prefix)
    if target_type == "branch":
        return bool(changed)
    # Commit and PR references are static implementation links, not path monitors.
    return False


def parse_github_remote(url: str) -> str | None:
    value = url.strip()
    if not value:
        return None
    owner_repo: str | None = None
    if value.startswith("git@github.com:"):
        owner_repo = value.split(":", 1)[1]
    elif value.startswith("ssh://") or value.startswith("http://") or value.startswith("https://"):
        parsed = urlparse(value)
        if (parsed.hostname or "").lower() == "github.com":
            owner_repo = parsed.path.lstrip("/")
    if not owner_repo:
        return None
    if owner_repo.endswith(".git"):
        owner_repo = owner_repo[:-4]
    parts = [p for p in owner_repo.split("/") if p]
    if len(parts) != 2:
        return None
    return f"{parts[0]}/{parts[1]}"
