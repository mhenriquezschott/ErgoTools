# Independent task counts

Counts belong to one assessment source: project, worker, tool and context. Worker
assessments begin with 15 rows by default and support 1–100. Job task-input mode uses one
starter row for an empty tool, rather than the worker's 15-row template.

Main +/- Task controls sit between Clear assessment and Calculate. Plus appends one blank
row and reveals it for entry; minus removes the final row. Buttons disable at their limits.
Settings > Assessment can set a larger count at once and identifies the affected project,
worker, tool and workplace/standalone owner. It does not change other assessments.

Increasing preserves existing rows and adds new identities. Reducing retains the prefix
and asks before removing entered trailing data. An unchanged count is a no-op. Shared
Undo/Redo restores removed rows, inputs and matching results. The main Save publishes the
accepted count and data. There is no global task-count preference and no destructive
reset on ordinary count changes.

Wholly unused rows are ignored by calculation and do not make an otherwise complete
assessment partial. A started row with missing required fields still requires correction.
Clear assessment empties the selected source while retaining its count, units and owner.

The hosts use the existing typed per-tool count commands and presenters. The shared
`AssessmentTaskGrid` renders rows and reports edits; it owns no calculator, repository or
Undo stack. See [shared editor](shared_assessment_editor.md).
