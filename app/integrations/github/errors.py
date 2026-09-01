from __future__ import annotations


class GitHubError(RuntimeError):
    pass


class GitHubConfigurationError(GitHubError):
    pass


class GitHubAuthenticationError(GitHubError):
    pass


class GitHubAuthorizationPending(GitHubAuthenticationError):
    pass


class GitHubSlowDown(GitHubAuthenticationError):
    pass


class GitHubDeviceFlowExpired(GitHubAuthenticationError):
    pass


class GitHubAccessDenied(GitHubAuthenticationError):
    pass


class GitHubRateLimitError(GitHubError):
    def __init__(self, message: str, reset_at: str | None = None) -> None:
        super().__init__(message)
        self.reset_at = reset_at


class GitHubPermissionError(GitHubError):
    pass


class GitHubNotFoundError(GitHubError):
    pass


class GitHubValidationError(GitHubError):
    pass


class GitHubNetworkError(GitHubError):
    pass


class GitHubTemporaryError(GitHubError):
    pass
