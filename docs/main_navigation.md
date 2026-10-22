> Historical component/checkpoint record. For current operation use [the user guide](user_guide.md), [development](development.md) and [STATUS](STATUS.md). Early pending-feature statements below are historical; M11 inventory records any actual remaining gap.

# Shared integrated navigation — F75

Run from this new project only:

```bash
.venv/bin/python -m ergotools.bootstrap --integrated-preview
```

This opt-in development preview places the F74 LiFFT task panel in the original
shared main container. It is not a separate final LiFFT application or a claim of
complete main-window parity. Existing preview commands remain available.

## Source and layout

Reviewed active reference methods: `setupNavigationButtons`, `setupTopWidgets`,
`setupTabsTopControls`, `setupWorkspaceFooter`, and `updateContextSummary`.
Unreachable layouts after explicit returns and originally hidden optional hierarchy
combos were not resurrected. Palette, processed packaged icons, typography, header,
worker bar, assessment tabs, association bar, footer and 1550×1015 reference size
are retained. Screenshots verify the code port; they did not determine positions.

Qt cached inherited toolbar layout metrics differently from the original host.
The port explicitly synchronizes spacing 3 and effective margins 7 on all sides
with the original themed toolbar. Native original/new toolbar geometry is
(710, 11, 802, 90) relative to its header. The reference CSS declares padding
5px 7px; Qt's effective toolbar layout margins are 7 on all sides. The regression
checks these effective values. Spanish All/"Todos" uses 34 pixels instead of the
English 18-pixel letter width to fit its translated text. Adjacent controls fit.

## Connected workflow

New/Open/Save operate on synthetic/new-format project files (`*.ergprj`, `*.sqlite`).
Workers, Jobs, Search/Select assessment context, Manage organization and Refresh
reuse the existing application operations and owned modal dialogs. Worker surname
filtering, ordering and first/previous/next/last use stored IDs and stored surnames,
including names with commas. Rendering blocks selection signals.

Before a worker switch, entered task cells are parsed as one atomic edit. Existing
Save/Discard/Cancel decisions apply to dirty assessments. Cancel retains the old
assessment and worker label; Save persists before switching. A worker with no
saved LiFFT assessment leaves the previous assessment selected and reports that
condition. Multiple eligible contexts use the existing context dialog. Navigation
never invents an assessment or reassociates historical records. Labels describe
the assessment's own assignment, including retained historical assignments.

Management completion refreshes shared labels without rebuilding the task grid or
losing its edit context. Explicit new projects/blank assessments initialize 15 empty
rows, the original default; opening an existing draft does not add or save rows.
Calculation currently requires every existing row to be valid. The reference's
blank/partial-row handling and configurable task count remain upcoming work.

## Boundaries still pending

PLOT/JROT, Export, Settings, Help, Transfer and DUET/ST views are visibly disabled
until their workflows are migrated. The tool names are retained in the tab strip;
those captions still need localized rendering. Backend localization and recorded
metric/imperial quantity handling remain available, but the final settings UI is
not yet connected here. Metric scientific-review gates remain unchanged.

The original model and result sidebar are absent, so the task panel temporarily
uses the available central width. Final menu/settings exceptions remain governed
by `final_targets.md`. Original task-data grid dialog and saved-assessment deletion
are incomplete. No VTK runtime dependency has been installed. Full model/result
clipping checks and Windows/macOS verification remain required when those areas
are integrated. Legacy comprehensive projects are not imported by this preview.

During composition, old harness widgets remain hidden and owned to reuse existing
lifecycle handlers. There is one application source of truth. This transitional
ownership is not the final widget structure and should be removed when the shared
window fully replaces the harness.

## Verification

Seven focused navigation regressions cover actual navigation buttons and dirty
Cancel/Save, ID/surname filtering and missing assessment, owned Worker Management
completion without task-grid reconstruction, Spanish/state capabilities, empty
startup, direct owned assessment-context selection and toolbar New with 15 rows.
All 621 tests and required quality gates pass. Native original/new shared controls
and important full preview states were inspected at 1550×1015, including Spanish
bottom scrolling. The independently extracted wheel passes New/edit/Calculate/
Save/reopen without importing the editable source package.

Evidence: `f75_validation.json`; captures are in `artifacts/main-navigation/`.
Characterization and isolated-wheel scripts are archived under `docs/reference/`.
Reference files, dependency lock and project schema remain unchanged.


## F76 subsequent integration

The original-style grid now supports an explicitly marked incomplete-row preview
and the original task-count dialog. This supersedes earlier pending/full-row-only
statements about grid interaction above. Strict preparation and non-grid evaluation
remain unchanged. See [current workflow and limits](lifft_grid_workflow.md).


## F77 subsequent integration

The original result sidebar and body-panel layout are now integrated. Earlier
statements about missing side-panel structure are historical. The VTK avatar and
its view interactions remain pending. See [current panel limits](main_panels.md).
