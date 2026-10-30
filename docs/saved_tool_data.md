# Finding saved assessments

The main worker row's Search action opens `WorkerSearchDialog` for the active tool.
Standalone assessments appear first in the scope tree, followed by All workplaces and
saved workplace branches. The initial All selection shows both standalone and workplace
sources. Filter by ID/name, surname initial or an exact hierarchy prefix.

Results retain exact document and assignment identities in item data, so sorting and
repeated station names never change the selected assessment. Saved risk percentages use
the shared colors; unavailable calculations are labeled explicitly. Historical workplace
owners remain individually addressable. Selecting a row and choosing Use assessment opens
that source without changing workplace assignments or copying data. Cancel preserves the
current source and pending text; invalid pending input must be resolved before departure.

Delete assessment reuses this picker with only the current worker/tool's existing sources,
then asks a separate confirmation. Removing an assessment keeps its workplace assignment;
Clear assessment instead retains the assessment and its task rows.

The former `ToolDataDialog`, `SavedToolOption` and `saved_tool_options` implementation has
been removed. Its bottom grid button is replaced by +/- Task. No runtime client should
import those retired modules. See [assessment ownership](assessment_context.md),
[task counts](task_count_integration.md) and [API contracts](api_contracts.md).
