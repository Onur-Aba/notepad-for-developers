# Active Project / Notes / Activity UX Fix

## Fixed

- Dashboard > Continue working is now scoped to the currently active project.
- Deleting the last note no longer silently creates another `Untitled Note`.
- Projects with zero notes now show a real empty editor state; a new note is created only with the `+` action.
- Deleted notes (and deleted decisions) are removed from recent-work history.
- Note cards reserve enough vertical space for title, preview, and date; the date is no longer clipped.
- Note preview/detail contrast was increased consistently across themes.
- Repository UI no longer describes the whole repository as `Unavailable` when only GitHub access could not be verified.
- Repository diagnostics distinguish GitHub access from a usable local repository.
- Activity Timeline repository-access messages are localized and user-facing instead of showing raw states such as `unavailable`.
- Activity Timeline cards are clickable. Review details include the knowledge item, repository, commit SHA, branch, timestamp, and available metadata.

## Verification

- `python -m compileall -q app tests`
- `pytest -q` -> 38 passed, 9 skipped (Qt/PySide6-dependent tests skipped in the packaging environment)
