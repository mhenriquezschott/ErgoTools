# Integrated PLOT and saved worker CSV — F118, 2026-10-08

PLOT is enabled in the existing integrated main toolbar when an open full project
supports the saved job/assessment data. Closing the project disables PLOT; JROT
remains disabled. This connects the source-derived PLOT components from
F103–F117 to the main application rather than adding another permanent UI.

## Project ownership and modal workflow

`application.plot_access.PlotRepository` combines the existing PLOT result,
image read/write and explicit position-save capabilities. The workspace exposes
a borrowed port after checking full-project support. The desktop receives only
that typed port; it does not acquire project lifetime or close its connection.
The bootstrap composition function injects validated image import, packaged icons,
CSV writing and the existing exact-assessment handoff callback. The modal owns
its widgets; the workspace retains the project throughout the single-user modal.
A second connection is unnecessary and could leave the workspace adapter's format
state out of sync after map/position schema upgrades. The same borrowed adapter
receives those explicit saves and remains usable afterward.

Opening PLOT deliberately leaves unfinished assessment input text uncommitted,
as existing saved-data browsing/export does. The existing F112 handoff decides
how to commit/resolve editor input if another exact saved assessment is loaded.
Foreign/no-longer-current assignments remain rejected; dirty Save/Discard/Cancel
policies remain those of the integrated editor. The host closes only after its
own consent and accepted editor selection. The actual context action is connected
through the existing marker layer, without copying mutable parent variables.

The modal integration exposed a concrete Escape gap: QDialog.reject bypasses
closeEvent. PlotWindow now applies the same default-No unsaved-image/marker
consent to rejection and window closing. Cancel retains the visible window and
pending intent; accepted closure stops locate/animation activity once through the
owned rejection path. It never implicitly saves map/assessment edits.

## Original CSV mapping and explicit provenance

Reference `plant_layout.py` grtool9ButtonClicked and
`plot_position_repository.py` plot_worker_records define the source export.
The original 28 retained columns remain in the same order: worker/assignment,
full workplace, tool/damage/percentage probability/source unit, worker metadata
and job/current approved profile evidence. Map coordinates and visual style
fields remain excluded. Fixed English machine headers and decimal points remain
independent of interface language. Saved workers are exported even when a marker
preview is hidden; view/style settings do not redefine membership. The applied
saved result snapshot supplies rows; edited filter intent or pending marker
geometry is not exported.

The appended columns are project_id, assessment_id, assessment_version,
evaluation_status, issue_keys and worker_body_unit. They distinguish exact source
ownership, scientific-review absence and the unit of body values. Canonical cm/kg
worker metadata is projected into the current display system with the body-unit
column, instead of exporting physically ambiguous values. This is independent of
the recorded ergonomic assessment source unit. Probability is percent, retaining
full arithmetic precision; no display/gauge clamp or model formula changes.
Unavailable values are empty, observed zero remains zero, and scientific gates
stay unavailable. This is a documented extension of the source interchange
format, not a claim that legacy metadata representations are identical.

The original dated WorkerStationShiftData filename, CSV/All Files chooser,
native overwrite confirmation, success message and no-data warning are retained
with EN/ES captions. Cancel performs no write. The infrastructure writer encodes
UTF-8 with standard comma quoting/CRLF into a same-directory temporary file,
then atomically replaces the selected target. Encoding/replacement failures
retain an existing target and remove ordinary temporary files. Errors report an
actionable localized message while preserving editor/map state. Existing
assessment summary CSV behavior is unchanged.

## Validation

Six focused cases verify retained headers/provenance, body unit projection,
missing versus zero, scientific-review blanks, quote/comma/newline round trips,
atomic replacement failure/cleanup, chooser cancellation, export success/error/
empty data and pending marker preservation. Real main actions open the owned
modal; the context-menu Load action selects another exact worker's DUET document.
Tests verify borrowed connection identity, history retention, continued saves
and image format upgrade through the same handle, clean cancellation/no-project
availability, and native Escape No/Yes consent. Earlier component tests retain
their pending-assessment checks; only their superseded disabled-PLOT assertion
was updated. Their persistence/input assertions continue to pass.

Twenty EN/ES window/modal/menu captures cover the enabled main toolbar, actual
PLOT, minimum/enlarged populated/empty states, CSV success/error/no-data and worker
context menu. Main UI before/after handoff includes avatar, headers, result cards
and bottom controls. Qt grabs cannot reliably capture native OpenGL under this
compositor, as documented in F78; four real VTK back buffers are placed at their
exact widget coordinates in those main images. They are explicitly composed
captures, not direct system screenshots. No whole-application pixel-parity claim
is made from synthetic integration fixtures. Actual export examples are archived
as en-workers.csv and es-workers.csv. The original retained-column mapping was
reviewed against source query/exclusion order and recorded separately.

898 tests pass with 96.88% combined coverage. Ruff/format, strict mypy,
architecture and wheel/sdist checks pass. Independent extracted-wheel execution
uses the real main toolbar, owned modal, saved CSV writer and context-menu DUET
handoff without implicit project writes. All 500 reference hashes and approved
dependency lock are unchanged. See f118_validation.json, artifacts/f118-check.log,
artifacts/f118-wheel.log, artifacts/f118-capture.log and artifacts/plot-integration.
Reproduction scripts are archived under docs/reference/f118-*.py.txt.

## Remaining migration

This is usable integrated PLOT for migrated full-project data, not final parity
with every legacy project or target operating system. Original-format import and
the comprehensive copied project's final integration test remain later work.
Existing scientific review gates remain open where previously documented. Next
is the original JROT workflow/solver/UI migration: CBC single-tool, HiGHS
multi-tool, no GLPK. Prepare exact versions and obtain the required dependency
approval before installing or changing the approved environment. Then validate
cross-feature project behavior and final original UI/workflow parity.
