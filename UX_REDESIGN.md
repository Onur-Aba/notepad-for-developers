# DevNest UX Redesign

This package is based on the previously supplied `DevNest-github-persistence-exe-fix` source. It does not replace or recreate the SQLite database schema.

## What changed

- Added persistent English / Turkish interface language selection.
  - Quick language selector in the top bar.
  - Language selector in Settings.
  - Changes apply immediately without restarting DevNest.
  - User notes/decision content is never translated or modified.
- Rebuilt global navigation around plain concepts: Home, Projects, Notes, Decisions, Architecture, Needs Review, GitHub Repositories, Settings.
- Added beginner-oriented hover explanations to primary navigation and actions.
- Rebuilt Decisions UX:
  - Current project is always visible.
  - Connected repository names are always visible for the selected decision.
  - Decision list includes repository context.
  - Filter decisions by repository or show unlinked decisions.
  - Guided action order: Connect code -> See changes -> Mark checked.
  - Added plain-language usage guide.
- GitHub repositories are ordered by `last_pushed_at` descending, with unknown dates last.
- GitHub repository cards show which DevNest projects already use each repository.
- GitHub “Add to current project” disables itself when the repository is already linked to the current project.
- Added clearer project creation language and repository explanations.
- Improved Projects, Project Detail, Architecture, Review Inbox, Search, Settings and Review Details copy.
- Added a product-level Qt stylesheet for clear hierarchy, cards, panels, selected navigation, helper banners and more readable tooltips.

## Safety / compatibility

- No database schema version change is required for this UX update.
- Existing notes, decisions, diagrams, project mappings, GitHub credentials and review baselines are preserved.
- GitHub remains read-only.
- Existing note editor / diagram behavior remains in place.

## Verification

- `python -m compileall -q app main.py`: passed.
- `pytest -q`: 28 passed, 9 skipped in the build environment.
- Qt runtime tests are skipped in this environment because PySide6 is not installed here; run the app on the Windows development environment before distributing the EXE.
