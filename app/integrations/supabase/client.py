from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from .config import SupabaseConfig
from .secret_store import clear_session, load_session, save_session

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{2,31}$")


class SupabaseError(RuntimeError):
    def __init__(self, message: str, *, status: int | None = None, code: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


@dataclass(slots=True)
class SupabaseSession:
    access_token: str
    refresh_token: str
    expires_at: int
    user_id: str
    email: str = ""
    username: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "user_id": self.user_id,
            "email": self.email,
            "username": self.username,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, object]) -> "SupabaseSession | None":
        try:
            return cls(
                access_token=str(raw["access_token"]),
                refresh_token=str(raw["refresh_token"]),
                expires_at=int(raw["expires_at"]),
                user_id=str(raw["user_id"]),
                email=str(raw.get("email") or ""),
                username=str(raw.get("username") or ""),
            )
        except (KeyError, TypeError, ValueError):
            return None


class SupabaseClient:
    """Small dependency-free Supabase Auth/PostgREST client.

    Every database request uses the signed-in user's JWT. The application never
    accepts or uses a service-role/secret key; authorization belongs to RLS and
    the SECURITY DEFINER RPC functions in ``supabase/devnest_schema.sql``.
    """

    def __init__(self, config: SupabaseConfig) -> None:
        self.config = config
        raw = load_session()
        self._session = SupabaseSession.from_dict(raw) if raw else None

    @property
    def configured(self) -> bool:
        return self.config.configured

    @property
    def signed_in(self) -> bool:
        return self._session is not None

    @property
    def session(self) -> SupabaseSession | None:
        return self._session

    @staticmethod
    def validate_registration(first_name: str, last_name: str, username: str, email: str, password: str) -> None:
        if not (1 <= len(first_name.strip()) <= 80) or not (1 <= len(last_name.strip()) <= 80):
            raise SupabaseError("Name and surname are required and must be at most 80 characters.")
        if not _USERNAME_RE.fullmatch(username.strip()):
            raise SupabaseError("Username must be 3-32 characters and use letters, numbers, _, . or -.")
        if len(email.strip()) > 254 or "@" not in email or email.startswith("@") or email.endswith("@"):
            raise SupabaseError("Enter a valid email address.")
        if len(password) < 10 or len(password) > 128:
            raise SupabaseError("Password must be between 10 and 128 characters.")

    def sign_up(self, first_name: str, last_name: str, username: str, email: str, password: str) -> bool:
        self._require_config()
        self.validate_registration(first_name, last_name, username, email, password)
        data = self._request_json(
            "POST", "/auth/v1/signup", auth=False,
            body={
                "email": email.strip(),
                "password": password,
                "data": {
                    "first_name": first_name.strip(),
                    "last_name": last_name.strip(),
                    "username": username.strip(),
                },
            },
        )
        if isinstance(data, dict) and data.get("access_token"):
            self._save_auth_response(data)
            self.refresh_profile()
            return True
        # Email-confirmation projects return a user but no session.
        return False

    def sign_in(self, email: str, password: str) -> SupabaseSession:
        self._require_config()
        if not email.strip() or not password:
            raise SupabaseError("Email and password are required.")
        data = self._request_json(
            "POST", "/auth/v1/token?grant_type=password", auth=False,
            body={"email": email.strip(), "password": password},
        )
        if not isinstance(data, dict) or not data.get("access_token"):
            raise SupabaseError("Supabase did not return a login session.")
        self._save_auth_response(data)
        self.refresh_profile()
        assert self._session is not None
        return self._session

    def sign_out(self) -> None:
        if self._session and self.configured:
            try:
                self._request_json("POST", "/auth/v1/logout", body={}, auth=True)
            except SupabaseError:
                pass
        self._session = None
        clear_session()

    def refresh_profile(self) -> dict[str, object] | None:
        if not self._session:
            return None
        rows = self.table_select("profiles", {"id": f"eq.{self._session.user_id}", "select": "id,username,first_name,last_name"})
        if rows:
            username = str(rows[0].get("username") or "")
            self._session.username = username
            save_session(self._session.as_dict())
            return rows[0]
        return None

    def ensure_session(self) -> SupabaseSession:
        self._require_config()
        if not self._session:
            raise SupabaseError("Sign in to DevNest Online first.", status=401)
        if self._session.expires_at <= int(time.time()) + 60:
            data = self._request_json(
                "POST", "/auth/v1/token?grant_type=refresh_token", auth=False,
                body={"refresh_token": self._session.refresh_token},
            )
            if not isinstance(data, dict) or not data.get("access_token"):
                self.sign_out()
                raise SupabaseError("Your online session expired. Sign in again.", status=401)
            self._save_auth_response(data)
        return self._session

    def table_select(self, table: str, query: dict[str, str] | None = None) -> list[dict[str, Any]]:
        data = self._request_json("GET", self._rest_path(table, query), auth=True)
        return data if isinstance(data, list) else []

    def table_insert(self, table: str, body: dict[str, object] | list[dict[str, object]], *,
                     upsert_on_conflict: str | None = None) -> list[dict[str, Any]]:
        query = {"on_conflict": upsert_on_conflict} if upsert_on_conflict else None
        prefer = "return=representation"
        if upsert_on_conflict:
            prefer = "resolution=merge-duplicates,return=representation"
        data = self._request_json("POST", self._rest_path(table, query), body=body, auth=True, prefer=prefer)
        return data if isinstance(data, list) else []

    def table_update(self, table: str, filters: dict[str, str], body: dict[str, object]) -> list[dict[str, Any]]:
        data = self._request_json("PATCH", self._rest_path(table, filters), body=body, auth=True, prefer="return=representation")
        return data if isinstance(data, list) else []

    def table_delete(self, table: str, filters: dict[str, str]) -> list[dict[str, Any]]:
        data = self._request_json("DELETE", self._rest_path(table, filters), auth=True, prefer="return=representation")
        return data if isinstance(data, list) else []

    def rpc(self, function_name: str, args: dict[str, object] | None = None) -> Any:
        return self._request_json("POST", f"/rest/v1/rpc/{urllib.parse.quote(function_name, safe='')}", body=args or {}, auth=True)

    def _save_auth_response(self, data: dict[str, Any]) -> None:
        user = data.get("user") if isinstance(data.get("user"), dict) else {}
        expires_in = int(data.get("expires_in") or 3600)
        self._session = SupabaseSession(
            access_token=str(data.get("access_token") or ""),
            refresh_token=str(data.get("refresh_token") or ""),
            expires_at=int(time.time()) + max(60, expires_in),
            user_id=str(user.get("id") or (self._session.user_id if self._session else "")),
            email=str(user.get("email") or (self._session.email if self._session else "")),
            username=self._session.username if self._session else "",
        )
        if not self._session.user_id:
            raise SupabaseError("Login response did not include a user id.")
        save_session(self._session.as_dict())

    def _require_config(self) -> None:
        if not self.configured:
            raise SupabaseError(
                "Supabase is not configured. Set DEVNEST_SUPABASE_URL and DEVNEST_SUPABASE_PUBLISHABLE_KEY (or DEVNEST_SUPABASE_ANON_KEY)."
            )

    @staticmethod
    def _rest_path(table: str, query: dict[str, str] | None) -> str:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
            raise SupabaseError("Invalid table name.")
        if not query:
            return f"/rest/v1/{table}"
        encoded = urllib.parse.urlencode(query, safe=".*(),:-_\"")
        return f"/rest/v1/{table}?{encoded}"

    def _request_json(self, method: str, path: str, *, body: object | None = None,
                      auth: bool = True, prefer: str | None = None) -> Any:
        self._require_config()
        if auth:
            session = self.ensure_session() if path != "/auth/v1/token?grant_type=refresh_token" else self._session
        else:
            session = None
        url = f"{self.config.url}{path}"
        payload = None if body is None else json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers = {
            "apikey": self.config.publishable_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "DevNest-Desktop/2",
        }
        if session:
            headers["Authorization"] = f"Bearer {session.access_token}"
        if prefer:
            headers["Prefer"] = prefer
        request = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read()
                if not raw:
                    return None
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")[:4096]
            message = f"Supabase request failed ({exc.code})."
            code = None
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    message = str(parsed.get("msg") or parsed.get("message") or parsed.get("error_description") or message)
                    code = str(parsed.get("code") or parsed.get("error_code") or "") or None
            except json.JSONDecodeError:
                pass
            # Never include request headers/tokens or arbitrary response dumps.
            raise SupabaseError(message, status=exc.code, code=code) from exc
        except urllib.error.URLError as exc:
            raise SupabaseError(f"Could not reach Supabase: {exc.reason}") from exc
