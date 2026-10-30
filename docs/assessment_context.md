# Assessment ownership and navigation

Each project permits one standalone assessment per worker/tool and one assessment per
workplace assignment/tool. A workplace identifies Plant, Section, Line, Station and Shift;
a Job is optional. Different workers, tools, assignments and shifts have independent inputs
and results. Reassigning a worker retains the previous assessment's original historical
owner rather than moving it silently. There is no selectable assessment-version lifecycle.

`WorkplaceContext` is the exact five-part location identity. `WorkerContext` adds project
and worker. `AssignmentAssessment` associates document ID, worker, tool and optional
assignment ID. Document identity remains distinct from display captions and path labels.
Standalone transfer targets use `StandaloneDestination`, without fabricating a workplace.

The main worker navigation opens the active tool's standalone source first. If absent,
it chooses the alphabetically first saved workplace source. If neither exists, it shows
a deferred standalone preview rather than inserting an empty record on navigation alone.
The expanded Assessment group selects existing saved sources through cascading Plant /
Section / Line / Station / Shift choices. Only relevant branches appear; Station includes
risk, and Job information remains separate. Counts belong to headings rather than names.
The selection summary identifies the source even when the group is collapsed.

Add assessment chooses a real workplace/shift and optional Job with the shared tree picker.
It creates a blank source, or replaces the existing selected-tool inputs after confirmation.
Delete lists existing current-worker/tool sources and removes the confirmed assessment only.
Transfer is the explicit Copy/Move workflow for standalone and workplace destinations.
These commands use shared project history and the main Save.

See [database tables](database_tables.md), [Transfer](assessment_transfer.md),
[Find](saved_tool_data.md) and [user guide](user_guide.md).
