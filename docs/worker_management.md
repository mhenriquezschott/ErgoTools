> Historical component/checkpoint record. For current operation use [the user guide](user_guide.md), [development](development.md) and STATUS. Early pending-feature statements below are historical; M11 inventory records any actual remaining gap.

# Current integrated Worker Management — M02

Open the integrated application and use **Workers**. The original two-tab form,
details toggle, directory/search/navigation, assignment picker and Save/Cancel/Close
are retained. M02 acceptance is complete; see evidence.
Both height and weight are checked across metric/imperial Save/reopen, and all
three assessment tools return to the exact selected worker/assignment after Close.
Notifications now retain original `Note:` and localized `Nota:`.

The F72 text below is historical implementation provenance. Its temporary-preview
instructions and then-pending integration statements do not describe current UI
status. Its raw-original-unit warning still applies to M04 conversion acceptance;
new-format worker measurements remain explicit cm/kg internally.

---

# Worker Management — F72

The visible original Worker Management form now runs from the temporary LiFFT
preview. Launch `.venv/bin/python -m ergotools.bootstrap`, Open a new-format-six
or seven project, and click **Worker Management** in the header. For an empty
synthetic format-seven project, first run the documented Job Management demo,
then Open `.cache/job-management-demo.ergprj` in the assessment preview. Older
projects stay readable; the action does not implicitly upgrade their format.

## Migrated workflow

- Create and edit workers with an ID; names and demographic fields are optional.
- Preserve the original details toggle, two-tab layout, search, alphabet filter,
  record navigation, directory paging and viewport-dependent page capacity.
- Save names, birth date, sex, height, weight and hiring date. Existing internal
  address/contact fields remain retained even though the original visible grid
  does not expose them.
- Classify active assignments using compatible placements. Save commits worker
  details and all changed classifications in one transaction. Failure leaves
  both persisted catalogs unchanged and visible edits available for retry.
- Add Job Assignment opens the original table picker and commits immediately,
  retaining unsaved worker text. On Close the preview activates that exact
  assignment's existing LiFFT assessment. If none exists it asks whether to
  create a blank one; declining retains the assignment and active assessment.
  Existing dirty-assessment decisions apply before changing assessment source.
- Cancel restores the first saved worker; Close does not save form edits.
  Unreferenced workers can be deleted after confirmation.

Management commits remain separate from assessment undo. Classification uses the
existing historical assignment operations: reassignment preserves the original
assessment's assignment identity.

## Explicit differences and limits

Worker body quantities are stored as centimeters and kilograms, with typed unit
projection into cm/kg or in/lb. The original saves raw numbers according to a
parent-window label and does not record their unit identity in the worker row.
The new form preserves canonical values exactly on an unchanged Save, avoiding
rounding drift when reopened with another display system. This body-mass
conversion is independent of the assessment model's pound-force conversion.
Original worker import needs a reviewed source-unit policy before conversion.

Deletion currently protects **all saved worker assignments**, including ones
without assessments. The original deletes workers with cascading links. This
conservative interim limit protects retained assignment/history ownership;
reviewed assignment-aware deletion remains pending. It is not final deletion
parity. Adding an assignment in the preview asks before creating an absent
assessment; final main-window context activation remains to be migrated.

The original hidden experimental anthropometry tabs/calculations are outside
this visible-form checkpoint, consistent with the final feature-ledger stage.
They have not been discarded from the migration plan. Organization editing,
legacy-project import, full LiFFT/DUET/ST screens and final integrated navigation
remain pending. Existing placement selection works with focused synthetic test
projects; the empty standalone demo has no organization or placements yet.

## Persistence and localization

`WorkerEntry` accepts optional immutable `WorkerDetails`. The hierarchy JSON
payload now writes version **2** and reads versions **1 and 2**, without changing
SQL tables or project format numbers. Old name-only workers remain valid. Builds
before F72 cannot read newly written version-two hierarchy payloads. There is no
implicit source-project conversion or compatibility claim for the old app.

English and Spanish messages/tooltips are scoped to the worker form. Sex/date
values, identifiers, country suggestions and saved user text remain independent
of translated labels. Country suggestions are frozen from the reference's
pycountry list; no additional runtime dependency was installed. Spanish tab and
alphabet widths accommodate translated labels. Dates use the dialog locale;
body inputs accept dot/comma decimal text and save finite nonnegative values.

## Validation

603 tests pass, including nine new worker cases: both unit systems/reopen,
classification history, failure retry, actual SQLite rollback, directory paging,
delete protection, existing-assessment activation and both blank-assessment
creation decisions. The codec test's formerly unsupported version 2 becomes
supported; version 3 remains rejected. Ruff/format, strict mypy, architecture and
package builds pass; coverage is 97.34%.

Native XCB original/new English forms were inspected at 1360 × 760, including
collapsed, expanded, selected, new-record and assignment-tab states. Spanish
expanded/assignment states and the 980 × 500 placement picker were inspected.
The temporary assessment preview was checked at 960 × 680; its calculation and
bottom controls fit after placing management entry buttons in the header. No VTK
view is present in this temporary screen. The reference capture extracts the
original class for layout only and stubs its hidden tabs; it is not an original
application integration run or scientific validation.

The independent built wheel saves/reopens a worker with its processed icons and
unit conversion. All 500 reference file hashes and the approved dependency lock
are unchanged. See `f72_validation.json`; native capture and verification scripts
are archived under `docs/reference/f72-*.py.txt`.
