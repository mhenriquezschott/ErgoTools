# PLOT Functional Specification

Status: current implemented behavior through 2026-09-20.

Scope: Plant-Layout Organizational Tool (PLOT), including filters, risk views,
plant canvas, Tools Overview, Worker/Job Placement Overview, outcome summaries,
and empty states.

## Purpose

PLOT presents saved individual LiFFT, DUET, or Shoulder Tool assessments and current
approved Job risk estimates in their organizational and spatial context. It displays
one plant layout at a time, filters assessment results and active Job placements,
draws Worker and Job markers, and summarizes the active scope.

## Window Structure

The resizable PLOT window contains:

1. Ergonomic Tool filter.
2. Workplace filter.
3. Optional Worker demographics filter.
4. Individual, Job, and Comparison risk-view selector.
5. Clear Filters and Apply Filters commands.
6. Plant View action rail and layout canvas.
7. Tools Overview and mode-specific Worker or Job Placement Overview tab.
8. Tool Outcome area with filtered statistics, risk ranges, group gauge(s), and
   highlights.

The minimum supported window size is approximately 1300 x 900. Resizing must retain
a usable plant canvas and must not clip the outcome area or overview controls.

## Filter Application Model

Filter controls are pending selections until **Apply Filters** is pressed. Applying
filters must rebuild the worker dataset, plant image/markers, overview, outcome, and
highlight details as one coherent state. **Clear Filters** resets controls to their
defaults; the user applies them to refresh the analytical view.

The applied tool name must label the outcome group and highlight-detail dialog. A
later un-applied click must not relabel already displayed results as another tool.

## Ergonomic Tool Filter

LiFFT, DUET, and Shoulder are persistent, equally weighted selectors. Exactly one is
selected. Applying the filter limits map markers, filtered statistics, group gauge,
and highlights to saved assessments for that tool.

The Tools Overview charts may compare all three tools even while the map and outcome
area use one applied tool.

## Workplace Filter

### Scope hierarchy

PLOT displays only one plant image at a time. Within that plant, the user may select
one or more nonredundant branches at Plant, Section, Line, or Station level and one
shift or All shifts.

- Selecting a parent includes all descendants.
- Selecting a parent removes redundant checked descendants.
- Multiple sections, lines, or stations are allowed only within the same plant.
- Selecting an item in another plant clears selections from the former plant.
- At least one workplace scope is required to accept the dialog.
- A higher-level and its descendant must not be counted twice.

The compact filter displays the plant ID and either the selected ID, `All`, or
`N selected` for Section, Line, and Station. Hover tooltips provide full hierarchy
and included-scope details. Shift is independent of the location hierarchy.

### Default scope

Clear Filters restores:

- The first available plant.
- All sections, lines, and stations below that plant.
- Shift 1 when it exists, otherwise the first available shift or All.

## Worker Demographic Filters

Worker demographics is collapsed and disabled by default. Enabling it reveals:

- Sex.
- Minimum and maximum age.
- Minimum and maximum weight.
- Minimum and maximum height.

Only enabled demographic controls constrain the result set. Numeric ranges are
inclusive. Workers lacking a value required by an active numeric filter do not match
that filter. Units shown for height and weight must follow project/worker data rules.

Demographic filters combine with the selected tool, workplace paths, and shift; they
do not replace those filters.

## Plant Layout Canvas

The selected plant supplies the background image. Saved assessment markers are
drawn over it using their persisted position and visual properties.

Marker semantics by view:

- Individual uses a triangle for Male, circle for Female, and hexagon when sex is
  not provided. Fill identifies the individual assessment risk category.
- Job uses one filled square per active Job placement. Its fill identifies the
  current approved Job risk; multiple Workers assigned to that placement do not
  duplicate the square.
- Comparison nests the smaller individual Worker symbol inside the applicable
  filled Job-risk square.
- A blue border identifies the selected marker.
- Visible controls whether a marker is drawn.
- Enable controls whether its result participates in summaries and outcomes.
- Lock prevents marker movement.

Filtering may destroy and recreate scene items. Any active Locate pulse must be
canceled before scene replacement so no deleted Qt graphics object is accessed.

## Plant View Actions

| Action | Expected behavior |
| --- | --- |
| Open image | Select/load the layout image associated with the displayed plant. |
| Save layout | Persist the current plant layout image association/state. |
| Zoom in | Enter click-to-zoom mode for the canvas. |
| Zoom out | Reduce magnification without going below the 1:1 scale. |
| Actual size | Restore the current layout view and marker rendering. |
| Marker opacity | Cycle non-background scene items through the implemented opacity levels. |
| Capture image | Save a raster capture of the current plant layout view. |
| Export | Export the current filtered PLOT dataset to CSV, excluding visual/internal fields. |

Canceling an Open, Capture, or Export file dialog must leave state unchanged.

## Tools Overview

The overview provides three selectable charts:

1. Total Worker Distribution by Tool: average outcome probability by ergonomic tool
   with standard-deviation error bars.
2. Worker Risk Distribution by Gender and Tool: tool results separated by recorded
   gender.
3. Worker Risk Distribution by Age and Tool: tool results grouped by age.

Every bar must have a black border. Clicking the chart opens a larger interactive
viewer. The chart description and scale note must change with the selected chart.

Graph Settings controls:

- Show/hide title.
- Show/hide legend when the chart has one.
- Show/hide horizontal grid.
- Show/hide bar values.
- Default, fixed 0-100 risk, or custom vertical-axis maximum.
- Text-size scaling.
- Save the displayed graph to an image file.

Settings apply to regenerated graphs and canceling the dialog must retain the prior
configuration.

## Worker Overview

Worker Overview operates on the current filtered assessment-result dataset, meaning
one worker may appear more than once if distinct workplace/shift results match.

### Selection

The worker selector supports ID/last-name ordering, last-name alphabet filtering,
first/previous/next/last navigation, and a search dialog. Search results identify the
exact worker, workplace, shift, and tool record.

Selecting a worker result must:

- Select and frame the corresponding map marker.
- Display its full workplace breadcrumb.
- Display available age, sex, height, and weight.
- Display tool, cumulative damage, and outcome probability.
- Render a marker preview using the proper shape and risk color.
- Load its visibility, enable, lock, X, Y, and scale values.

### Locate

Locate identifies the selected marker and briefly pulses its border. It is enabled
only when the selected result has a live marker. It must work for a dataset containing
one worker and for larger datasets. Reapplying filters, changing plants, or otherwise
rebuilding the scene must safely cancel the pulse.

### Visual controls

- Visible immediately shows or hides the selected marker.
- Enable includes or excludes the selected result from summaries/outcomes.
- Lock enables or prevents marker movement.
- X and Y identify/persist marker position.
- Scale controls selected marker size.
- Save persists the selected marker's position and display settings.
- Save All applies the entered common scale and persists all current markers.

The plant image control must retain its allocated size when Worker Overview content
changes.

## Job Placement Overview

In Job view, the second overview tab becomes **Job Placement**. It operates on the
active placements in the current applied workplace, shift, and ergonomic-tool scope.

- The selector, first/previous/next/last controls, and Locate select the exact Job
  placement and corresponding map square.
- The panel displays the full workplace/shift context, Job identity, assigned-Worker
  count, current Job cumulative damage and probability, and approved profile/version.
- X and Y represent the shared, shift-independent Station anchor. Worker-specific
  saved marker coordinates remain separate.
- Dragging a Job square or editing X/Y creates a provisional movement only. The
  database must remain unchanged until **Save position** is pressed.
- **Cancel movement** restores the prior displayed position. **Save position** commits
  the Station anchor and refreshes every placement that shares that Station.
- While movement is pending, placement selection/navigation is disabled so the
  pending edit cannot be applied to a different placement.

## Filtered Results

Only enabled results in the current applied tool/demographic/workplace scope contribute
to statistics.

Displayed statistics are:

- Total Workers.
- Average Age for workers with birth-year data.
- Male count and Female count.
- Male and Female average cumulative damage.
- Male and Female average outcome risk.
- Overall average cumulative damage.
- Overall average outcome risk.

Sex-specific averages use only records explicitly identified as Male or Female.
Overall averages use all enabled matching results.

## Group Outcome

In Individual view, the group score is the arithmetic mean of outcome probability
across enabled matching Worker results. Job view summarizes active placed Jobs.
Comparison shows separate Individual-average and applicable-Job-average gauges.
Every gauge uses the same shared risk ranges defined in the main UI specification.

The gauge label is tool-specific:

- LiFFT Group Risk Score.
- DUET Group Risk Score.
- ST Group Risk Score for the Shoulder Tool.

The legend shows the four shared probability ranges. It explains categories; it does
not represent counts.

## Highlights

A high-risk result has probability greater than 50%. Highlights group such results by
station and report:

- Station ID.
- Number of high-risk worker results.
- Average probability among those high-risk results.
- Maximum probability among those high-risk results.

A single high-risk worker is sufficient to create a highlight. Detection must work
for LiFFT, DUET, and Shoulder Tool.

The compact warning reports the number of high-risk results and affected stations.
View details is visible only when details exist. Dialog and content titles include the
applied tool, for example `PLOT LiFFT Highlight Details` and `LiFFT High-risk station
details`. Average and maximum cells use the corresponding shared risk color with a
legible foreground.

When no high-risk result exists, PLOT displays a neutral message and hides View
details.

## Empty Scope Behavior

When no enabled assessment result matches the applied filters, PLOT must clear all
previous data:

- Worker selector becomes empty.
- Worker identity, demographic, assessment, preview, and visual controls are cleared
  or disabled.
- Locate is disabled and its internal target is `None`.
- Total Workers and sex counts become zero.
- Averages display an unavailable dash rather than stale values.
- The chart displays an explicit no-results state.
- Group gauge resets to 0 with `Not available` status.
- Highlight details are cleared and View details is hidden.
- The plant background may remain, but no stale worker marker may remain visible.

This behavior must also hold when records exist but every matching result is disabled.

## Data and Persistence Boundaries

PLOT must distinguish:

- Worker identity/demographic data.
- Individual assessment data for an exact tool/workplace/shift.
- Assignment/classification data.
- Tool-specific marker visual state.
- Plant layout image state.

Changing marker position or visibility must not alter task inputs or calculated risk.
Changing a filter must not move, copy, or delete an assessment. Saving a marker must
not overwrite another tool or workplace marker.

## Shared Terminology

- Use **Workplace** for Plant > Section > Line > Station plus Shift filtering.
- Use **assessment workplace** for the exact context viewed in the main UI.
- Use **ergonomic tool** for LiFFT, DUET, and Shoulder Tool.
- Use **outcome probability** for the percentage shown by gauges and risk colors.
- Use **worker result** when one worker assessment at one context is counted.
