# Current assessment context picker

The owner-approved October 12 context-navigation update supersedes the historical
F39 integration status below. The integrated main window uses classified assignment
selection with four columns: workplace hierarchy, type, Job and Saved/New assessment.
The hierarchy stretches while remaining columns size to content, keeping status visible
at the original 700×540 minimum. All labels/tooltips and summaries support English
and Spanish. Exact typed assignment IDs, not captions, select ownership. Selection
opens saved data or a deferred draft and never moves/copies data or creates a record.

See current workflow and regression catalog.

---

# Classified context chooser — F39, 2026-10-01

The current reference uses AssessmentWorkplaceDialog, a classified-job assignment
hierarchy with a shift filter. Its older inline context controls are hidden by
setupTabsTopControls. The new reusable AssessmentContextDialog follows the active
dialog: 700 x 540 minimum, 18/16 margins, 10px vertical spacing, three hierarchy/type/
job columns, current-context expansion, wrapped context summary and Use/Cancel.

The injected ClassifiedAssignment values combine existing AssignmentSnapshot
ownership/eligibility with explicit job display metadata. The dialog filters exact
project/worker, active assignment, non-null placement and active placement; only
assignment leaves can be accepted. Shifts use the catalog's binary-sorted IDs.
Repeated eligible ownership is rejected. The catalog-backed boundary does not
reproduce the reference fallback to assignment-derived shifts when the shift
catalog is absent: unknown catalog membership cannot produce a valid selection.

Assignment input is a snapshot supplied by the caller, not a database query or a
complete job model. The future adapter must supply ordered, current, classified
assignment data and enforce job/placement consistency. No operational data is read.

## Handoff and scope

Acceptance prepares an AssessmentSelection through the existing presenter, without
saving or switching documents. The host must resolve pending widget text and dirty
choice, then call the selector's select/create operation. Cancellation leaves the
workspace unchanged. A stale catalog or missing membership prevents acceptance and
shows a reopen instruction. The presenter rechecks active source when the host
executes the request. Missing stored assessments are not implicitly created.

This component is not wired into the temporary LiFFT harness or the final integrated
window yet. Persisted job assignment editing, host pending-text/dirty dialogs and
main-window context summary synchronization remain pending. There is no Organization
editor action in this dialog, matching the reference's separate main-window action.
English reference labels are retained; localized variants are still required later.

## Visual inspection and validation

All six required icons (plant, section, line, station, jobmanagement and cancel)
exist as packaged processed assets and are injected as QIcons. No replacement icons
or dependencies were introduced. Palette, typography and controls reuse the existing
Qt stylesheet with the audited reference dialog-specific styling.

Native XCB captures at 700 x 540 were inspected for populated/current selection,
collapsed hierarchy, empty shift, stale catalog, and expanded shift popup. The first
capture revealed a clipped selected Type label and a system-blue selection gutter.
The Type column was widened to 140px (reference 90px) and the branch highlight set
to the same teal as selected rows. Recaptured states show complete labels, wrapped
summary and unobscured bottom controls. Images: artifacts/context-dialog/*.png;
reproduction: reference/f39-capture.py.txt. No VTK or adjacent main-window regions
changed; full integrated-window geometry acceptance remains pending.

401 tests pass, including five new real Qt scenarios with synthetic version-four
projects. The new module has 100% combined coverage; total coverage is 98.85%.
Ruff/format, strict mypy (90 files), architecture and builds pass. Independent wheel,
reference/lock and screenshot integrity evidence: f39_validation.json. Original
files and approved dependencies remain unchanged.

Next migrate persistent classified job/placement/worker-assignment records, then
wire the chooser into the integrated selection workflow with dirty-text handling.
Do not populate final UI choices with synthetic assignments or infer jobs from
available workplace combinations.
