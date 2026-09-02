from __future__ import annotations

import os
from dataclasses import dataclass

from app.public_config import DEFAULT_SUPABASE_PUBLISHABLE_KEY, DEFAULT_SUPABASE_URL


@dataclass(frozen=True, slots=True)
class SupabaseConfig:
    """Supabase client configuration for the desktop application.

    The packaged production URL + publishable key are public client values and
    are bundled so a released DevNest.exe works when launched by double-click.
    Environment variables remain supported as developer/deployment overrides.

    Security must never rely on hiding a publishable key in a desktop binary;
    Supabase RLS and server-side authorization are the data-access boundary.
    """

    url: str = ""
    publishable_key: str = ""

    @classmethod
    def from_environment(cls) -> "SupabaseConfig":
        url = (
            os.getenv("DEVNEST_SUPABASE_URL")
            or os.getenv("SUPABASE_URL")
            or DEFAULT_SUPABASE_URL
        ).strip().rstrip("/")
        key = (
            os.getenv("DEVNEST_SUPABASE_PUBLISHABLE_KEY")
            or os.getenv("DEVNEST_SUPABASE_ANON_KEY")
            or os.getenv("SUPABASE_PUBLISHABLE_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
            or DEFAULT_SUPABASE_PUBLISHABLE_KEY
        ).strip()
        return cls(url=url, publishable_key=key)

    @property
    def configured(self) -> bool:
        return self.url.startswith("https://") and bool(self.publishable_key)
