from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.integrations.supabase.client import SupabaseClient, SupabaseError
from app.integrations.supabase.config import SupabaseConfig


def test_supabase_config_prefers_publishable_key(monkeypatch):
    monkeypatch.setenv("DEVNEST_SUPABASE_URL", "https://example.supabase.co/")
    monkeypatch.setenv("DEVNEST_SUPABASE_PUBLISHABLE_KEY", "sb_publishable_test")
    monkeypatch.setenv("DEVNEST_SUPABASE_ANON_KEY", "legacy")
    config = SupabaseConfig.from_environment()
    assert config.url == "https://example.supabase.co"
    assert config.publishable_key == "sb_publishable_test"
    assert config.configured


def test_registration_validation_rejects_sql_injection_username():
    with pytest.raises(SupabaseError):
        SupabaseClient.validate_registration("Ada", "Lovelace", "ada';drop table profiles;--", "ada@example.com", "very-secure-pass")


def test_registration_validation_rejects_short_password():
    with pytest.raises(SupabaseError):
        SupabaseClient.validate_registration("Ada", "Lovelace", "ada_dev", "ada@example.com", "123")


def test_rest_path_url_encodes_filter_values():
    path = SupabaseClient._rest_path("profiles", {"username": "eq.user-name", "select": "id,username"})
    assert path.startswith("/rest/v1/profiles?")
    assert "username=eq.user-name" in path
    assert "select=id,username" in path


def test_supabase_sql_enables_rls_and_never_uses_service_role_client_key():
    sql = (Path(__file__).resolve().parents[1] / "supabase" / "devnest_schema.sql").read_text(encoding="utf-8").lower()
    assert "enable row level security" in sql
    assert "revoke all on all tables in schema public" not in sql
    assert "team_can_manage_member" in sql
    assert "team_can_view_resource" in sql
    assert "service_role" in sql  # documentation warning is present
    assert "grant execute" in sql


def test_supabase_config_uses_packaged_public_defaults_without_environment(monkeypatch):
    for name in (
        "DEVNEST_SUPABASE_URL",
        "SUPABASE_URL",
        "DEVNEST_SUPABASE_PUBLISHABLE_KEY",
        "DEVNEST_SUPABASE_ANON_KEY",
        "SUPABASE_PUBLISHABLE_KEY",
        "SUPABASE_ANON_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    config = SupabaseConfig.from_environment()
    assert config.url == "https://tceysmcbqrvdjlvlowcj.supabase.co"
    assert config.publishable_key.startswith("sb_publishable_")
    assert config.configured
