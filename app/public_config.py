from __future__ import annotations

"""Public production configuration bundled with the DevNest desktop client.

These values are intentionally client-visible identifiers. A desktop binary
cannot keep them secret, and they are safe to ship only because authorization
is enforced by GitHub/Supabase and Supabase Row Level Security (RLS).

NEVER put Supabase service-role/secret keys, GitHub client secrets, database
passwords, JWT signing secrets, or any other privileged credential here.

Developers can still override these defaults with the existing DEVNEST_*
environment variables without rebuilding the application.
"""

DEFAULT_GITHUB_CLIENT_ID = "Iv23liQwgwyxC1bVXMgd"
DEFAULT_GITHUB_APP_SLUG = "devnest-local-onur"

DEFAULT_SUPABASE_URL = "https://tceysmcbqrvdjlvlowcj.supabase.co"
DEFAULT_SUPABASE_PUBLISHABLE_KEY = "sb_publishable_u1XVB_rmP5YTLUDC00J3Ig_XUXKsNHS"
