from __future__ import annotations

from typing import Mapping

# Keep this list in sync with CloudService.Permissions and the Supabase schema.
TEAM_PERMISSION_KEYS: tuple[str, ...] = (
    "view_project",
    "edit_project",
    "delete_project",
    "create_note",
    "edit_note",
    "delete_note",
    "create_decision",
    "edit_decision",
    "delete_decision",
    "edit_architecture",
    "manage_access",
    "manage_roles",
    "invite_members",
)


def permissions_strictly_dominate(
    actor: Mapping[str, object] | None,
    target: Mapping[str, object] | None,
) -> bool:
    """Return True only if actor has a strict superset of target permissions.

    This is intentionally a partial-order rather than a numeric score. A role
    manager cannot manage a role that has *any* capability the manager lacks,
    even if some weighted rank would otherwise be larger.
    """
    actor = actor or {}
    target = target or {}
    actor_keys = {key for key in TEAM_PERMISSION_KEYS if bool(actor.get(key, False))}
    target_keys = {key for key in TEAM_PERMISSION_KEYS if bool(target.get(key, False))}
    return target_keys < actor_keys
