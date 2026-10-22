# Properties, menu icons and assessment scroll acceptance

The three requested correction areas are **3/3 complete (100%)**. No milestones or
dependencies were added. Migration and cleanup ledgers remain 12/12 and 6/6.

## Behavior

Project Properties now uses the application palette, typography, processed icons,
read-only copyable fields and a resizable card layout. Native project name, filename,
location, creation metadata, project language, measurement system and full description
remain. Obsolete data/images folders and duplicate database fields are removed.
Missing optional metadata is explicitly not recorded; description text is literal,
complete and scrollable. Opening Properties does not save or discard pending edits.

Menu icons use a menu-only QProxyStyle metric: 16 to 19 logical pixels on the approved
Linux style, approximately 20% larger after integer rounding. Toolbar/button icons
retain their existing dimensions. Qt handles display scaling. Style installation is
idempotent and preserves application ownership of its underlying style.

Assessment source Undo/Redo restores both scrollbar offsets recorded at edit time,
including when the user scrolls elsewhere before replay. This covers LiFFT, DUET and
ST, numeric inputs and selector edits. Retiring grids release their focused child
before replacement so Qt cannot advance focus down all tasks. A single queued
restoration follows layout; document identity/revision guards prevent applying it to
a changed document. Scroll state belongs only to the desktop presentation layer and
is not stored in project data or application/domain history. Native typing Undo is
preserved. If a rebuilt grid is shorter, Qt clamps offsets to its available range.

See [icon editing instructions](icon_editing.md) for authoritative source artwork,
restart behavior, manifest provenance and delivery rebuilding.

## Verification

The required gate passed **1,329 tests, zero failures/skips; 95.75% combined coverage**.
This percentage measures exercised statements/branches, not the percentage of tests
passing. Ruff, formatting, strict mypy (258 sources/tools), architecture, naming,
structural documentation, semantic review inventory (414 maintained files) and build
checks passed. Twelve changed/new maintained files have current semantic reviews.
Guide/resource follow-up passed 16 tests and 78 subtests.

Focused regressions use 50-task grids for all three tools at the first and middle
row, actual focused controls and toolbar actions, scrolling away before Undo/Redo,
and exact source restoration. Properties tests cover English/Spanish, literal long
text, full paths, missing metadata, resizing, accessibility and title geometry.
Previous Properties tests were updated from the obsolete 13-row fixed-size contract;
Save As metadata, saved defaults and invalid pending-input protections remain tested.

Native English/Spanish verification inspected 24 functional captures plus four final
Properties title/layout captures. These include expanded Project/Workplace/Edit and
PLOT/JROT menus, populated/empty/long/enlarged Properties, and Default worker DUET
with 50 tasks at task 1 and task 25. The final title captures supersede earlier title
spacing. All 194 saved comprehensive assessment sources/results and permanent fixture
bytes remain unchanged. No artwork bytes or manifest hashes changed in this follow-up.

Evidence: [validation](properties_scroll_validation.json),
artifacts/properties_scroll_check.log, artifacts/properties_scroll_focused.log,
artifacts/properties_scroll_guides.log, artifacts/properties_scroll_review/validation.json
and artifacts/properties_scroll_reviewed_files.json. The first full gate exposed an
obsolete Properties test contract, updated before the final successful gate; its log
is retained as artifacts/properties_scroll_initial_check.log.

Only the new codebase was edited. Windows/macOS native visual testing remains deferred
as agreed. Restart running application instances to use these changes.
