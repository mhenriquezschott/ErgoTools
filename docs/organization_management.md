# Organization Management

Organization maintains Plant → Section → Line → Station and independent recurring Shifts.
A Station is a physical location; a Job is an assessed activity that may be placed there.
Workplace assignments combine a worker, station, shift and optional Job. Assessments can
belong to those assignments or remain standalone.

Each hierarchy level has its own required identity and optional details. Plant opening
date and Section/Line/Station creation dates use optional calendars. Plant operational
duration uses hours/minutes. Shifts in use is derived from distinct shifts referenced by
active worker assignments or Job placements in that Plant, not an editable count.

Recurring Shift start/end times use optional 24-hour controls (00–23 / 00–59). Typing
0830 or 8:30 enters 08:30; 8: advances to minutes. Ends next day permits overnight shifts.
Unspecified time differs from midnight. Recurring shifts do not store dated incident or
ergonomic-risk event counts. Station details do not contain the removed task description,
equipment, ergonomic risk level, performance metric, power or materials fields.

Valid edits use the project session without local Save buttons. Shared Undo/Redo preserves
optional-detail expansion and surviving hierarchy expansion/selection. Deleting referenced
records is protected. Closing the window retains accepted edits; main Save publishes them.
The main Assessment selectors browse the selected worker/tool's saved sources through the
same hierarchy without creating assignments merely by selecting a location.

See [database tables](database_tables.md), [assessment ownership](assessment_context.md)
and [the user guide](user_guide.md).
