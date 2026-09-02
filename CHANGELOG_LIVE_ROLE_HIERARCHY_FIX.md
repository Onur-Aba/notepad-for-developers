# Live Team Role / Hierarchy Fix

- Team membership and role/permission changes are refreshed silently while the Teams UI is open; users no longer need to switch pages to see a change take effect.
- Invitation acceptance is refreshed immediately and the owner/member list picks up newly accepted members automatically.
- Accepted invitations now always receive the built-in `Member` role instead of whichever custom role happens to have the lowest derived score.
- Role hierarchy is now enforced as a strict permission-superset relationship on the server, not only by a weighted numeric rank.
- A user with `manage_roles` can manage only members/roles whose effective permissions are a strict subset of their own.
- Users cannot edit their own base role even if a personal `manage_roles` override raises their effective permissions.
- Non-owners cannot edit built-in system roles (`Admin` / `Member`).
- Non-owners cannot assign the built-in `Admin` role.
- Member-specific permission overrides are revalidated after every change so a manager cannot promote a target to equal or higher effective permissions.
- The Teams UI disables role/member actions that the current user cannot perform, while Supabase RPC checks remain the authoritative security boundary.
- Team detail snapshots now include the signed-in viewer's effective permissions and each member's effective permissions so client controls update without stale page state.
