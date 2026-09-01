# DevNest 2.3 — UX, Project Trash & Navigation Fixes

- Settings page redesigned as a centered, scrollable, comfortable-width panel with larger controls.
- Project creation replaced with a theme-native two-step dialog so dark/light themes apply consistently on Windows.
- Global left navigation is now resizable with a draggable splitter; its width is remembered in QSettings.
- Added a permanent Trash button at the bottom of global navigation.
- Projects now have a red Delete action next to Archive.
- Project deletion uses two explicit confirmations: first “Yes, I understand”, then exact project-name typing.
- Deleting a project moves the project and all DevNest-owned workspace content into Trash as one reversible bundle.
- Project Trash cards expand/collapse to show notes, decisions, diagrams, repository mappings, code links and review baselines.
- Restoring a project preserves notes that had already been individually deleted before the project was trashed.
- Permanent project deletion is only available from Trash and does not delete the underlying GitHub repository or local folder.
- GitHub Repositories page can now remove a repository from the currently selected project.
- Project history commit rows now use a compact disclosure arrow; file changes are hidden until expanded and can be collapsed again.
- Database schema advanced to v7 with a safe sequential migration and project-trash state columns.
- Added database tests for grouped project Trash, restore semantics and permanent project deletion.

Validation: 35 passed, 9 skipped.
