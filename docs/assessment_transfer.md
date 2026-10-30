# Assessment Copy and Move

Transfer uses the exact saved source assessment context and selected tools. Sources may
be standalone or associated with a workplace assignment, including historical ownership.
The destination worker is explicit. Choose the first Standalone assessment row, or a
station in the hierarchy plus a shift. Standalone destinations need no organization data.

Copy retains the source. Move removes only the selected source tools after the destination
has been created successfully. Inputs, task identities, units and source-bound calculated
results retain their saved precision; transferring does not recalculate them. Each copy is
independently editable. A workplace destination reuses its active assignment or creates
an unclassified assignment; a standalone destination creates no workplace assignment.

Missing selected destination tools are created. Existing selected tools remain selectable
and their risk values appear in the tree. The preview names the tools to replace. The
localized confirmation defaults to No; No/Cancel changes nothing. Unselected tools,
Job risks, historical owners and workplace assignments remain. The identical source owner
cannot be the destination. Historical observations are not silently replaced as active data.

The integrated project keeps accepted transfers privately until the main Save. Shared
Undo/Redo restores replaced targets and Move sources together. Moving the displayed
assessment opens its destination; Copy keeps the source visible. Invalid pending source
text must be resolved before an operation that removes that source. Copy can use existing
saved data while unfinished local text remains; normal valid cell completion still applies.

## Implementation

- `domain/assessment_transfer.py`: immutable `TransferRequest`, `StandaloneDestination`
  and `TransferPlan`, membership/self-transfer checks and selected-tool replacement rules.
- `application/transfer_access.py` and `ProjectWorkspace`: borrowed capability, expected
  snapshots, source acceptance and invalidation of retired browsing sessions.
- `infrastructure/assessment_project_file.py`: one write transaction preloads sources,
  removes approved targets, inserts exact copied sources/results, then removes Move sources.
  Any failure rolls back the entire transfer.
- `desktop/worker_transfer_dialog.py`: source tools, destination worker/tree/shift,
  saved-risk badges, selection interlocks and explicit confirmation. No SQL is in the UI.

`replace_existing` defaults False for programmatic callers. The GUI grants it only after
confirmation and checks that the approved target set has not changed. Expected catalog
checks repeat under the write lock. No native-format change or project migration is required.

Regression coverage includes all three tools, standalone/workplace directions, same-worker
standalone creation, occupied/new targets, exact result replay/Save/reopen, retained sessions,
localization, self-transfer rejection and failures after partial multi-tool insertion.
See [API contracts](api_contracts.md) and [the user guide](user_guide.md).
