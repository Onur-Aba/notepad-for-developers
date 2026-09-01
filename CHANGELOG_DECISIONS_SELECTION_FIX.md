# Decisions selection/editor fix

- Fixed a case where creating or selecting a decision could leave the right-side editor blank because the list selection and `current_decision_id` were already equal before the decision was actually loaded.
- Decision list refreshes now explicitly synchronize the selected list item with the loaded editor content.
- Switching between decisions saves the previous decision without rebuilding the list mid-selection.
- The right-side decision editing controls are hidden when no decision is selected; only a friendly empty state is shown.
- The first decision is no longer silently auto-selected when entering the page with no explicit selection.
