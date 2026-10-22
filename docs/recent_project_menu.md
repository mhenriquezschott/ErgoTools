# F89 — recent projects and explicit Close

Project > Recent projects now displays the existing bounded, newest-first user
history. Numbered basenames identify entries; action data and tooltips retain the
full location. Listing does not open project databases. It reuses the copied Open
icon, application theme and English/Spanish captions. No settings format changed.

A selected available project uses the same explicit assessment picker and lifecycle
as Open, including all three tools. Cancelled selection and failed/corrupt target
loads retain the current session. Failed targets are not silently forgotten.
A missing file instead offers an owned confirmation, defaulting to No, to remove
only its history entry. Removal does not commit pending assessment text. Failed
settings writes retain history and the current editor.

Clear history changes only recent locations, retaining preferences, project data
and pending task text. It is disabled for empty history. Settings adapter failures
are reported without losing the old history. Neither listing nor clearing history
creates a second project or edit policy.

Project > Close project releases the open project through the existing workspace
lifecycle. Valid pending task input is accepted as an ordinary source edit before
the existing Save/Discard/Cancel prompt. Invalid text blocks Close before that
prompt and remains visible. Cancel retains the open, possibly newly dirty source;
it does not undo valid input already accepted. Save persists it before release;
Discard leaves the last saved version intact. Closing clears the displayed
assessment/results and disables project operations, while keeping the main window,
preferences and native renderer available for another Open. Quit/window shutdown
still releases the renderer. Existing lifecycle warnings are surfaced.

## Validation

Seven focused regression cases cover three-tool invalid input, Cancel/Save/Discard
and reopen; database-free listing; write failure; pending-input preservation;
picker cancellation; corrupt-target isolation; missing-entry confirmation/removal;
and English/Spanish summary geometry after Close. Native visual inspection exposed
a pre-existing empty-grid translation problem: summary labels retained their prior
fixed width when no output cells existed. Label sizing now updates independently
of output alignment, preserving the original layout and eliminating Spanish
clipping.

The required approved-environment gate passes with 692 tests, 96.84% combined
coverage, strict mypy on 141 source files, lint/format, architecture and both
package builds. Captures under artifacts/recent-projects/ include populated
Project/Recent menus, empty Spanish Recent and disabled Close, actual owned
missing-file and dirty-close confirmations, invalid/Cancel Close and English/
Spanish closed main states. At 1550 by 1015 the native avatar, result cards,
headers, labels and bottom controls remain visible. Native VTK framebuffers
use the existing composed capture method.

An isolated extracted wheel passes three-tool Close Cancel/Save and recent reopen,
missing-entry removal, clear-history isolation, renderer retention on Close and
renderer cleanup on window shutdown. All 500 reference file hashes and the
approved lock are unchanged. Evidence: f89_validation.json, artifacts/f89-check.log
and archived reference/f89-capture.py.txt / reference/f89-verify.py.txt.
Only synthetic projects and preferences were used.

## Remaining scope

Opening a project with no assessment retains the existing no-assessments message
and current project; full empty-project Open is not implemented here. This is
incremental menu integration, not complete reference menu/workflow parity.
Next is Save As/backup, retaining the established project ownership and explicit
save policies. Transfer/export, View/Help, remaining dialog localization and
decimal preference persistence remain. Scientific direction/metric moment review
gates, remaining overlays/camera animation, PLOT/JROT, legacy import and final
copied-project/platform acceptance remain unchanged. The former 67% estimate is
withdrawn; no reliable replacement overall percentage or completion date exists.
