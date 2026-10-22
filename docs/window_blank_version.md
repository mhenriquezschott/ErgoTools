> Historical checkpoint, superseded by the owner-directed removal of assessment versions.
> See [current ownership contract](single_assessment_ownership.md). The version UI/API described below no longer exists.

# Blank historical version creation — F55

New blank version in the temporary LiFFT window creates an empty draft for the open
assessment's exact assignment/model group. The confirmation displays the proposed
version and states that the current version will not change. Version allocation
uses one above the group's highest saved version; a UUID supplies the source ID.
The initial source retains the open assessment's recorded units, with no task copy.

Pending text requires explicit Apply/Discard first. After confirmation the existing
Save/Discard/Cancel prompt handles dirty source. Source identity/revision and the
workspace history snapshot are checked again before calling the existing preflight
and atomic historical creation workflow. Final uniqueness checks handle a competing
version creation; there is no automatic retry under a different version number.

Success opens a clean, persisted, noncurrent draft and clears prior calculated
results. Cancel creates nothing. Save persists the prior source before creation;
Discard leaves that prior saved source untouched. As in F47, a late creation failure
can leave the old source clean if its separate Save already succeeded. Old versions
and currentness remain intact. Set current version is a separate deliberate action.

The action requires an existing assignment link in a version-six project. Older
projects, no open project and unbound sources cannot invent ownership. This is not
a first-assessment creation flow or a worker/job setup screen. The preview remains
LiFFT-only; no default project format or legacy files are changed.

Three new desktop scenarios cover pending protection, empty-source/unit retention,
saved reopen, unchanged current owner, Save/Discard/Cancel, stale history and unbound
sources. All 474 tests pass; total coverage 98.92%. Ruff/format, strict mypy
(101 files), architecture and builds pass. An extracted-wheel test creates and
reloads a blank version through the actual window action.

Native XCB inspection covers empty/populated/pending windows, Spanish at 960 x 680,
English/Spanish confirmations, dirty-choice prompt and resulting blank noncurrent
editor. The complete task region, result panel, labels and bottom controls fit
without visible clipping. Existing text-only button/picker styling is reused;
no icon assets were needed or added. Evidence: f55_validation.json and archived
f55-capture.py.txt. All 500 original files and dependency lock remain unchanged.
No schema, dependency or scientific formula change occurred.

Next: first-assessment/project setup and complete worker/job record workflows,
followed by integrated model UI, legacy import and final parity validation.
