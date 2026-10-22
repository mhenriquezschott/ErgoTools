# Original active feature inventory — M11

This closes M11.1 against the read-only working reference, not an inferred screen
list. The source inventory parses all **41** top-level `src/*.py` modules and
**490** signal connections, plus Qt event overrides. Thirty-eight modules are
import reachable from main.py. The conservative self/callback/class/import graph
finds **660** reachable methods. Reachability is a review aid, not proof that a
button is visible or that a callback executes. The report records each connection's
line, signal, callback, containing method, reachability and disposition:
[source inventory](../artifacts/m11-audit/original-entry-points.json),
[full mapping](../artifacts/m11-audit/feature-map.json).

The table maps each source family to actual new files and accepted workflow
evidence. Connection counts are mapped / dormant / hidden. The mapping is at
feature-family granularity; each callback retains its exact source location in
the machine report. It does not imply one new class per old handler. Search's
specific route is separately verified under owner-approved CR007 below.

| Original module | Connections | Migrated implementation or disposition | Evidence |
|---|---:|---|---|
| pyTST | 0 / 0 / 0 | `domain/assessments/tst.py`; `domain/assessments/tst_summary.py` | [m01-acceptance](m01_acceptance.md), [m10-acceptance](m10_acceptance.md) |
| compareopallrotation_window | 1 / 0 / 0 | `presentation/desktop/rotation_comparison.py` | [m08-acceptance](m08_acceptance.md) |
| comparerotation_window | 0 / 0 / 0 | `presentation/desktop/rotation_comparison.py` | [m08-acceptance](m08_acceptance.md) |
| database | 2 / 0 / 0 | `infrastructure/assessment_project_file.py`; `infrastructure/assessment_store.py` | [m04-acceptance](m04_acceptance.md), [m10-acceptance](m10_acceptance.md) |
| database_inventory | 0 / 0 / 0 | Unreachable old implementation, offline utility or hidden D3 experiment; retain original archive/source, no new UI. | Classification below |
| job_placement_repository | 0 / 0 / 0 | `domain/job_catalog.py`; `infrastructure/job_catalog_store.py` | [m03-acceptance](m03_acceptance.md) |
| job_risk_repository | 0 / 0 / 0 | `domain/job_risk.py`; `infrastructure/job_risk_store.py` | [m03-acceptance](m03_acceptance.md) |
| job_window | 20 / 0 / 0 | `presentation/desktop/job_management_dialog.py`; `presentation/desktop/job_workplace_dialog.py`; `domain/job_management.py` | [m03-acceptance](m03_acceptance.md), [m10-acceptance](m10_acceptance.md) |
| jrot_database | 0 / 0 / 0 | `infrastructure/rotation_scheme_store.py` | [m07-acceptance](m07_acceptance.md) |
| line_window | 0 / 18 / 0 | Imported legacy window; no constructed route from current ErgoTools. Visible replacements live in organization/context/transfer forms. | Classification below |
| main | 114 / 7 / 0 | `presentation/desktop/lifft_window.py`; `presentation/desktop/main_navigation.py`; `presentation/desktop/assessment_menu.py`; `presentation/desktop/assessment_context_dialog.py`; `presentation/desktop/worker_search_dialog.py`; `application/project_workspace.py` | [m01-acceptance](m01_acceptance.md), [m04-acceptance](m04_acceptance.md), [m09-acceptance](m09_acceptance.md), [m10-acceptance](m10_acceptance.md) |
| multiselectcombobox | 1 / 0 / 0 | `presentation/desktop/plot_filter_controls.py` | [m05-acceptance](m05_acceptance.md) |
| optimizedrotation_window | 0 / 0 / 0 | `presentation/desktop/rotation_comparison.py` | [m08-acceptance](m08_acceptance.md) |
| organization_window | 14 / 0 / 0 | `presentation/desktop/organization_dialog.py`; `application/organization_management.py` | [m02-acceptance](m02_acceptance.md), [m10-acceptance](m10_acceptance.md) |
| plant_layout | 71 / 3 / 1 | `presentation/desktop/plot_window.py`; `presentation/desktop/plot_filters_panel.py`; `presentation/desktop/plot_graph_dialog.py`; `presentation/desktop/plot_graph_settings.py`; `presentation/desktop/plot_worker_controls.py`; `application/plot_history.py` | [m05-acceptance](m05_acceptance.md), [m06-acceptance](m06_acceptance.md), [m10-acceptance](m10_acceptance.md) |
| plant_window | 0 / 22 / 0 | Imported legacy window; no constructed route from current ErgoTools. Visible replacements live in organization/context/transfer forms. | Classification below |
| plotviewerdialog | 1 / 1 / 0 | `presentation/desktop/plot_figure_viewer.py`; `presentation/desktop/plot_figure_export.py` | [m06-acceptance](m06_acceptance.md) |
| plot_position_repository | 0 / 0 / 0 | `domain/plot_positions.py`; `infrastructure/plot_position_store.py` | [m06-acceptance](m06_acceptance.md) |
| pyDUET | 0 / 0 / 0 | `domain/assessments/duet.py`; `domain/assessments/duet_summary.py` | [m01-acceptance](m01_acceptance.md), [m10-acceptance](m10_acceptance.md) |
| pyLiFFT | 0 / 0 / 0 | `domain/assessments/lifft.py`; `domain/assessments/lifft_summary.py` | [m01-acceptance](m01_acceptance.md), [m10-acceptance](m10_acceptance.md) |
| risk_colors | 0 / 0 / 0 | `presentation/desktop/theme/lifft_colors.py` | [m01-acceptance](m01_acceptance.md) |
| risk_ranges | 0 / 0 / 0 | `domain/risk.py`; `presentation/desktop/theme/risk.py` | [m01-acceptance](m01_acceptance.md), [m09-acceptance](m09_acceptance.md) |
| rotation_layout | 41 / 22 / 0 | `presentation/desktop/rotation_dialog.py`; `presentation/desktop/rotation_solve.py`; `presentation/desktop/rotation_history.py` | [m07-acceptance](m07_acceptance.md), [m08-acceptance](m08_acceptance.md), [m10-acceptance](m10_acceptance.md) |
| rotation_optimizer | 0 / 0 / 0 | `infrastructure/pulp_rotation_optimizer.py` | [m08-acceptance](m08_acceptance.md) |
| rotation_repository | 0 / 0 / 0 | `infrastructure/rotation_scheme_store.py` | [m07-acceptance](m07_acceptance.md), [m08-acceptance](m08_acceptance.md) |
| rotation_schema | 0 / 0 / 0 | `domain/rotation_scheme.py`; `infrastructure/rotation_scheme_store.py` | [m07-acceptance](m07_acceptance.md) |
| rotation_scope_dialog | 4 / 0 / 0 | `presentation/desktop/rotation_scope_dialog.py` | [m07-acceptance](m07_acceptance.md) |
| schema_migrations | 0 / 0 / 0 | `infrastructure/legacy_conversion.py`; `infrastructure/legacy_reconciliation.py` | [m04-acceptance](m04_acceptance.md), [m10-acceptance](m10_acceptance.md) |
| section_window | 0 / 18 / 0 | Imported legacy window; no constructed route from current ErgoTools. Visible replacements live in organization/context/transfer forms. | Classification below |
| shift_window | 0 / 20 / 0 | Imported legacy window; no constructed route from current ErgoTools. Visible replacements live in organization/context/transfer forms. | Classification below |
| station_window | 0 / 18 / 0 | Imported legacy window; no constructed route from current ErgoTools. Visible replacements live in organization/context/transfer forms. | Classification below |
| testmultiop | 0 / 0 / 0 | Unreachable old implementation, offline utility or hidden D3 experiment; retain original archive/source, no new UI. | Classification below |
| tooldatadialog | 3 / 0 / 0 | `presentation/desktop/tool_data_dialog.py` | [m01-acceptance](m01_acceptance.md) |
| tooltransferdialog | 0 / 14 / 0 | Imported legacy window; no constructed route from current ErgoTools. Visible replacements live in organization/context/transfer forms. | Classification below |
| visualjobmarker | 0 / 0 / 0 | `presentation/desktop/plot_marker_item.py`; `presentation/desktop/plot_marker_layer.py` | [m05-acceptance](m05_acceptance.md), [m06-acceptance](m06_acceptance.md) |
| visualworkertool | 3 / 0 / 0 | `presentation/desktop/plot_marker_item.py`; `presentation/desktop/plot_marker_layer.py` | [m05-acceptance](m05_acceptance.md), [m06-acceptance](m06_acceptance.md) |
| vtk_camera_director | 1 / 0 / 0 | `presentation/desktop/rendering/vtk_body_renderer.py` | [m09-acceptance](m09_acceptance.md) |
| workertransferdialog | 0 / 21 / 0 | Unreachable old implementation, offline utility or hidden D3 experiment; retain original archive/source, no new UI. | Classification below |
| worker_transfer_window | 13 / 0 / 0 | `presentation/desktop/worker_transfer_dialog.py`; `domain/assessment_transfer.py`; `infrastructure/assessment_project_file.py` | [m04-acceptance](m04_acceptance.md), [m10-acceptance](m10_acceptance.md) |
| worker_window | 29 / 1 / 6 | `presentation/desktop/worker_management_dialog.py`; `domain/worker_details.py` | [m02-acceptance](m02_acceptance.md), [m10-acceptance](m10_acceptance.md) |
| zcpwindow | 0 / 0 / 0 | Unreachable old implementation, offline utility or hidden D3 experiment; retain original archive/source, no new UI. | Classification below |

## Visible paths and exceptions

Main project New/Open/Save/Save As/Backup/Close/Properties/recent paths, worker
ordering/letters/navigation, worker management, organization, Jobs, assessment
context/versions/data/count/reset/delete, LiFFT/DUET/ST calculations, PLOT,
JROT, worker Transfer, CSV export, preferences, Help and Authors have mappings
above and accepted M01–M10 evidence. Shared menus/settings follow the explicitly
approved modernization exceptions; calculations and visible form controls retain
the original conventions.

**CR007 / R015: Search.** Original main.py:5177 opens WorkerSearchDialog
(425–741), while the migrated Search incorrectly reused the context chooser.
The owner explicitly approved the bounded restoration. The original constructor
and buildUi control/layout code is ported to worker_search_dialog.py. Main
Search now filters saved current assessments across workers by casefolded ID/name,
surname initial and exact workplace ancestry. Select assessment context remains
separate. Sorted rows carry AssignmentSelection, not reconstructed display text;
closed assignment owners remain selectable. Same-workplace historical owners are
separate rows, following the accepted immutable ownership architecture. Older
versions remain available through version/data management. Cancel preserves
pending text; accepted selection uses the existing Save/Discard/Cancel policy.
See tests/test_assessment_search.py and artifacts/m11-search/comparison.json.

**Original nonoperative placeholders.** mainCut/mainPaste only display information;
Export/Export As are disabled/informational placeholders. They do not establish
an original working operation to port. Accepted actual CSV/image export and scoped
Undo/Redo remain implemented. These are classified source placeholders, not newly
excluded functional requirements.

## Hidden and dormant source classification

- Worker head/neck, upper-body and lower-body anthropometry controls are built but
  tabs after Optional details are hidden (worker_window.py:343–352). The example
  head/neck calculation is not an exposed validated assessment. Preserve original
  evidence/raw archived data; do not enable these experimental tabs.
- PLOT D3/extra-tool-8 constructs zcpWindow only behind its hidden button. It is
  archived, not a new visible tool. Active plant-image loading reads image_name
  and fits original image pixels; stored rotation/crop/mirror metadata is dormant
  on that path. R003/F142 documents why applying it would change original behavior.
- Individual plant/section/line/station/shift windows are import reachable but
  have no construction path from the working main UI. Visible organization and
  assessment-context forms provide the active management routes.
- tooltransferdialog is imported, but its callers are unconnected old transfer
  actions; active tool-data buttons open ToolDataDialog. workertransferdialog is
  an older unreachable transfer implementation; worker_transfer_window is active.
- main controlPanelconnectSignals, worker loadWorkerDetailsOld, PLOT legacy worker
  queries and rotation initUI are dormant alternatives. The working rotation
  constructor invokes initResponsiveUI. No duplicate legacy implementation is
  introduced into the new application.
- database_inventory/testmultiop and src/updateCode utilities are offline tools,
  not product routes. Original tests and cached bytecode are not product features.
- GLPK removal is the owner's explicit solver decision: CBC for one tool and
  HiGHS for multi-tool optimization. Original private solver alternatives do not
  create an obligation to restore GLPK.

No active functional omission is silently reclassified as an exclusion. Original
scientific inconsistencies remain preserved/documented in review_register.md.
Windows/macOS native acceptance and delivery are M12; they are not claimed here.
The original English Search's short surname caption and horizontal table scrolling
at minimum width are retained; Spanish labels fit without changing the English
layout. Full text/tooltips and larger-window layout remain available.
