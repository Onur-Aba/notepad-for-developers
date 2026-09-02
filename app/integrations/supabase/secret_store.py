from __future__ import annotations

import json
import os
from pathlib import Path

try:
    import keyring
except Exception:  # pragma: no cover - runtime fallback
    keyring = None

SERVICE = "DevNest.Supabase"
ACCOUNT = "supabase-session"


def _fallback_path() -> Path:
    return Path.home() / ".devnest_supabase_session.json"


def load_session() -> dict[str, object] | None:
    raw: str | None = None
    if keyring is not None:
        try:
            raw = keyring.get_password(SERVICE, ACCOUNT)
        except Exception:
            raw = None
    if raw is None and os.name != "nt":
        path = _fallback_path()
        if path.exists():
            try:
                raw = path.read_text(encoding="utf-8")
            except OSError:
                raw = None
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def save_session(value: dict[str, object]) -> None:
    raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if keyring is not None:
        try:
            keyring.set_password(SERVICE, ACCOUNT, raw)
            return
        except Exception:
            if os.name == "nt":
                raise RuntimeError("Windows secure credential storage is unavailable.")
    if os.name == "nt":
        raise RuntimeError("Windows secure credential storage is unavailable.")
    path = _fallback_path()
    path.write_text(raw, encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def clear_session() -> None:
    if keyring is not None:
        try:
            keyring.delete_password(SERVICE, ACCOUNT)
        except Exception:
            pass
    if os.name != "nt":
        try:
            _fallback_path().unlink()
        except FileNotFoundError:
            pass
