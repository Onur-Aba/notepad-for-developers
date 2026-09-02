# DevNest Design System

## Product rationale
DevNest is a local-first developer workspace for projects, repositories, notes, technical decisions, architecture, review state, activity and team collaboration. The UI is optimized for frequent desktop use, keyboard efficiency, auditability and dense but readable information.

## Interface modes

### Classic
- Preserves the established DevNest component geometry and familiar visual rhythm.
- Uses the same color ThemeSpec palette, page structure, features and data model as before this update.
- Exists as the compatibility/familiarity mode.

### Modern
- Technical, calm, compact, predictable and content-first.
- Uses stronger hierarchy, clearer selected/focus states, flatter surfaces and consistent radii/spacing.
- Avoids decorative gradients, glass effects, oversized radii, emoji navigation controls and unnecessary motion.
- Does not fork page logic: it is a visual/component skin layered on the same application behavior.

## Token architecture
DevNest keeps the existing `ThemeSpec` as its semantic color source. Modern mode derives component tokens from it rather than hard-coding a second palette.

Semantic roles:
- `window` → application background
- `surface` → navigation/cards/dialog surfaces
- `surface_alt` → elevated/helper surfaces
- `editor` → text/data input surface
- `text` → primary text
- `muted` → secondary text
- `border` → separators/control boundaries
- `hover` → pointer hover state
- `selected` → classic selected state
- `accent` → action/focus/modern selected emphasis

Derived Modern roles include accent-soft, accent-soft-hover, input-bg, elevated, focus, primary foreground and danger foreground.

## Typography
- UI/body: Segoe UI Variable Text → Segoe UI → system sans-serif fallback.
- Mono is reserved for code/path/commit-oriented content where already used.
- Page titles carry primary hierarchy; section/card labels remain compact for developer-tool density.

## Spacing and shape
Primary spacing rhythm: 4 / 8 / 12 / 16 / 20 / 24 / 32.
Modern component radii are intentionally limited to a small family around 8–14 px rather than arbitrary per-card values.

## Interaction states
Interactive components account for default, hover, focus, pressed/checked, selected and disabled states. Focus uses the current theme accent and remains visible in both light and dark palettes.

## Accessibility
- Keep native Qt controls for keyboard semantics.
- Preserve visible focus instead of removing outlines/borders.
- Primary button foreground is selected from contrast against the active accent.
- Status is not communicated by color alone where the application already has text/glyph state.
- Modern mode removes emoji from primary navigation/system controls while keeping meaningful text labels.
- Avoid unnecessary animation; the interface relies on immediate state changes.

## Internationalization
- English and Turkish are first-class application languages.
- All new interface-mode controls, help text, navigation variants, editor/find/diagram controls and legacy dialogs touched by this update have both languages.
- Layouts use flexible Qt layouts and word-wrapped help text so longer Turkish labels remain usable.

## Color theme compatibility
Classic and Modern are independent from color choice. Every existing System/Dark/Light color theme can be paired with either interface mode. Switching interface mode must never modify user data or select a different color theme.
