# M5 uncovered-path review

All 1,282 collected tests pass. Combined statement/branch coverage is **96.25%**:
470 statements and 452 branch destinations remain unexecuted in the main pytest
coverage report. Each of the 86 files with residual paths was reviewed against its
actual source/owner/conditions; the exact statements and branch endpoints are in
[the detailed review](../artifacts/cleanup-m5-uncovered-paths.json).

These are remaining test limitations, not a claim that every possible failure or
UI state has been tested. No 100% path-coverage claim is made. Production branches
include wrong types/owners, absent capabilities, corrupt storage and failed
round-trip checks, plus UI cancellation/presence/navigation/painter alternatives.
CLI subprocesses and native Qt threads execute outside this pytest instrumentation.
M5 additionally exercised the real solver threads and installed startup/relocation/
snapshots; these results do not artificially increase the coverage number.

Original LiFFT/DUET/ST numerical calculation paths are characterized; the residual
LiFFT raw-damage nonfinite guard rejects overflow. All 388 saved calculations in
the two relocated projects equal fresh evaluation exactly, including explicit
partial outcomes. Real CBC/HiGHS worker threads completed with valid schedules and
correct backend/stage evidence. No new defect repair or calculator change was found
necessary for M5. Remaining untested corrupt/OS/UI alternatives are recorded below
rather than silently converted into extra milestones. Native Windows/macOS remain
deferred. The fixed acceptance threshold remains 90% combined coverage.

| File | Missing statements | Missing branch destinations | Review disposition |
|---|---:|---:|---|
| `src/ergotools/application/assessment_export.py` | 0 | 1 | Saved unit-label fallback; normal saved-summary export and exact per-source units covered by tests and relocated result equality. |
| `src/ergotools/application/assessments/duet_commands.py` | 2 | 2 | Stale expected-source and changed row-identity guards; normal immutable grid edits and history covered. |
| `src/ergotools/application/assessments/evaluation.py` | 2 | 2 | Wrong-tool session guards for DUET/ST grid entry points; normal and partial calculations exercised across 388 relocated versions. |
| `src/ergotools/application/assessments/lifft_commands.py` | 2 | 2 | Stale expected-source/source-unit/row-identity guards; normal LiFFT edits and history covered. |
| `src/ergotools/application/organization_management.py` | 2 | 4 | Missing selected record and shift-delete branch; normal organization persistence covered; no inferred absent record. |
| `src/ergotools/application/plot_history.py` | 5 | 5 | Invalid bound counts, wrong-project/revision edits and initialization-after-edit guards; accepted filter/geometry undo exercised by focused suite. |
| `src/ergotools/application/plot_results.py` | 1 | 1 | Foreign hierarchy/project guard; all real native ownership/catalog projections validated. |
| `src/ergotools/application/project_workspace.py` | 30 | 26 | Absent-capability/project, stale forms and dishonest adapter round-trip guards. Required Save As/Backup path additionally exercised with exact SQL equality for both comprehensive copies. |
| `src/ergotools/application/saved_results.py` | 1 | 1 | Source/result mismatch rejection; 388 source-bound saved results exactly equal fresh calculation and snapshots. |
| `src/ergotools/bootstrap.py` | 11 | 11 | Diagnostic preview/old-capability paths, asset decode rejection and CLI misuse; real installed positional relative/spaced startup additionally exercised. |
| `src/ergotools/domain/assessment_transfer.py` | 10 | 11 | Typed identity, missing owner/current version, conflicting destination and generated-ID rejection guards; valid copy/move and rollback suite covers intended ownership. |
| `src/ergotools/domain/assessments/lifft.py` | 1 | 1 | Nonfinite raw damage overflow guard; normal arithmetic/rounding characterized. Guard rejects extreme overflow rather than saving fabricated risk. |
| `src/ergotools/domain/assessments/tst_draft.py` | 1 | 1 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `src/ergotools/domain/organization_record.py` | 3 | 3 | Wrong kind, incomplete ancestry and nontext metadata rejection. |
| `src/ergotools/domain/rotation_scheme.py` | 6 | 8 | Wrong typed IDs/collections, foreign/missing scopes and optional unscoped links; actual 12 saved schemes and all references survive whole-project snapshots. |
| `src/ergotools/domain/work_catalog.py` | 1 | 1 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `src/ergotools/domain/work_hierarchy.py` | 2 | 2 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `src/ergotools/domain/worker_details.py` | 4 | 4 | Wrong date/text/unit types; valid canonical cm/kg and metric/imperial conversions characterized. |
| `src/ergotools/infrastructure/assessment_history_store.py` | 7 | 7 | Missing caller transaction, wrong project and mismatched round-trip guards; valid transaction/ownership history survives exact snapshots. |
| `src/ergotools/infrastructure/assessment_project_file.py` | 22 | 23 | Corrupt/mismatched integrity, closed repository, typed project/owner/scheme guards and old-format alternatives. Both real full projects and four new snapshots passed integrity and complete SQL equivalence. |
| `src/ergotools/infrastructure/draft_store.py` | 1 | 1 | Caller-owned transaction guard; ordinary source persistence and rollback covered. |
| `src/ergotools/infrastructure/job_catalog_store.py` | 3 | 3 | Missing transaction/wrong-project guards; exact native job/placement/worker catalogs included in snapshot checks. |
| `src/ergotools/infrastructure/job_risk_store.py` | 7 | 7 | Transaction/project/stale-form and round-trip guards; authored risk catalogs retained exactly, including frozen references. |
| `src/ergotools/infrastructure/project_migration.py` | 0 | 3 | Earlier result-envelope/header alternatives; current native startup requires no converter and cannot import it. |
| `src/ergotools/infrastructure/project_snapshot.py` | 2 | 2 | Foreign risk catalog and duplicate/missing image ownership guards; both native files retain all four embedded images and catalogs. |
| `src/ergotools/infrastructure/rotation_scheme_store.py` | 4 | 4 | Wrong project/record identity and malformed serialized target/current rows; actual native schemes validated/reopened. |
| `src/ergotools/infrastructure/saved_result_store.py` | 1 | 1 | Missing caller-owned transaction rejection; real sole results preserved exactly. |
| `src/ergotools/infrastructure/work_hierarchy_store.py` | 1 | 2 | Malformed field-pair and optional validator branch; real complete hierarchy checked in every snapshot. |
| `src/ergotools/presentation/desktop/authors_dialog.py` | 1 | 1 | Corrupt packaged logo decode rejection; asset bytes/integrity and ordinary About workflow covered. |
| `src/ergotools/presentation/desktop/duet_presenter.py` | 3 | 3 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `src/ergotools/presentation/desktop/duet_task_panel.py` | 0 | 1 | Conditional widget/item/scene presence, event forwarding or optional drawing branch; inspected listed source/conditions. No calculation or storage operation is silently skipped on the normal validated path. |
| `src/ergotools/presentation/desktop/job_management_dialog.py` | 11 | 18 | Empty selections/reentrancy/navigation bounds, cancelled search and Spanish search/information message branches; management and risk-profile workflow suite passes. |
| `src/ergotools/presentation/desktop/job_risk_table.py` | 1 | 1 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `src/ergotools/presentation/desktop/job_workplace_dialog.py` | 1 | 1 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `src/ergotools/presentation/desktop/lifft_presenter.py` | 9 | 11 | Wrong-tool/absent-source, stale editor, count bounds and row identity guards plus unchanged reset branches; normal edit/calculate/history suite passes. |
| `src/ergotools/presentation/desktop/lifft_task_panel.py` | 1 | 3 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `src/ergotools/presentation/desktop/lifft_window.py` | 59 | 76 | Management modal glue, source-absent/pending/cancel/overwrite warnings, optional diagnostic Help and navigation guards. Installed native EN/ES tools/VTK/PLOT/JROT and positional startup verified; normal Save As/Backup also exact at adapter boundary. |
| `src/ergotools/presentation/desktop/main_navigation.py` | 4 | 6 | Absent action/worker and wrong item-ID guards; real loaded navigation/recent menu shown in both languages. |
| `src/ergotools/presentation/desktop/manual_launcher.py` | 2 | 2 | Qt cache open/commit failure branches; actual packaged bytes/local-file URL/EN/ES Help contract checked by focused regressions. |
| `src/ergotools/presentation/desktop/organization_dialog.py` | 20 | 18 | Empty/stale/optional hierarchy selections, expandable details, identifier errors and cancelled/Spanish delete paths; record these as residual UI branches, not failed tests. |
| `src/ergotools/presentation/desktop/plot_chart_canvas.py` | 0 | 1 | Conditional widget/item/scene presence, event forwarding or optional drawing branch; inspected listed source/conditions. No calculation or storage operation is silently skipped on the normal validated path. |
| `src/ergotools/presentation/desktop/plot_filters_panel.py` | 2 | 4 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `src/ergotools/presentation/desktop/plot_graph_settings.py` | 0 | 1 | Conditional widget/item/scene presence, event forwarding or optional drawing branch; inspected listed source/conditions. No calculation or storage operation is silently skipped on the normal validated path. |
| `src/ergotools/presentation/desktop/plot_history_actions.py` | 10 | 7 | Native QLineEdit focus/typing paths and fallback event delegation; application filter/geometry history paths covered by focused suite. |
| `src/ergotools/presentation/desktop/plot_job_overview.py` | 0 | 2 | Conditional widget/item/scene presence, event forwarding or optional drawing branch; inspected listed source/conditions. No calculation or storage operation is silently skipped on the normal validated path. |
| `src/ergotools/presentation/desktop/plot_layout_canvas.py` | 0 | 1 | Conditional widget/item/scene presence, event forwarding or optional drawing branch; inspected listed source/conditions. No calculation or storage operation is silently skipped on the normal validated path. |
| `src/ergotools/presentation/desktop/plot_map_panel.py` | 2 | 0 | Interactive native file picker; injected image-import paths, decoded images and map persistence covered. |
| `src/ergotools/presentation/desktop/plot_marker_layer.py` | 15 | 13 | Wrong ownership/mode, duplicate settings, partial geometry restore and fallback replay without host. Integrated history uses host path; native maps and source snapshots validated. |
| `src/ergotools/presentation/desktop/plot_summary_figure.py` | 0 | 1 | Conditional widget/item/scene presence, event forwarding or optional drawing branch; inspected listed source/conditions. No calculation or storage operation is silently skipped on the normal validated path. |
| `src/ergotools/presentation/desktop/plot_tools_overview.py` | 0 | 1 | Conditional widget/item/scene presence, event forwarding or optional drawing branch; inspected listed source/conditions. No calculation or storage operation is silently skipped on the normal validated path. |
| `src/ergotools/presentation/desktop/plot_window.py` | 5 | 10 | Absent history/csv writer, rejected scope and close-without-event guards; actual native open/filter/project projections and resize verified. |
| `src/ergotools/presentation/desktop/plot_worker_controls.py` | 2 | 1 | No selection rejection and native success message; actual settings persistence characterized. |
| `src/ergotools/presentation/desktop/plot_worker_overview.py` | 3 | 5 | Filter reset, missing marker/selection and search-selection branches; real native map projects retained. |
| `src/ergotools/presentation/desktop/plot_worker_picker.py` | 0 | 2 | Conditional widget/item/scene presence, event forwarding or optional drawing branch; inspected listed source/conditions. No calculation or storage operation is silently skipped on the normal validated path. |
| `src/ergotools/presentation/desktop/plot_worker_preview.py` | 11 | 3 | Alternative marker painter shapes, comparison and empty preview; visual-only, no calculator/storage effect. |
| `src/ergotools/presentation/desktop/plot_workplace_dialog.py` | 0 | 1 | Conditional widget/item/scene presence, event forwarding or optional drawing branch; inspected listed source/conditions. No calculation or storage operation is silently skipped on the normal validated path. |
| `src/ergotools/presentation/desktop/rendering/vtk_body_renderer.py` | 3 | 4 | Invalid/closed animation state and timer scheduling/completion alternatives. Native body assets rendered for all tools; these are GUI timer branches, not scientific paths. |
| `src/ergotools/presentation/desktop/result_scales.py` | 0 | 1 | Conditional widget/item/scene presence, event forwarding or optional drawing branch; inspected listed source/conditions. No calculation or storage operation is silently skipped on the normal validated path. |
| `src/ergotools/presentation/desktop/results_sidebar.py` | 3 | 2 | No-probability/review-required view states; invalid/partial scientific status is characterized elsewhere. Current saved/partial EN/ES cards inspected. |
| `src/ergotools/presentation/desktop/rotation_comparison.py` | 5 | 3 | Wide comparison table sizing branch; drawing-only, schedule/evidence validation separate. |
| `src/ergotools/presentation/desktop/rotation_dialog.py` | 10 | 15 | Unavailable history/empty or cancelled scheme/scope/no pool branches; actual saved schemes, native default/enlarged forms and frozen links verified. |
| `src/ergotools/presentation/desktop/rotation_display.py` | 1 | 1 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `src/ergotools/presentation/desktop/rotation_history.py` | 1 | 1 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `src/ergotools/presentation/desktop/rotation_scope_dialog.py` | 1 | 1 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `src/ergotools/presentation/desktop/rotation_solve.py` | 12 | 8 | QThread.run is not measured by this pytest report. M5 additionally ran real QThreads with real CBC single-tool and HiGHS two-stage solvers, joined them, and validated schedule/backend/stages. Remaining guards suppress absent/stale preview. |
| `src/ergotools/presentation/desktop/rotation_table.py` | 13 | 6 | Wrong risk basis/exact restored-pool guards, editable index bounds and native Clear Cell context menu. Valid complete schemes/grid choices covered; native grid inspected. |
| `src/ergotools/presentation/desktop/text.py` | 1 | 1 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `src/ergotools/presentation/desktop/tool_tab_focus.py` | 0 | 1 | Conditional widget/item/scene presence, event forwarding or optional drawing branch; inspected listed source/conditions. No calculation or storage operation is silently skipped on the normal validated path. |
| `src/ergotools/presentation/desktop/tst_presenter.py` | 3 | 3 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `src/ergotools/presentation/desktop/tst_task_panel.py` | 0 | 2 | Conditional widget/item/scene presence, event forwarding or optional drawing branch; inspected listed source/conditions. No calculation or storage operation is silently skipped on the normal validated path. |
| `src/ergotools/presentation/desktop/worker_management_dialog.py` | 31 | 22 | Navigation/page/table-selection and country metadata branches, absent/unsaved assignment selection, Spanish delete/error and empty-placement messages. Worker/assignment persist/validation/history suite passes; no missing-record invention. |
| `src/ergotools/presentation/desktop/worker_transfer_dialog.py` | 9 | 6 | No request, unavailable selection and unexpected-error/logging/Spanish message paths; Copy/Move transactional rollback/currentness suite passes. |
| `tools/check_architecture.py` | 5 | 2 | CLI formatting/entry code runs before pytest under check.sh; negative inspection fixtures cover actual architecture rules. |
| `tools/check_documentation.py` | 13 | 5 | CLI formatting/entry code runs before pytest; negative fixtures cover function/receiver/generator/error contracts. Residual absence/reporting variants do not silently certify review. |
| `tools/check_documentation_review.py` | 13 | 5 | CLI entry/refresh runs outside pytest measurement; comparison/refresh-no-approval/tampering/new/deleted-source cases covered by negative regressions. |
| `tools/check_naming.py` | 7 | 2 | CLI enumeration/reporting runs before pytest; negative fixtures cover naming and case-collision rules. |
| `tools/project_migration/ergotools_migration/cli.py` | 3 | 0 | External subprocess success CLI path is not included in main pytest process coverage; real final delivered converter command separately exercised. |
| `tools/project_migration/ergotools_migration/legacy_assessments.py` | 1 | 1 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `tools/project_migration/ergotools_migration/legacy_catalogs.py` | 1 | 1 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `tools/project_migration/ergotools_migration/legacy_evidence.py` | 16 | 15 | Optional external historical-format fixture helper rejection guards and corrupt evidence reads; not used by current native storage/conversion output, no second result/archive in native files. |
| `tools/project_migration/ergotools_migration/legacy_plot.py` | 1 | 1 | Typed/absent state guard or early return; inspected listed source/conditions. Normal owned component behavior is covered by its focused suite. |
| `tools/project_migration/ergotools_migration/legacy_project.py` | 13 | 3 | Optional original snapshot helper is not on the current native Open path. Old-schema integrity failure and helper deserialization cleanup remain unmeasured, outside application package. |
| `tools/project_migration/ergotools_migration/legacy_reconciliation.py` | 3 | 2 | Negative/wrong model indices and ambiguous current source classification; supported conversion never invents data. |
| `tools/project_migration/ergotools_migration/legacy_rotations.py` | 3 | 3 | Invalid dimensions, ambiguous foreign cells and orphan child-record guards; supported comprehensive schemes retain exact references. |
| `tools/project_migration/ergotools_migration/previous_project.py` | 2 | 2 | Existing destination and unsupported prior version rejection; supported version upgrade suite covers sole-result format conversion. |
| `tools/project_migration/migrate_project.py` | 2 | 0 | External script entry/import is measured in its own process, not normal pytest coverage; installed native imports remain converter-free. |
