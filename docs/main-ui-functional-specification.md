# Main Assessment UI Functional Specification

Status: current implemented behavior through 2026-09-15.

Scope: project handling, worker and organization management, assessment workplace
selection, and LiFFT, DUET, and Shoulder Tool assessment workflows. JROT is excluded
and will receive a separate specification.

## Purpose and Conventions

This document defines behavior that users and tests may rely on. It describes the
current application rather than a proposed redesign.

- **Must** identifies an invariant that should be protected by automated tests.
- **Current limitation** records visible behavior that should not be interpreted as
  a completed feature.
- An **assessment** is one worker's result for one ergonomic tool at one exact
  workplace and shift.

## Main Window

The main window contains:

1. The Project, Edit, View, Tools, and Help menus.
2. A project header and primary toolbar.
3. Worker selection and navigation controls.
4. Three equally prominent assessment tabs: LiFFT, DUET, and Shoulder Tool.
5. The 3D body-region view and risk legend.
6. The individual-result summary cards.
7. The assessment workplace footer.
8. A status bar showing the active tool, units, project, and assessment status.

The header must display the current project name and whether a project is loaded.
The footer must display the current project separately from the assessment status.

### Primary toolbar

The toolbar mirrors the main commands: New, Open, Save, PLOT, JROT, Export,
Settings, and Help. PLOT requires an open project. Export acts on the selected
ergonomic tool. Settings currently opens the task-count configuration. JROT is
visible, but its detailed behavior is reserved for the future JROT specification.

## Projects

### Project package

A project consists of an `.ergprj` XML descriptor and its referenced data and image
directories. The descriptor and companion directories must remain together when a
project is moved or shared.

Opening a project resolves the database relative to the descriptor, applies
non-destructive schema migrations, loads workers, organization values, shifts, and
jobs, then loads the selected worker and assessment context.

### Project commands

| Command | Expected behavior |
| --- | --- |
| New | Clear the current UI state and begin project creation using default workplace values and shift 1. |
| Open | Select an `.ergprj` file, resolve its companion database, migrate it if required, and load it. |
| Save | Save the project descriptor and current assessment data to the active project. |
| Save As | Write the project using a new project location/name. |
| Properties | Display descriptor metadata, database/data paths, language, and measurement system. |
| Export selected tool as CSV | Export the active tool's saved task and summary data. Canceling the file dialog must not create a file. |
| Quit | Close the application; `Ctrl+Q` invokes the same action. |

**Current limitation:** the generic Export and Export As menu actions are disabled.
CSV export is the supported main-window export path.

## Preferences and Help

- Number of Tasks accepts 1 through 100 and rebuilds the active assessment grid.
- Measurement System switches between Metric and Imperial labels and calculation
  units. A saved assessment is loaded using its recorded unit.
- English is enabled. Spanish remains present but disabled while translation work is
  incomplete.
- Animated body-region focus is persisted in application settings. When disabled,
  the model remains in the full-body view.
- User Guide opens the bundled PDF.
- About opens the author information dialog.
- **Current limitation:** Edit > Cut and Paste display informational messages and do
  not edit assessment fields.

## Worker Selection and Navigation

The worker selector displays a worker ID and, when available, the worker's last and
first names. The unique Worker ID is the identity key; names are optional.

| Control | Expected behavior |
| --- | --- |
| Worker dropdown | Select a worker from the current worker directory. |
| A-Z order | Toggle worker ordering between ID and last name. |
| Last-name alphabet | Limit the selector to workers whose last name starts with the chosen letter; All removes this limit. Unavailable initials are disabled. |
| First/Previous/Next/Last | Navigate the current ordered/filtered worker list. |
| Workers | Open Worker Management. |
| Search | Search saved assessments for the active ergonomic tool. |
| Transfer | Move or copy selected tool assessments between workplace contexts. |
| Refresh | Reload worker data and the current assessment. |

Changing workers must retain the currently selected assessment workplace. If the
new worker has no saved assessment for the active tool at that exact context, the
form must be empty; data from another station or shift must never appear.

When edited inputs are present, changing workers prompts whether to save them. The
chosen worker and workplace must remain internally consistent after either answer.

## Saved-Assessment Search

Search is specific to the active LiFFT, DUET, or Shoulder Tool tab. It does not show
workers merely because they exist; each result represents a saved assessment.

The dialog supports:

- Partial Worker ID, first-name, or last-name search.
- Last-name initial filtering.
- Workplace hierarchy filtering at plant, section, line, or station level.
- A result table containing worker identity, exact workplace, and shift.
- Selection of one exact assessment result.

Using a result must select both its worker and its full assessment context, then load
that record in the main UI.

## Assessment Workplace

### Identity

Every individual assessment is addressed by the following composite context:

```text
(Worker ID, Tool, Plant, Section, Line, Station, Shift)
```

The selected workplace applies to all three tool tabs, while each tool has a separate
record at that context.

### Visible behavior

The bottom bar displays:

```text
Assessment workplace  Plant > Section > Line > Station > Shift
```

**Select assessment workplace** changes which assessment location is being viewed.
It does not transfer, copy, or delete any record. Selecting a context immediately
loads the active worker's assessment at that exact location.

The selection must remain unchanged when the user:

- Navigates between workers.
- Changes the active assessment tool.
- Calculates, saves, deletes, or refreshes an assessment.
- Returns from PLOT without selecting a PLOT result for editing.

### Internal state

The visible footer is a read-only summary. The current implementation retains five
hidden `QComboBox` controls for Plant, Section, Line, Station, and Shift because
legacy load/save/delete functions still read those widgets. These are internal state
holders, not a second user-facing workplace selector and not part of JROT.

The application also stores an authoritative assessment-context tuple. The hidden
controls and footer must be synchronized to that tuple before assessment loading,
saving, or deletion. Code must never recreate the hidden combo boxes after UI setup.

Future refactoring may replace the hidden widgets with a dedicated context model,
provided all behavior and composite-key rules in this document remain unchanged.

## Organization Management

Organization Management maintains two directories:

- Location hierarchy: Plant > Section > Line > Station.
- Shifts: independent records referenced alongside a workplace path.

Supported operations are selection, creating a new plant or shift, adding the next
child level, editing optional details, saving, canceling edits, and deleting after
confirmation.

Identifiers are required and unique within their parent. Existing identifiers are
read-only because related records may depend on them. Stations are the final
location level. Deleting a parent may cascade to related child and assessment data;
the UI must request confirmation.

Returning to the main window should retain the previous assessment context whenever
all referenced records still exist. If a selected record was removed, the controls
must resolve to a valid available context.

## Worker Management

### Directory behavior

Worker Management provides live ID/name search, last-name alphabet filtering,
ordering, paginated results, row selection, and first/previous/next/last navigation.
The worker count and page indicators must reflect the filtered directory.

### Required and optional data

Only Worker ID is required. It cannot contain spaces and must be unique.

Optional details include first name, last name, sex, date of birth, calculated age,
height, weight, and date of hiring. Missing sex is displayed as `Not provided`.
Missing date of birth uses the date control's `Not provided` state. Date of birth and
date of hiring use the same `dd MMM yyyy` display format.

Height and weight labels follow the active measurement system. Missing height or
weight is permitted but produces guidance because those fields improve PLOT
demographic filtering.

### Worker commands

- New worker clears the editor for a new ID.
- Save changes inserts or updates the record.
- Delete requires confirmation and removes the worker according to database
  constraints/cascades.
- Cancel restores the selected saved record or clears an unsaved new record.
- Close returns to the main assessment UI and refreshes the worker directory.

Worker workplace/job classification shown in Worker Management is part of the
integrated work-risk model. Detailed JROT use of that classification is outside this
document.

## Worker Transfer

Transfer operates on saved assessment records, not only worker identity. The dialog
must show the source worker/context, available ergonomic tools, and a destination
workplace hierarchy.

The user selects one or more tools and chooses whether to copy or move:

- Copy retains the source and creates/updates the destination record.
- Move creates/updates the destination and removes the source record.
- The source and destination cannot be identical.
- Related task rows, assessment summary, and tool-specific PLOT marker information
  must remain associated with the transferred assessment.
- Cancel leaves the database unchanged.

After transfer, the main UI must reload the active worker and assessment context.

## Assessment Tools

All tools use a configurable task-row count, calculate task-level cumulative damage,
sum total cumulative damage, and convert the result to an outcome probability. The
result color and risk category use the shared risk ranges.

### LiFFT

Inputs per task:

- Lever arm, in centimeters or inches.
- Load, in newtons or pounds.
- Repetitions per work day.

Calculated values per task are moment, cumulative damage, and percentage of total
damage. The summary reports total cumulative damage and probability of a high-risk
job.

### DUET

Inputs per task:

- OMNI-Resistance rating from 0 through 10.
- Repetitions per work day.

Calculated values per task are cumulative damage and percentage of total damage.
The summary reports total cumulative damage and probability of a distal upper-
extremity outcome.

### Shoulder Tool

Inputs per task:

- Direction/type of shoulder exertion.
- Lever arm, in centimeters or inches.
- Load, in newtons or pounds.
- Repetitions per work day.

Calculated values per task are moment, cumulative damage, and percentage of total
damage. The summary reports total cumulative damage and probability of a shoulder
outcome.

### Common commands

| Command | Expected behavior |
| --- | --- |
| Calculate | Validate current task inputs and refresh task results, totals, risk color, 3D body-region state, gauge, metrics, and status. It does not by itself persist the project. |
| Reset | Clear the active tool's task inputs and calculated values. |
| Delete | Delete only the active worker/tool/exact-workplace assessment after confirmation. |
| Task-data grid | List saved assessment contexts for the current worker/tool and allow one to be selected for viewing. |
| Save | Persist all three tool forms for the active worker at the selected assessment workplace, where applicable. |

Saving at one station must not overwrite the same worker's record at another station.
Deleting at one tool/context must not delete other tools or contexts.

## Individual Result Presentation

The right sidebar always corresponds to the active tool and current form state. It
contains:

- Tool-specific individual risk title.
- Risk category and colored indicator.
- Semicircular probability gauge.
- Cumulative-damage value and scale.
- Tool-specific key metrics.
- Ready/Incomplete status and supporting text.

When no saved assessment exists at the selected context, task inputs and calculated
outputs must be empty/zero, the category must be `Not available`, and the status must
state that no assessment is saved there. Values from a previously displayed worker,
tool, station, or shift must be cleared.

## Body-Region View

The 3D view focuses on the anatomical region associated with the active tool:

- LiFFT: lower back.
- DUET: hands and distal forearms.
- Shoulder Tool: shoulders.

Calculated risk colors the active region using the current result color. Empty or
reset assessments hide the risk overlay. Rotate moves the camera around the model,
Zoom increases magnification, and Reset View restores the configured tool focus or
the full-body view when animated focus is disabled.

These interactions require VTK/OpenGL and must be manually checked in a graphical
session in addition to offscreen widget tests.

## Shared Risk Ranges

| Probability | Category | Color |
| --- | --- | --- |
| 0% through 25% | Low Risk | `#19B83F` |
| Greater than 25% through 37.5% | Moderate Risk | `#F5C400` |
| Greater than 37.5% through 50% | Moderate High Risk | `#FF8A19` |
| Greater than 50% through 100% | High Risk | `#FF3B30` |

Boundary values must follow this table exactly and the same palette must be used in
the main UI, PLOT, Job Management, and JROT.

## Status Rules

- Ready means assessment data is available for the active worker, tool, and exact
  context.
- Incomplete means no saved assessment exists there or required input is absent.
- The status bar and sidebar must describe the same state.
- Switching to an empty record must clear prior totals, gauge state, metrics, and
  body-region risk coloring.

## Excluded from This Specification

- JROT rotation creation, optimization, comparison, and persistence.
- The main-window Job selector, Job Management, job risk-profile versioning, and
  approval workflows, except where a job appears as worker-classification metadata.
- Proposed database changes not yet implemented.
