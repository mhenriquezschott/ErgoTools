# M09 accepted — shared UI, localization, units and avatar

M09 earns its fixed **1.75 points**: **94.50/100 overall; 9/12 complete;
20.50/26 remaining-baseline points earned; 5.50 points left**. Scope and weights
are unchanged. M10 is next, not started or authorized by this approval.

M09.1 closes shared original-style navigation, header/footer and the approved
menu/settings exceptions. Owner-approved CR005 restores the live original
`Current Project: <name>  •  Loaded` header and `Current Project: <name>` footer,
with Spanish equivalents. Empty, unsaved and closed projects show the original
no-project caption without Loaded; first Save updates it. Caption refresh does
not commit or discard pending assessment text, translate literal project names,
or alter persisted metadata. Original icons, palette, typography and layout remain.
The existing toolbar uses Qt's normal space management for long titles; Help
remains accessible through the accepted Help menu.

M09.2 closes the shared EN/ES and metric/imperial matrix using current checks plus
valid M01–M08 component evidence. Authors credit prose is now Spanish when selected;
English text, names, attribution/link, original logo/size and close behavior remain.
Transfer supporting prose already renders Spanish from the existing catalog.
R011 is resolved by full-size individual PNG and actual font ink measurements;
no sidebar or Transfer layout adjustment was necessary. Unit toggles preserve
canonical sources and saved CSV data/provenance, including row-specific recorded
unit labels. Body-unit normalization/opposite-unit Save/reopen and PLOT unit/export
comparisons reuse accepted M02/M04/M06 evidence. Machine CSV headings and branded
proper names intentionally remain stable, while user-entered values stay literal.

M09.3 closes native VTK region focus, Rotate/Zoom/Reset, settled gauges, pending
unavailable display and minimum/enlarged main-window checks. Twelve tool/language/
display-unit cases preserve saved source and export values; all camera controls
restore the exact base view. Original keyboard behavior uses the M01 comparison
and current full regression gate. No renderer/solver/core redesign was added.

Final approved-baseline gate: **1,184 tests, 96.40% coverage**, Ruff, format,
strict mypy, architecture and wheel/sdist pass. Pre-caption independent wheel:
113 focused shared tests plus 60 subtests. Final rebuilt wheel: 30 caption/lifecycle
regressions and 14 native EN/ES main-window captures, with imports confined to the
extracted package. The 34 earlier shared captures remain valid for unchanged
components; all **48 milestone captures** were inspected. Full caption ink fits
1550×1015 and 1800×1200, including the comprehensive project's title. Native
viewport, cards, task headers, context/footer and bottom controls remain contained.

All 500 reference manifest files and the approved dependency lock are unchanged.
Linux XCB is the validated native platform; Windows/macOS remain M12. M10 still
owns one final comprehensive cross-feature scenario; M11 owns final inventory and
the updated packaged user guide. This milestone does not claim those completed.
See [bounded review](m09_review.md), [validation](m09_validation.json),
[fixed ledger](finish_progress.json) and the archived CR005 patch/native scripts.
