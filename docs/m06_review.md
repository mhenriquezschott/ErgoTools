# M06 bounded comparison and correction — complete

M06 closes at **89.00/100; 6/12 milestones complete; 15/26 remaining-baseline
points earned, 11 points left**. Its existing 2.5 points are awarded once. No
milestone, acceptance criterion or weight was added, removed or expanded. M07 next;
not started in this batch.

## CR004 closed — original requirement retained

The proposed removal of PLOT undo/redo was mistaken and withdrawn. The accepted
modernization plan already includes marker move/scale history. The owner reaffirmed
undo/redo across the application and extensible initial English/Spanish localization.
M06.1 stayed unchanged; no additional permission was needed for its implementation.

## Completed bounded work

Application-owned position commands now support released drag/scale, worker
settings, validated typed/batch edits, Cancel, Undo/Redo and selected explicit
Save. Styled localized Edit actions use platform-standard shortcuts and preserve
local typing history. Save failures retain intent; Undo after Save is a draft
change only. Exact fractional geometry and complete station order are retained.
See plot_history.md for ownership, partial-save and history-lifetime contracts.

The required comprehensive-copy acceptance found two concrete integration
failures: rounded field projections caused an extra Save edit, and remove/reappend
station ordering caused a false dirty state. Both were corrected within M06's
bounded correction pass and covered by regressions. Subsequent native harness
issues involved concurrent shared-display focus and an overlapping marker target;
final acceptance runs alone and verifies the selected item's hit target. Those
harness fixes required no further product changes. Initial failure logs remain
under artifacts/m06-history-native-first.log, -second.log, -concurrent.log and
-hit-test.log. Injected write errors in the successful log are expected tests.

Final full gate: 1,168 tests, 96.37% coverage; lint, format, strict types,
architecture and packaging pass. Final wheel: 83 focused native PLOT regressions
pass. Copied comprehensive EN/ES native workflow and independent reopen pass;
12 current captures inspected. Reuse valid original chart/export comparisons
rather than repeating unchanged scientific/export evidence. All 500 original
reference hashes and approved dependency lock remain unchanged.
