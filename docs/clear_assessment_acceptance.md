# Clear assessment — verified, 2026-10-19

The owner approved replacing the duplicate assessment Reset/trash controls with one
**Clear assessment** button in LiFFT, DUET and ST. The saved-data chooser remains.
Clear applies only to the active worker/tool/context. It empties inputs and removes
its calculated output while retaining the assessment identity, task count/order,
original units and worker/workplace selection. Other assessments are unchanged.
DUET/ST retain their existing blank-row selector defaults.

The themed EN/ES confirmation identifies the project, worker and context; its title
identifies the tool. Cancel is the default and leaves pending input/data unchanged.
One shared Undo step restores exact inputs and results without recalculation; Redo
clears again. Main Save publishes the change. Blank Clear adds no history and keeps
Redo; no-project controls are disabled. No Add assessment control was introduced.

## Cause of the old blank grids

A private-copy reproduction showed the old trash operation removed only Ana's
LiFFT assessment (12 ownership records became 11); DUET/ST still existed. The
handler then lost the active assessment/navigation context, displaying all panels
empty. The new control uses established source-editing commands and history
instead of deleting the assessment and losing the current selection. Existing
backend deletion contracts remain for their lifecycle/integrity callers.
See [reproduction](../artifacts/clear_assessment_review/deletion_reproduction.json).

## Validation

`bash tools/check.sh`: **1,738 passed, zero failures/skips, 94.37% coverage**;
format/lint, strict types (265), architecture, naming, documentation/review and
wheel/source builds pass. Native focused checks: **126 passed / 78 subtests**.
Independent extracted wheel: **144 passed / 78 subtests**; all 243 package Python
files and both guides match reviewed source; external converter excluded.

Coverage includes all three tools, English/Spanish, metric/imperial, standalone and
real assignments, 1/7/15/100 task counts, Cancel, repeated Clear/Undo/Redo, exact
results, other-assessment isolation, main Save/reopen and failed-Save recovery.
Thirty-six native XCB/VTK captures inspected through full-window/enlarged control
sheets and dialog details cover populated, cancelled, cleared, restored and empty
states. Both updated packaged Help assessment sections were rendered and inspected.
Captures settled for 1,100ms before inspection so gauge animation was complete.
The first empty LiFFT capture in the Spanish harness retained startup English;
Spanish DUET/ST empty states and all populated/confirmation states were inspected.
This is not new acceptance of Spanish startup-preference behavior.

Nineteen maintained source/test files were substantively reviewed and their hashes
updated. Inventory: 431 files, 2,997 functions, 412 classes, 315 constants; zero
pending reviews/gaps. Architecture, API, saving and bilingual user guides updated.
Full evidence: [validation](../artifacts/clear_assessment_review/validation.json),
[package](../artifacts/clear_assessment_review/package.json),
[visuals](../artifacts/clear_assessment_review/visual_validation.json),
[protections](../artifacts/clear_assessment_review/protections.json).

The owner workflow project, both maintained comprehensive fixtures and uv.lock
retain their starting hashes. No reference writes, schema/formula/dependency changes,
new permanent fixtures or automatic backups. Linux migration/cleanup remains 100%;
Windows/macOS acceptance remains deferred. No additional milestone was created.

## Next owner check

Restart the application and reopen workflow_4_workers.ergprj. For Ana > LiFFT,
Clear > Cancel should retain 13.2%. Clear > confirm should leave 15 empty rows in
Ana's same context. Undo once should restore the inputs and 13.2%; inspect DUET/ST
as well. Main Save is the only durable save. Await owner feedback before continuing
organization setup; the owner project was not edited by validation.

## Owner feedback and equal-width follow-up — 2026-10-19

Owner confirms Clear works and requests matching Clear/Calculate widths around the
existing middle chooser. The three panel layouts remove the obsolete 320px Clear
cap and give both main actions equal stretch; the chooser stays 40 × 40 and both
actions retain their 40px height. No control rename, behavior or data change is
needed. Native EN/ES geometry checks cover all three tools at 1550px minimum and
1600px widths, allowing only Qt's unavoidable one-pixel split when free width is
odd. Evidence is in artifacts/clear_button_layout.

Final follow-up gate: 1,738 passed, zero failures/skips, 94.37% coverage; required
standards/types/documentation/builds pass. All 12 EN/ES bottom-row details and native
English LiFFT/Spanish DUET full windows inspected; no new clipping. Native screen
captures include VTK children. Owner project, maintained fixtures and lock unchanged.
See [layout validation](../artifacts/clear_button_layout/validation.json).
