# F112 — original worker marker menu and assessment editor handoff

Source mapping: `src/visualworkertool.py`, `showContextMenu`, `lockItem`,
`saveItem`, `loadintoToolWindow`; `src/plant_layout.py`, `saveVars`; and
`src/main.py`, `loadEditVarsToUI`. Job markers have no source context menu, so
this slice adds actions only to worker markers. Commented Delete/Rotate/Scale
entries are not implemented source actions and are not introduced.

Right-click selects the clicked assignment once and opens the original three
entries in order: Lock, Save, Load into Tool Window. The native text-only source
menu is preserved without adding unrelated icons. English/Spanish captions are
owned by the existing language contract. The temporary menu is parented to the
canvas, closed and released after execution. Opening a menu performs no writes.

Lock previews `locked=True` in the existing worker settings and disables drag;
Save uses the existing transactional marker save and error/retry path. It commits
valid marker geometry/settings, not partially typed invalid overview fields.
Source `lockItem` changed only Qt's movement flag without updating its persisted
lock value; the migrated action records the actual lock consistently on Save.
Unlock remains the original overview checkbox, not a redesigned menu action.

The marker layer receives an injected `SummaryExportRow -> bool` editor operation.
Load resolves the clicked saved assignment/model from the current PLOT rows,
without parsing worker-combo text or workplace labels. `LifftWindow` validates
project identity and the saved current document before accepting editor text, then
uses the existing pending-input and Save/Discard/Cancel policy. It clears the
appropriate cached evaluations and refreshes the selected integrated tool after
success. Same-document loading retains raw widget edits and undo/session identity.
Source data/units and scientific gates stay unchanged; no calculation or evidence
approval is performed implicitly.

Deliberate safety correction: pending marker edits block handoff with a localized
message requiring Save/Cancel. Loading never implicitly commits/discards map edits.
A missing editor callback disables Load; loader failures are logged and shown
through the injected localized error operation. Cancel/failure returns False.
Neither marker nor editor discovers/forces a parent close through Qt ancestry.
The complete PLOT host must resolve all field/close intent and close only after an
accepted handoff. That parent composition is still pending, and production PLOT
remains disabled; these component tests are not a claim of complete PLOT parity.

## Validation

Five focused native cases exercise English/Spanish menu captions, real right-click,
selection, lock, pending-map block, Save failure/retry and persisted lock, callback
Cancel/error/absence, exact owner/model handoff for LiFFT/DUET/ST, foreign and
noncurrent document rejection, raw same-source edits, actual editor Cancel/Save/
Discard persistence and unchanged positions. Existing fixtures are synthetic.
Full checks pass: 865 tests, 96.42% coverage, Ruff/format, strict mypy on 180 source
files, architecture, wheel and sdist. The isolated wheel repeats menu lock/save,
pending-map interlock, actual editor Cancel/Save and all three tool handoffs;
reopened positions and source units/data match their expected persisted values.

Native evidence contains 20 images: two original menus, six localized normal/
selected/disabled menus, six full integrated tool windows and six raw VTK frames.
Menus and complete windows were visually inspected. English normal/selected menus
match the source pixel-for-pixel. Full 1548×1060 windows retain their existing
avatar region, assessment headers, result cards, labels and bottom controls without
new clipping. The existing F94 evidence method archives native VTK buffers and
composites them at their Qt widget position because QWidget.grab alone leaves
native OpenGL child content black. Spanish ST's pre-existing long task-choice
elision remains outside this slice; this does not claim final whole-window parity.

Evidence: `f112_validation.json`, `artifacts/f112-check.log`,
`artifacts/f112-wheel.log`, `artifacts/f112-native.log`,
`artifacts/plot-context-actions`, and reproducible `reference/f112-capture.py.txt`
and `reference/f112-verify.py.txt`. All 500 reference hashes and the approved lock
remain unchanged. No dependencies, architecture layers, source models, unit rules
or VTK adapter changed.

Next: original summaries and full PLOT composition, including parent close consent
and the final load/close sequence, remaining map/deletion actions and acceptance.
JROT follows with CBC single-tool, HiGHS multi-tool and no GLPK. Overall completion
percentage and finish date remain unvalidated.
