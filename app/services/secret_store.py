from __future__ import annotations

import ctypes
import json
import os
from ctypes import wintypes
from pathlib import Path


class SecretStoreError(RuntimeError):
    pass


_TARGET = "DevNest:GitHub"
_CRED_TYPE_GENERIC = 1
_CRED_PERSIST_LOCAL_MACHINE = 2
_ERROR_NOT_FOUND = 1168


if os.name == "nt":
    class FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

    class CREDENTIALW(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR), ("LastWritten", FILETIME), ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)), ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR),
        ]

    _advapi32 = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    _CredWriteW = _advapi32.CredWriteW
    _CredWriteW.argtypes = [ctypes.POINTER(CREDENTIALW), wintypes.DWORD]
    _CredWriteW.restype = wintypes.BOOL
    _CredReadW = _advapi32.CredReadW
    _CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIALW))]
    _CredReadW.restype = wintypes.BOOL
    _CredDeleteW = _advapi32.CredDeleteW
    _CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    _CredDeleteW.restype = wintypes.BOOL
    _CredFree = _advapi32.CredFree
    _CredFree.argtypes = [ctypes.c_void_p]


def _fallback_file() -> Path:
    # Development-only fallback for non-Windows platforms. Production Windows
    # builds use Credential Manager and never write tokens here.
    return Path.home() / ".devnest_github_credentials.json"


def save_github_credentials(data: dict[str, object]) -> None:
    payload = json.dumps(data, separators=(",", ":")).encode("utf-8")
    if os.name != "nt":
        path = _fallback_file(); path.write_bytes(payload)
        try: path.chmod(0o600)
        except OSError: pass
        return
    blob = (ctypes.c_ubyte * len(payload)).from_buffer_copy(payload)
    credential = CREDENTIALW()
    credential.Type = _CRED_TYPE_GENERIC
    credential.TargetName = _TARGET
    credential.CredentialBlobSize = len(payload)
    credential.CredentialBlob = ctypes.cast(blob, ctypes.POINTER(ctypes.c_ubyte))
    credential.Persist = _CRED_PERSIST_LOCAL_MACHINE
    credential.UserName = "github"
    if not _CredWriteW(ctypes.byref(credential), 0):
        raise SecretStoreError(f"Windows Credential Manager error: {ctypes.get_last_error()}")


def load_github_credentials() -> dict[str, object] | None:
    if os.name != "nt":
        path = _fallback_file()
        if not path.exists(): return None
        try: return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError): return None
    pointer = ctypes.POINTER(CREDENTIALW)()
    if not _CredReadW(_TARGET, _CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)):
        error = ctypes.get_last_error()
        if error == _ERROR_NOT_FOUND: return None
        raise SecretStoreError(f"Windows Credential Manager error: {error}")
    try:
        credential = pointer.contents
        raw = ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
        decoded = json.loads(raw.decode("utf-8"))
        return decoded if isinstance(decoded, dict) else None
    finally:
        _CredFree(pointer)


def clear_github_credentials() -> None:
    if os.name != "nt":
        try: _fallback_file().unlink()
        except FileNotFoundError: pass
        return
    if not _CredDeleteW(_TARGET, _CRED_TYPE_GENERIC, 0):
        error = ctypes.get_last_error()
        if error != _ERROR_NOT_FOUND:
            raise SecretStoreError(f"Windows Credential Manager error: {error}")
