# Recents, Notes Empty State & First-Launch Onboarding Fix

## Dashboard / Continue Working
- Recent items now resolve through an active project before being shown.
- Projects moved to Trash or permanently deleted no longer appear through stale recent-history rows.
- Project-scoped recent history remains isolated to the currently active project.

## Notes
- The right side of the Notes page now uses explicit editor/empty states.
- When no note is selected, the editor is hidden instead of being shown disabled.
- The empty state explains what to do and includes a `Yeni not oluştur / Create new note` button.
- If search/filtering removes the selected note from the visible list, pending edits are saved and the empty state is shown.
- Clearing the note selection also switches to the empty state.

## Onboarding
- The onboarding tour is persisted as shown on first launch and will not reappear on later launches, including after Skip/Close.
- The setting is synced immediately for reliable first-launch-only behavior.
- Every tutorial step now includes a destination button that opens the page being explained.
- The tour is modeless so navigation can happen immediately while the tutorial remains available.

## Validation
- Added regression coverage for stale recent items belonging to trashed/permanently deleted projects.
- Test suite: 39 passed, 9 skipped in the packaging environment.
- Python compileall check completed successfully.
