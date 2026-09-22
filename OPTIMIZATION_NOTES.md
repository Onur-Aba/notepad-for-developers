# DevNest performance optimization notes

This build focuses on the note editor, startup responsiveness, and resume behavior.

## Changes

- Autosave is now a true idle debounce with a 1.8 second default and a 1.0 second minimum.
- Repeated autosaves for the same note are coalesced into one `note_updated` activity event per 15-minute editing session instead of appending one database row per save.
- Autosave updates only the current sidebar card instead of rebuilding every note card.
- Full-document word counting is debounced by 250 ms instead of scanning the entire note on every keystroke.
- Supabase/cloud polling network calls run through the background task runner instead of Qt's UI thread.
- Periodic repository/cloud checks are paused while the app is inactive.
- Returning to the foreground waits briefly for the window to repaint, then runs only the lightweight local HEAD check; a full review refresh happens only when a local Git change is detected.
- Startup network/repository work is delayed until after the first UI paints.
- GitHub page startup avoids duplicate cached rendering / credential-state refreshes.

## Validation in the optimization environment

- `python -m compileall -q app main.py`: passed.
- `pytest -q`: 55 passed, 9 skipped.
- The skipped tests require PySide6, which was not installed in the optimization container. `build.ps1` installs all Windows build requirements before running the full test suite.

## Important

Generated `build/`, `dist/`, and Python cache folders are intentionally omitted from the optimized ZIP. Rebuild the Windows executable from the optimized source so an older executable cannot be mistaken for the optimized version.
