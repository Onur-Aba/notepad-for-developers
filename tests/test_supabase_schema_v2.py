from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = (ROOT / "supabase" / "devnest_schema.sql").read_text(encoding="utf-8")


def test_cloud_rows_have_optimistic_revision_audit_columns() -> None:
    assert "cloud_projects add column if not exists revision" in SCHEMA
    assert "cloud_resources add column if not exists revision" in SCHEMA
    assert "cloud_projects add column if not exists updated_by" in SCHEMA
    assert "cloud_resources add column if not exists updated_by" in SCHEMA
    assert "devnest_cloud_resource_revision" in SCHEMA


def test_role_rpc_no_longer_accepts_manual_rank() -> None:
    assert "drop function if exists public.team_create_role(uuid,text,integer,jsonb)" in SCHEMA
    assert "drop function if exists public.team_update_role(uuid,text,integer,jsonb)" in SCHEMA
    assert "team_create_role(p_team_id uuid, p_name text, p_permissions jsonb)" in SCHEMA
    assert "team_update_role(p_role_id uuid, p_name text, p_permissions jsonb)" in SCHEMA
    assert "devnest_permission_rank" in SCHEMA


def test_team_snapshot_rpcs_exist_for_fast_page_load() -> None:
    assert "function public.team_overview()" in SCHEMA
    assert "function public.team_detail_snapshot(p_team_id uuid)" in SCHEMA
    assert "grant execute on function public.team_overview() to authenticated" in SCHEMA
