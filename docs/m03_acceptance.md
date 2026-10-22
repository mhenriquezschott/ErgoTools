# M03 — Organization and Jobs acceptance complete

M03 earns its fixed **2.25 points**, moving **80.5% → 82.75%**.
Three of twelve milestones complete; 8.75/26 remaining-baseline points earned,
17.25 still to earn. M04 is next and was not started. No scope/weight change.
This milestone closes existing implementations; no production repair was needed.

## M03.1 — original forms and native visual evidence

The original OrganizationWindow constructor, field definitions and stylesheet run
read-only under the approved new Qt baseline with a disposable synthetic database.
Seven matched screenshots are byte-identical: Plant collapsed, expanded and bottom
scroll, Station collapsed/expanded, selected Shift and new Shift. Empty-project,
selected hierarchy and Spanish states were also inspected. The selected-Shift
harness explicitly selects Day; changing the directory tab alone does not select it.

Original JobWindow constructors/styles match common visible control rectangles,
button icon sizes and table column widths in eight cases: empty, approved, draft
and evidence states at 980×720 and 1120×740. Original DB callbacks are stubbed;
projected fixture values compare layout, not original data writes or calculator
outputs. New version selects the evidence tab, so draft/evidence captures share
that tab; separate packaged measurement/evidence views cover both. Original-table
cells remain empty in this layout oracle; existing scientific tests provide the
numeric/color evidence. No UI was reconstructed from screenshots.

Reuse original-source placement comparison F59/F60 and individually inspect its
expanded/selected and minimum-size original/new images. Existing processed icons,
form arrangement and filtering are retained. The unchanged independent wheel adds
eight inspected full-window captures and one expanded profile-options image:
Spanish Station/Shift, approved/draft Jobs including both tabs at minimum size,
Spanish selected/filtered placements at minimum size and empty placements. Fixed
bottom buttons fit; optional organization details scroll as in the original.
No VTK, integrated result card or assessment-table region changed in M03.

## M03.2 — usable persisted workflows

**64 focused regressions passed against the extracted wheel**, covering:

- Empty project → Plant/Section/Line/Station/Shift → Job/profile → placement →
  worker assignment → saved assessment, with independent reopen.
- Organization optional metadata, Spanish decimal input, duplicate validation,
  Save/Cancel, unreferenced deletion, referenced protection and SQLite rollback/retry.
- Job creation, copied draft versions, edited evidence approval, current selection,
  retirement, navigation/search/discard and independent reopen.
- Nested placement Save preserving unsaved job text; across-shift selection,
  hidden filtered selection, Clear, Cancel, protected deletion and failure recovery.
- Atomic job/profile Save and approval, immutable approved measurements, historical
  assignment ownership and zero programmatic checkbox event cascades.
- EN/ES captions, templates and locale handling without translating stored evidence.

An additional packaged smoke scenario uses the actual integrated **Jobs toolbar**
and **Manage organization footer** actions. Both open correctly parented modals;
Save persists a job and Station metadata, Close discards subsequent local edits,
assessment source identity remains unchanged, and independent reopen verifies data.
Its fixture contains LiFFT only. An initial attempt to switch to absent tools hit
the expected New assessment prompt; the harness was corrected, without application
changes. No three-tool smoke claim is made from that fixture.

The full M02 standards/types/architecture/build gate (**1,157 tests; 96.49% coverage**)
is reused: no production/test source changed, and the current wheel SHA matches
that validated artifact. No repeated full gate or rebuild was needed. All **500
reference hashes** and the approved lock remain unchanged. No packages installed.

## Explicit existing dispositions and remaining boundaries

The already documented generic Save success message replaces the original three
branch-specific notifications; it does not change Save results. It remains a
noncritical wording review entry, not hidden repair work or a new milestone.
Existing styled popup/search-icon corrections follow the asset/selection rules.
Referenced-record deletion remains conservative to preserve historical owners;
M03 does not reintroduce original destructive cascades over assessment history.
Original ambiguous metadata such as Area/Capacity receives no invented units.
Metric/imperial assessment measurements retain explicit source/result identity;
organization seconds/hours/kWh and stored free text are not silently converted.

M04 retains original-project conversion and body-unit provenance review; M09 retains
whole-app localization/units/avatar acceptance; M10 comprehensive integration and
M12 native platforms remain incomplete. This is M03 component/workflow acceptance,
not a claim of final whole-application replacement readiness.

Evidence: [validation](m03_validation.json), artifacts/m03-organization/,
artifacts/m03-jobs/, artifacts/m03-packaged/, m03-wheel.log and
m03-integration-wheel.log. Reproduction scripts retained in docs/reference/m03-*.py.txt.
