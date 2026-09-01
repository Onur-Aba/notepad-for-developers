from __future__ import annotations

import ctypes
import json
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass

SERVICE_NAME = "DevNest.GitHub"
ACCOUNT_NAME = "github-user-token"


@dataclass(slots=True)
class StoredCredentials:
    access_token: str | None = None
    refresh_token: str | None = None
    expires_at: str | None = None
    refresh_expires_at: str | None = None


class CredentialStore(ABC):
    @abstractmethod
    def get(self) -> StoredCredentials: ...

    @abstractmethod
    def set(self, credentials: StoredCredentials) -> None: ...

    @abstractmethod
    def delete(self) -> None: ...

    def get_github_access_token(self) -> str | None:
        return self.get().access_token

    def set_github_access_token(self, token: str) -> None:
        current = self.get()
        current.access_token = token
        self.set(current)

    def delete_github_access_token(self) -> None:
        self.delete()


def _credentials_to_json(credentials: StoredCredentials) -> str:
    return json.dumps({
        "access_token": credentials.access_token,
        "refresh_token": credentials.refresh_token,
        "expires_at": credentials.expires_at,
        "refresh_expires_at": credentials.refresh_expires_at,
    }, separators=(",", ":"))


def _credentials_from_json(raw: str | None) -> StoredCredentials:
    if not raw:
        return StoredCredentials()
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return StoredCredentials()
    if not isinstance(data, dict):
        return StoredCredentials()
    return StoredCredentials(
        access_token=data.get("access_token"),
        refresh_token=data.get("refresh_token"),
        expires_at=data.get("expires_at"),
        refresh_expires_at=data.get("refresh_expires_at"),
    )


class _FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", ctypes.c_uint32), ("dwHighDateTime", ctypes.c_uint32)]


class _CREDENTIALW(ctypes.Structure):
    _fields_ = [
        ("Flags", ctypes.c_uint32),
        ("Type", ctypes.c_uint32),
        ("TargetName", ctypes.c_wchar_p),
        ("Comment", ctypes.c_wchar_p),
        ("LastWritten", _FILETIME),
        ("CredentialBlobSize", ctypes.c_uint32),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", ctypes.c_uint32),
        ("AttributeCount", ctypes.c_uint32),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", ctypes.c_wchar_p),
        ("UserName", ctypes.c_wchar_p),
    ]


class WindowsCredentialStore(CredentialStore):
    """Native Windows Credential Manager store.

    It intentionally uses the same service/username pair as the previous
    python-keyring implementation. This keeps existing DevNest credentials
    readable while removing runtime dependency on keyring backend discovery in
    a PyInstaller EXE.
    """

    CRED_TYPE_GENERIC = 1
    CRED_PERSIST_ENTERPRISE = 3
    ERROR_NOT_FOUND = 1168
    CREDENTIALW = _CREDENTIALW

    def __init__(self) -> None:
        if sys.platform != "win32":
            raise RuntimeError("Windows Credential Manager is only available on Windows.")
        self._advapi = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
        self._advapi.CredReadW.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.POINTER(self.CREDENTIALW)),
        ]
        self._advapi.CredReadW.restype = ctypes.c_int
        self._advapi.CredWriteW.argtypes = [ctypes.POINTER(self.CREDENTIALW), ctypes.c_uint32]
        self._advapi.CredWriteW.restype = ctypes.c_int
        self._advapi.CredDeleteW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32]
        self._advapi.CredDeleteW.restype = ctypes.c_int
        self._advapi.CredFree.argtypes = [ctypes.c_void_p]
        self._advapi.CredFree.restype = None

    @staticmethod
    def _decode_blob(raw: bytes) -> str:
        if not raw:
            return ""
        # python-keyring's Windows backend writes UTF-16. Older/fallback
        # versions may contain UTF-8, so accept both.
        if len(raw) % 2 == 0:
            try:
                text = raw.decode("utf-16-le").lstrip("\ufeff").rstrip("\x00")
                if text:
                    return text
            except UnicodeDecodeError:
                pass
        return raw.decode("utf-8").rstrip("\x00")

    def _read_target(self, target: str) -> tuple[str | None, str | None]:
        pointer = ctypes.POINTER(self.CREDENTIALW)()
        ctypes.set_last_error(0)
        ok = self._advapi.CredReadW(target, self.CRED_TYPE_GENERIC, 0, ctypes.byref(pointer))
        if not ok:
            error = ctypes.get_last_error()
            if error == self.ERROR_NOT_FOUND:
                return None, None
            raise OSError(error, "Windows Credential Manager could not read the DevNest credential.")
        try:
            credential = pointer.contents
            blob = ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
            return credential.UserName, self._decode_blob(blob)
        finally:
            self._advapi.CredFree(pointer)

    def get(self) -> StoredCredentials:
        # python-keyring normally stores the first credential under the service
        # name. Its collision fallback uses username@service; support both.
        for target in (SERVICE_NAME, f"{ACCOUNT_NAME}@{SERVICE_NAME}"):
            username, raw = self._read_target(target)
            if raw is not None and (username in {None, ACCOUNT_NAME} or target != SERVICE_NAME):
                return _credentials_from_json(raw)
        return StoredCredentials()

    def set(self, credentials: StoredCredentials) -> None:
        raw = _credentials_to_json(credentials).encode("utf-16-le")
        blob_buffer = ctypes.create_string_buffer(raw)
        credential = self.CREDENTIALW()
        credential.Flags = 0
        credential.Type = self.CRED_TYPE_GENERIC
        credential.TargetName = SERVICE_NAME
        credential.Comment = "DevNest GitHub user access token"
        credential.CredentialBlobSize = len(raw)
        credential.CredentialBlob = ctypes.cast(blob_buffer, ctypes.POINTER(ctypes.c_ubyte))
        credential.Persist = self.CRED_PERSIST_ENTERPRISE
        credential.AttributeCount = 0
        credential.Attributes = None
        credential.TargetAlias = None
        credential.UserName = ACCOUNT_NAME
        ctypes.set_last_error(0)
        if not self._advapi.CredWriteW(ctypes.byref(credential), 0):
            error = ctypes.get_last_error()
            raise OSError(error, "Windows Credential Manager could not save the DevNest credential.")

    def delete(self) -> None:
        for target in (SERVICE_NAME, f"{ACCOUNT_NAME}@{SERVICE_NAME}"):
            ctypes.set_last_error(0)
            ok = self._advapi.CredDeleteW(target, self.CRED_TYPE_GENERIC, 0)
            if not ok:
                error = ctypes.get_last_error()
                if error != self.ERROR_NOT_FOUND:
                    raise OSError(error, "Windows Credential Manager could not delete the DevNest credential.")


class KeyringCredentialStore(CredentialStore):
    """Portable OS credential-store implementation for non-Windows platforms."""

    def __init__(self) -> None:
        try:
            import keyring  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Secure credential support requires the 'keyring' package.") from exc
        self._keyring = keyring

    def get(self) -> StoredCredentials:
        return _credentials_from_json(self._keyring.get_password(SERVICE_NAME, ACCOUNT_NAME))

    def set(self, credentials: StoredCredentials) -> None:
        self._keyring.set_password(SERVICE_NAME, ACCOUNT_NAME, _credentials_to_json(credentials))

    def delete(self) -> None:
        try:
            self._keyring.delete_password(SERVICE_NAME, ACCOUNT_NAME)
        except Exception as exc:
            if "not found" not in str(exc).lower():
                raise


class InMemoryCredentialStore(CredentialStore):
    def __init__(self) -> None:
        self.credentials = StoredCredentials()

    def get(self) -> StoredCredentials:
        return StoredCredentials(
            self.credentials.access_token, self.credentials.refresh_token,
            self.credentials.expires_at, self.credentials.refresh_expires_at,
        )

    def set(self, credentials: StoredCredentials) -> None:
        self.credentials = StoredCredentials(
            credentials.access_token, credentials.refresh_token,
            credentials.expires_at, credentials.refresh_expires_at,
        )

    def delete(self) -> None:
        self.credentials = StoredCredentials()


class UnavailableCredentialStore(CredentialStore):
    """Offline-safe fallback used only when the OS credential backend is unavailable."""

    def get(self) -> StoredCredentials:
        return StoredCredentials()

    def set(self, credentials: StoredCredentials) -> None:
        raise RuntimeError("Secure OS credential storage is unavailable.")

    def delete(self) -> None:
        return None


def create_default_credential_store() -> CredentialStore:
    if sys.platform == "win32":
        try:
            return WindowsCredentialStore()
        except Exception:
            # Keep a safe fallback for unusual Windows environments. keyring
            # still targets Windows Credential Manager when its backend works.
            try:
                return KeyringCredentialStore()
            except Exception:
                return UnavailableCredentialStore()
    try:
        return KeyringCredentialStore()
    except Exception:
        return UnavailableCredentialStore()
