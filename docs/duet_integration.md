# Integrated DUET workflows — F80

The original main window now embeds both migrated task components, with its
existing layout, processed icons and shared panels. DUET selection is enabled;
ST remains visibly disabled until its original controls are migrated. The CLI
`--integrated-preview` uses the existing native VTK adapter. No dependency,
scientific formula, schema or project-format change was required.

## Ownership and actions

A clicked tab requests a model; committed source determines the accepted tab.
The window restores the source's tab before processing a request, commits all
pending grid input atomically, then applies existing Save/Discard/Cancel policies.
Rejected text stays visible. Cancel restores the original tab and data. Bound
assessments select the same assignment's current document for the requested tool.
If missing, the existing creation prompt requires Yes before creating default
rows with retained assignment ownership, the next version and current status.
Unbound projects select existing matching documents explicitly when ambiguous or
ask before creating a new source. Opening lists only supported migrated models.

Worker/context and blank-version operations now route by active assessment kind.
Shared Save commits pending DUET input before transactional persistence. Reset is
one reversible source edit. Close checks DUET text, dirty decisions and project
cleanup before finalizing the renderer and releasing both presenters' contexts.
The prior isolated LiFFT harness stays LiFFT-only; mixed selection belongs to the
integrated preview.

## Shared results and anatomy

DUET's evaluator supplies immutable typed results, not parsed labels. The shared
cards display its probability, damage, explicit incomplete/ready state, task count
and repetitions; load/moment show dashes as in the reference. Its body labels,
footer tool and outcome captions update in English/Spanish. The original DUET
camera shot frames arms/hands; calculated risk colors all four active patches.
Changes, Reset and invalid input remove obsolete color. Returning to LiFFT restores
its document, view and camera. No dimensional conversions apply to DUET inputs.

## Verification and limitations

650 native tests pass, 96.76% combined coverage. Six new integration workflows
cover assigned tool selection, shared calculations/cards, edit/Save/reopen, canceled
and invalid transitions, localized Reset/worker routing, explicit creation for
unbound and bound data, and actual native scene/close cleanup. All standard gates
and builds pass. Native full-window captures include selected/populated/empty,
calculated/expanded/error/Spanish/bottom-scroll and return states. The original
DUET component comparison is recorded in F79; F80 inspects its full-window fit
with the actual avatar and cards. Composed captures use the real VTK back buffer,
not a fabricated avatar. The independent extracted wheel verifies both tools
from another launch directory. All 500 reference hashes and the F79 lock remain
unchanged; see `f80_validation.json` and `artifacts/duet-integration/`.

Complete menu/settings, DUET task-count changes, saved-data Delete/task-data
selection, simultaneously retained per-tool overlays and optional camera animation
remain pending. The Settings task-count action is disabled while DUET is active,
rather than invoking the LiFFT reset operation. Tab captions retain the reference
English branded names; complete menu/tab localization remains planned. ST,
PLOT/JROT, legacy project import, full project lifecycle, final copied comprehensive
project and Windows/macOS acceptance remain incomplete. LiFFT metric and ST model
review gates are unchanged. Two connected assessment tabs do not imply complete
application parity or a reliable whole-migration percentage.
