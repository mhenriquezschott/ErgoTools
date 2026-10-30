# Worker Management

Workers maintains identity, optional demographics and workplace assignments in the open
project. Worker ID is required. Names, sex, birth/hiring dates, height and weight are
optional; dimensions are normalized internally and displayed in project units. A blank
birth-date calendar opens eighteen years before today without assigning a birthday.
Hiring dates cannot be in the future.

The searchable directory, alphabet and first/previous/next/last navigation select records.
Unavailable initials are disabled. Add worker accepts one record and starts the next;
editing an existing field accepts valid data without a local Save button. Shared Undo/Redo
is available inside the window and in the main UI. Invalid text stays for correction or
explicit cancellation. The main project Save writes accepted changes.

Workplace assignments identify a station and shift, with an optional compatible Job.
Assign workplace, Change and Remove manage these records separately from assessments.
No Job assigned is valid. Changing/removing a workplace assignment keeps existing
assessments with their original historical owner. Closing Workers does not create or
associate assessments. Add/Delete assessment and Transfer are explicit main-window actions.

The assigned-workplaces table sizes location/Job/action columns to content and headers,
uses spare width, and scrolls only when required. Tooltips describe the hovered data or
action. See [ownership](assessment_context.md), [Transfer](assessment_transfer.md)
and [shared saving](single_project_save.md).
