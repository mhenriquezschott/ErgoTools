# Organization Management — F73

The default assessment preview now exposes **Organization Management** alongside
existing work-management controls. Run `.venv/bin/python -m ergotools.bootstrap`
from this new project. Create a new project, open Organization Management and
save a Plant. Use Add element for its Section, Line and Station; the Shifts tab
creates independent shifts. Job Management can then place a job at that station,
and Worker Management can assign the job and activate/create its assessment.
This is a usable migrated management workflow in the temporary preview, not the
final integrated main window.

## Original form and separation

The implementation ports the reviewed `OrganizationWindow` layout, field order,
stylesheet, dimensions, icons, directory tabs, collapsed optional details,
selection, Cancel/Save/Delete/Close actions and tooltips. Runtime assets are
packaged copies; no reference application imports or database accesses occur.
English and Spanish labels are presentation translations; stored identifiers and
field keys remain stable. Root creation uses one connected slot that chooses its
action from the tab, avoiding the reference's repeated signal reconnections.

Typed immutable `OrganizationRecord` values validate known fields, complete
ancestry, finite numeric values and unique metadata. Pure application functions
compose these values into the existing hierarchy. The modal owns unsaved form
text, and the existing workspace/repository publishes only a successfully saved
snapshot. A failed database write leaves entered text available for retry. Cancel
reloads saved fields or abandons an unsaved new record. Close does not autosave.
Returning from the modal does not rebuild the assessment editor.

## Storage and units

Hierarchy JSON now writes payload version 3 with optional organization metadata.
Versions 1 and 2 remain readable without fabricated operational data. Earlier
migration builds cannot read catalogs saved by this checkpoint. SQL schema is
unchanged. Desktop New uses existing project format 7 so work-management controls
are available immediately; the lower-level creation API retains its format-2
default and supports an explicit initial version. Existing project files are not
implicitly upgraded or converted. The initial preview assessment stays unbound
until an explicit assignment/assessment workflow creates a bound assessment.

Worker body quantities still use canonical cm/kg, and assessment force/length
units still have their existing metric/imperial boundaries. This form retains the
reference's explicitly named units (seconds, hours, kWh) for operational fields.
Unspecified Area/Capacity quantities are not assigned invented units or converted.

## Intentional limits

Existing identifiers are read-only. Duplicate creation and missing parent keys
are rejected. Confirmed deletion removes an unreferenced subtree and its metadata;
existing job/assignment/assessment guards refuse referenced workplaces or shifts.
This conservatively differs from some original database cascades. Final deletion
parity must account for imported relationships and JROT records. The form does not
implement PLOT geometry, operational legacy import or final application navigation.

## Verification

Four focused tests cover the complete empty-project → workplace/shift → job →
worker → LiFFT workflow; actual SQLite rollback followed by retry/reopen; Cancel,
duplicates and subtree deletion; and payload compatibility/invalid metadata/full
field translation. All 607 tests and required standards/build gates pass.

Native XCB captures in `artifacts/organization-management` were visually inspected
at the original 1120×740 minimum. Matching Plant collapsed, expanded and scrolled
bottom captures are byte-identical to the isolated reference class on the same
host/Qt environment. Empty, selected Station, Shift and Spanish states are also
inspected, as are both 960×680 preview languages. This verifies the migrated form,
not final assessment/VTK parity. Synthetic reference data lived only in temporary
files. The extracted wheel independently opens the owned organization modal,
creates the hierarchy/shift, saves operational data and reopens the project.

See `f73_validation.json` and archived characterization/verification scripts in
`docs/reference`. All 500 recorded reference files and `uv.lock` are unchanged.
