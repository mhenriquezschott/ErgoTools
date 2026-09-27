# Ergo Tools UI Rule

Visual coherence is a required part of every UI change, not optional polish.

- Do not add or modify an interface unless it follows the established Ergo Tools palette, typography, spacing, button treatment, icon style, tooltips, and interaction patterns.
- Reuse the processed assets in `assets/ui-icons`. Never mix in system-default or unrelated icon sets when a styled asset exists.
- Normalize new designer icons for transparent background, crop, canvas size, and visual padding before use.
- When a required icon is missing, explicitly tell the user which icon is needed. Temporary Qt controls must still follow the application stylesheet.
- Visually inspect every changed window and its important expanded, selected, empty, and populated states before considering the work complete.
- When adding or resizing controls, verify that adjacent fixed-format regions move or resize with them. In particular, inspect the complete VTK model, result cards, labels, and bottom controls for clipping at the target window size.

# Dependency Change Approval Rule

The Python version and every application-library version are part of the tested
ErgoTools compatibility baseline.

- Never install, upgrade, downgrade, replace, or change the allowed version range of
  Python or any dependency without the user's explicit approval.
- Never create or adopt a test environment with different versions as evidence that a
  change is compatible with the project baseline.
- Run application and regression tests with the documented baseline versions. The
  environment manager may be Conda or `venv`; the Python and library versions must
  match.
- If a proposed implementation requires a feature from another library version, stop,
  explain the required version change and its risks, and obtain explicit approval
  before modifying code, environment files, lock files, or installed packages.
