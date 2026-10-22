# Explicit current-version selection — F52

AssessmentHistory.with_current(document_id) selects exactly one existing version
within its assignment/model group. It preserves order, document ownership,
statuses and all other groups. Selecting the existing current row returns the
same snapshot; a missing document raises KeyError. A group with no current row
can select one, and an older version can deliberately become current.

The F44 reference table/index capture establishes at-most-one-current and the
independence of status/currentness. This new explicit repository operation conforms
to those constraints; it is not a claim that an equivalent reference assessment
UI command was captured. No status is automatically changed to complete or
superseded, and no scientific approval is inferred.

AssessmentProjectFile.select_current_assessment(expected, document_id) obtains a
write lock, validates hierarchy/history/source links, and compares the full saved
history with the expected snapshot before changing flags. A stale or foreign
snapshot fails without writes. It clears the old flag before setting the new one
to satisfy the partial unique index; both changes commit or roll back together.
Reads after reopening resolve the selected version. Source documents are not edited,
saved, deleted or activated.

Expected-value comparison detects saved ownership changes but does not lock external
source edits or detect an intervening change away from and back to equal history.
No automatic conflict merge is performed. Repository callers must refresh after
conflicts. This operation requires explicit version-six historical support and
does not upgrade existing projects.

Three new integration cases cover scoped switching, preserved status/source,
nonconsecutive versions, selecting the same row, missing/foreign targets, selecting
an older version, no previous current row, a competing connection and an injected
failure between demotion and promotion. All 466 tests pass; total coverage 98.91%,
history domain 100%, history store 95.56%. Ruff/format, strict mypy (101 files),
architecture and builds pass. The extracted wheel independently verifies switching,
stale-history rejection and reopen. All 500 original files and dependency lock
remain unchanged; see f52_validation.json.

This completes a repository lifecycle capability, not a desktop version selector.
Workspace-owned history snapshots, current-version controls and creation controls
still need composition with the existing dirty-source and callback safeguards.
No schema, dependency, UI or scientific formula change occurred.
