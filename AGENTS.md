# Ergo Tools UI Rule

Visual coherence is a required part of every UI change, not optional polish.

- Do not add or modify an interface unless it follows the established Ergo Tools palette, typography, spacing, button treatment, icon style, tooltips, and interaction patterns.
- Reuse the processed assets in `assets/ui-icons`. Never mix in system-default or unrelated icon sets when a styled asset exists.
- Normalize new designer icons for transparent background, crop, canvas size, and visual padding before use.
- When a required icon is missing, explicitly tell the user which icon is needed. Temporary Qt controls must still follow the application stylesheet.
- Visually inspect every changed window and its important expanded, selected, empty, and populated states before considering the work complete.
- When adding or resizing controls, verify that adjacent fixed-format regions move or resize with them. In particular, inspect the complete VTK model, result cards, labels, and bottom controls for clipping at the target window size.
