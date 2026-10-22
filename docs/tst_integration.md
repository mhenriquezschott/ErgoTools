# Integrated Shoulder Tool — F83

ST joins LiFFT and DUET in the existing `--integrated-preview` main window. The F82
eight-column task component is embedded directly into the original third tab;
no new permanent standalone app or redesigned layout is introduced. The original
window, tool captions, processed assets, body controls and results-card structure
remain the starting point.

## Selection, persistence and ownership

Shared operations route by the committed source, not an unaccepted tab click.
ST pending input parses/commits before shared Save, tool/context/file transitions
and close. Parsing failure retains the ST tab and entered text; dirty Cancel retains
the edited source. A completed transition refreshes the appropriate presenter.
Undo/Redo and Save/reopen keep explicit direction identities and original units.
Invalid preference changes restore the previous unit/decimal selector values and
retain text. Reset remains the deliberate way to discard invalid pending fields.

Bound tool switching selects the current ST version for the same historical
assignment. A missing tool requires explicit creation consent; new ST default data
contains 15 Handling Loads rows with missing numeric fields, attached to the same
assignment with next version and current marker. Unbound projects choose existing
matching tool documents or explicitly create blank data. Worker/context/version
operations retain ST kind. New blank historical versions remain noncurrent, as
in the existing version workflow. Open now lists all three supported source kinds;
the older LiFFT-only development harness retains its restricted listing.

## Cards, native camera and scientific boundary

The shared cards use original Individual Shoulder and shoulder-outcome captions,
source task/repetition/load metrics, and an absent maximum moment. The native
renderer selects the original shoulder shot through the portable BodyViewState
contract. ST review/pending/invalid states show no gauge/damage values or colored
shoulder overlays. Leaving DUET clears its old anatomical risk rather than treating
it as an ST result. Returning to another tool restores its source/region/captions.
No simultaneous retained multi-tool risk or camera animation is added in this slice.

The F82 scientific gates remain unchanged. Calculate exposes structured input
errors first; otherwise ST returns review.tst_direction and metric source also
returns review.tst_metric_moment, without task results or summary. The status card
says Review required instead of asserting readiness. This is integrated editing
and review behavior, not final calculation parity. Direction labels match explicit
new-format model data; the unresolved legacy index swap is not applied or used for
legacy import. No scientific formula or physical conversion was changed.

Spanish, metric/imperial input projections and the resizable main window are wired
to ST. A two-line Spanish shoulder outcome caption fixes observed clipping inside
the fixed-size gauge. Reset clears stale validation/review messages, matching the
original reset intention. Result metrics retain recorded source quantities; they
do not reinterpret a display-unit projection as persisted source data.

## Validation and remaining work

Five integrated native workflows cover all three tabs, actual Save/reopen, review
cards, invalid-text/tab/close protection, dirty Cancel/Discard, preference rejection,
localization, Reset, worker navigation, real version creation, explicit missing ST
creation and its ownership, and actual native shoulder camera/overlay/cleanup.
The existing main-navigation expectation now requires the ST tab enabled. The old
LiFFT geometry regression waits 30ms for native resize/layout/deferred header events;
it retains its same width/containment/scroll assertions.

Native captures include populated/review/expanded/Spanish/metric/pending-invalid/
empty-bottom/DUET-return/ST-return states at 1550×1015 and 1920×1200, checking the
avatar, cards, labels and bottom controls. As in F78, actual VTK framebuffers are
composed at the widget position into Qt captures because direct embedded-OpenGL
capture is unreliable under this compositor. Capture scripts are archived in
`docs/reference/f83-capture.py.txt`; images are in `artifacts/tst-integration/`.

Full gates: 662 native tests, 96.89% combined coverage, strict mypy (137 files),
architecture, lint/format and both builds. The extracted wheel exercises three-tool
switching, ST review/card/native scene, edit/Save/reopen and cleanup. All 500 reference
hashes and the approved lock remain unchanged (`f83_validation.json`).

Next complete task-count Settings for DUET/ST and the remaining menu/settings,
saved-data Delete and task-data selection operations. Scientific reviews, retained
multi-tool overlays/camera animation, PLOT/JROT, legacy import and final copied-project/
platform validation remain outstanding. Three connected tabs are not full parity.
