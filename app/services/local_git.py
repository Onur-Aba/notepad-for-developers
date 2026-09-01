from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(RuntimeError):
    pass


@dataclass(slots=True)
class GitRepositoryInfo:
    root: Path
    head_sha: str
    branch: str | None
    remote_url: str | None
    github_owner: str | None
    github_repo: str | None


def _run_git(path: Path | str, *args: str) -> str:
    working = Path(path)
    try:
        completed = subprocess.run(
            ["git", "-C", str(working), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except FileNotFoundError as exc:
        raise GitError("Git was not found. Install Git for Windows and restart DevNest.") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitError("Git command timed out.") from exc
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "Unknown git error"
        raise GitError(message)
    return completed.stdout.strip()


def parse_github_remote(url: str | None) -> tuple[str | None, str | None]:
    if not url:
        return None, None
    value = url.strip()
    patterns = [
        r"^(?:https?://|git://)github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$",
        r"^git@github\.com:([^/]+)/(.+?)(?:\.git)?$",
        r"^ssh://git@github\.com/([^/]+)/(.+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.match(pattern, value, flags=re.IGNORECASE)
        if match:
            return match.group(1), match.group(2)
    return None, None


def inspect_repository(path: Path | str) -> GitRepositoryInfo:
    path = Path(path).expanduser().resolve()
    root_text = _run_git(path, "rev-parse", "--show-toplevel")
    root = Path(root_text).resolve()
    head = _run_git(root, "rev-parse", "HEAD")
    branch = _run_git(root, "branch", "--show-current") or None
    try:
        remote = _run_git(root, "remote", "get-url", "origin") or None
    except GitError:
        remote = None
    owner, repo = parse_github_remote(remote)
    return GitRepositoryInfo(root, head, branch, remote, owner, repo)


def current_head(path: Path | str) -> str:
    return _run_git(path, "rev-parse", "HEAD")


def default_branch(path: Path | str) -> str | None:
    try:
        symbolic = _run_git(path, "symbolic-ref", "refs/remotes/origin/HEAD")
        return symbolic.rsplit("/", 1)[-1] if symbolic else None
    except GitError:
        try:
            return _run_git(path, "branch", "--show-current") or None
        except GitError:
            return None


def changed_files(path: Path | str, base_sha: str, head_sha: str) -> list[str]:
    if base_sha == head_sha:
        return []
    output = _run_git(path, "diff", "--name-only", "--no-renames", f"{base_sha}..{head_sha}")
    return [line.replace("\\", "/").strip("/") for line in output.splitlines() if line.strip()]


def commit_count(path: Path | str, base_sha: str, head_sha: str) -> int:
    if base_sha == head_sha:
        return 0
    value = _run_git(path, "rev-list", "--count", f"{base_sha}..{head_sha}")
    try:
        return int(value)
    except ValueError:
        return 0


def recent_commits(path: Path | str, limit: int = 50) -> list[dict[str, str]]:
    fmt = "%H%x1f%h%x1f%s%x1f%an%x1f%aI%x1e"
    output = _run_git(path, "log", f"--max-count={max(1, min(limit, 200))}", f"--pretty=format:{fmt}")
    result: list[dict[str, str]] = []
    for record in output.split("\x1e"):
        parts = record.strip().split("\x1f")
        if len(parts) == 5:
            result.append({"sha": parts[0], "short_sha": parts[1], "title": parts[2], "author": parts[3], "date": parts[4]})
    return result
