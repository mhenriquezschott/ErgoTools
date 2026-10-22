# Original JROT scheme form — F124, 2026-10-09

F125 adds selected-tool optimization/transfer and owned cancellation; see
[jrot_selected_optimization.md](jrot_selected_optimization.md). The F124 evidence
and pending-action descriptions below record that earlier checkpoint.

Source: rotation_layout.py initResponsiveUI (171–520), scope commands (846–929),
scheme navigation (1165–1232), save/load (1290–1465), and New/Cancel/Delete/Search
(1671–1890). Only active source controls were migrated; obsolete fixed-layout and
old alternate handlers are not imported. F122 supplies the scope chooser; F123
supplies the editable worker/time-block grid. Layout comes from source code.

RotationForm builds the original title/support line, setup/risk segments,
All Jobs/Workplace pending-scope controls, five-level icon/arrow path, scheme ID/
workers/blocks/limit fields, navigation and commands, horizontal two-panel
splitter, Use as Current, bottom action rail and disclaimer. Size is 1480x900;
minimum remains 1480x740. Margins, spacing, button/icon dimensions and source
stylesheet are retained. Existing packaged applyrotation/comparerotation/
optimizeselectedtool/optimizealltools assets were added to the icon registry;
no asset or dependency was installed or changed. The original raster arrow is
scaled directly from its full icon size. No VTK/avatar exists in the reference
JROT form; both table panels and the bottom controls were inspected.

RotationDialog controls the view through the borrowed RotationRepository port,
combining saved catalog reads and explicit scheme commands. It does not import
SQL or solvers, open a connection, own a project handle, alter assessment edits,
or use application-global parent lookups. Main navigation composition remains
pending until optimization/comparison makes the complete JROT workflow usable.
The form can be exercised directly by tests/validation, not a replacement app.

Save validates the actual cells and stable ID, preserves selected scheme name/
description, writes once and publishes the saved selection only after commit.
The accidental recursive save wrapper in the source is not reproduced. Grid
loading retains exact retired profile/closed assignment evidence. Merely changing
the displayed risk tool never changes links, units or saved optimization
provenance. Manual cell changes intentionally reset saved provenance to MANUAL,
instead of claiming the edited schedule is still an optimizer result. This is
an explicit provenance correction; formulas and evidence remain unchanged.

New retains the previously selected scheme as Cancel's target. Cancel restores
that scheme's complete scope/counts/cells, or clears an unsaved grid when no saved
scheme exists (the source left it unchanged in that case). Previous/next/first/
last and exact-ID search select saved schemes. Typed ID changes cannot leave
Delete/navigation acting on another loaded identity. Navigation keeps repository
SQLite NOCASE ordering, including its ASCII-only folding. Delete defaults to No,
requires confirmation, writes once, then selects the first remaining scheme or
shows the original empty table after deleting the last record. Reads needed for
the following view occur before deletion. Failed reads/writes retain the visible
grid and saved selection and report a localized error, with diagnostics logged.

Scope selection returns exact pending stations only on modal acceptance. Apply
rebuilds a manual draft with the requested worker/block counts, then replaces the
applied scope. All Jobs changes the pending scope; Clear immediately applies the
organization-wide empty draft. Worker count clamping follows source pool limits.
Like the source, count selections take effect when applying scope or starting New.
Scope cancellation leaves the applied grid intact. There is no speculative
multi-user/project-switch callback layer in this modal single-user workflow.

English/Spanish form text, tooltips, search and message actions are localized.
The short Spanish Turn. heading has a full Turno tooltip; Optimizar actual fits
its original fixed action width. Spanish heading minimums include text metrics.
The existing styled popup delegate avoids white-on-white native selected options.
Messages reuse packaged JROT/action icons and locally translated buttons rather
than system command glyphs or global Qt translators. Scheme QPushButtons do not
auto-activate on Enter. These are targeted localization/interaction corrections.
Original scrolling remains for wide tables, so a partly visible final column at
minimum size is accessible through its scrollbar; enlarged tables show it fully.

Validation: 972 native tests pass (seven new focused cases), 96.75% combined
coverage. Ruff/format (461 files), strict mypy (211 source files), architecture,
wheel and sdist pass. Tests use real form clicks and saved project reopen, New/
Cancel/navigation, delete consent, exact search, pending/applied scopes, frozen
links, missing measurements, failure retention and optimized/manual provenance.
Native localized confirmation/acknowledgment buttons are also clicked, with
No verified as the deletion default. Synthetic projects only; no operational
reference database is opened for writes.

Twenty-four final native captures were inspected: two original source full-form
comparisons plus 22 new EN/ES minimum/enlarged empty, saved, draft, pending/applied
scope, scope chooser, scheme dropdown, search, deletion confirmation and incomplete
prompt states. English setup/scheme groups, grid, optimized panel, transfer and
bottom action rectangles match the source at 1480x740 and 1720x1000. Both panels,
labels and bottom controls remain visible; original wide-grid horizontal scrolling
is retained. Full pixel identity is not claimed because focus, disabled pending
commands, localized text and the mandated packaged message assets differ.
Independent extracted-wheel EN/ES actual Save/New/Cancel/reopen/confirmed Delete
and exact zero-risk profile/Imperial evidence pass. All 500 reference hashes and
approved dependency lock are unchanged. Evidence: f124_validation.json,
artifacts/f124-check.log, artifacts/f124-wheel.log and artifacts/jrot-form.

Next: connect actual CBC single-tool/HiGHS multi-tool optimization to this form,
results/comparison transfer, owned solver-thread cancellation/closure, then main
navigation. Optimization, comparison and transfer buttons remain visibly disabled
with a pending tooltip. GLPK remains excluded. Legacy compatibility, comprehensive
copied-project integration and final application UI/workflow/platform acceptance
remain in the plan. No reliable whole-app percentage/date is established.
