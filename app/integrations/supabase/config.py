from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SupabaseConfig:
    """Runtime-only Supabase configuration.

    DevNest intentionally does not ship a project URL or client key in source.
    Desktop deployments supply them through environment variables. A Supabase
    publishable/legacy anon key is a *client* key (RLS is the security boundary),
    but keeping deployment configuration out of the binary makes projects easier
    to rotate and avoids accidental coupling to one hosted backend.
    """

    url: str = ""
    publishable_key: str = ""

    @classmethod
    def from_environment(cls) -> "SupabaseConfig":
        url = (os.getenv("DEVNEST_SUPABASE_URL") or os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
        key = (
            os.getenv("DEVNEST_SUPABASE_PUBLISHABLE_KEY")
            or os.getenv("DEVNEST_SUPABASE_ANON_KEY")
            or os.getenv("SUPABASE_PUBLISHABLE_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
            or ""
        ).strip()
        return cls(url=url, publishable_key=key)

    @property
    def configured(self) -> bool:
        return self.url.startswith("https://") and bool(self.publishable_key)
