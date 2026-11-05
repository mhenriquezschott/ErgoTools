# Guided rotation comparisons and rework

Normal JROT compares and reopens accepted rotation runs. Report export remains disabled
while the team defines its contents and formats. The optional Legacy editor cannot replace
or delete these guided records.

## Current input review versus saved results

The input-review page has Worker schedule averages and Job risk values tabs. These use
the current editable scenario, current shared Job values and copied timing. Worker values
summarize their entered schedule; they do not come from individual worker assessments.
An absent or incomplete schedule/tool stays unavailable, displayed as a dash.

The optimization and comparison pages display a valid unkept preview or an explicitly
kept optimization run, with that status stated above the results. Saved results always use their frozen worker/Job labels, numerical coefficients,
timing, baseline/proposal and solution. They are never silently recalculated using today's
Job values. Changed inputs, Job measurements or neighboring sources produce a stale label
while the original result remains readable. The saved setup, analyzed tools and qualified
solver status are shown explicitly. All analyzed-tool tabs display the same solved schedule;
viewing another tool or table does not run the optimizer.

Opening JROT restores the remembered rotation, falling back to the first name/ID-ordered
record when no valid selection exists. A selected record with a kept run opens step 08
with the drawer collapsed; an unsolved record opens step 01 with the drawer expanded.
Choosing another rotation from the combo follows the same rule. Reading or closing
a clean saved result creates no rotation, Job values or dirty project data.

Unsupported older/future run models retain read-only schedules and provenance, with no
newly interpreted weighted indices or rework claim.

## What the comparison means

The before side uses the run's saved baseline, otherwise its explicitly entered/generated
starting proposal. If neither exists, there is no before score or change. A No-path solve
never invents an observation. Explicit rework can promote a saved result to a reference
baseline; this is called a baseline, rather than claimed as a new physical observation.

Both sides use the same frozen Job coefficients and timeline. Worker change is after minus
before in percentage points; a negative change means a lower planning index. Worst index,
spread and population mean are shown separately. Under full staffing the population mean
is invariant: redistribution can improve the worst worker while increasing another worker's
index. These are weighted Job-risk indices, not individual injury probabilities or a new
physiological dose/recovery calculation.

Step 07 matrices show Job risks and weighted worker indices. Centered bold cells retain
full names/values in tooltips; row-number gutters have room for their labels. Content
minima remain readable while spare height enlarges rows modestly without forcing scrolling.
Step 08 uses separate white tool groups with strong titles, before/after arrows and
contrast-aware values. Show/Hide schedule details has an arrow and expands immediately
below the statistics. A separate High Risk Notice identifies intrinsic Job risks. It follows
the agreed comparison design: before/after maximum-worker-index cards,
per-tool statistics (mean, maximum, population standard deviation and range), and a notice
about intrinsically High Jobs. Optional schedule details contain before/after matrices and
matched worker indices. There is no chart. These views use one frozen solved schedule.

## Explicit retention and reoptimization

Run optimization produces a preview. **Keep optimization result** rechecks the current
project/session, inputs, coefficients and explicit neighboring runs before one shared
undoable project edit. **Keep result & compare** performs that same action and opens 08.
The original baseline is unchanged. Replacing an existing kept run requires confirmation;
Discard preview preserves it. Closing an unkept preview offers Keep, Discard or Cancel.
Main Save publishes kept data; reopening displays it without another solve. Cancelled,
failed or stale solves cannot overwrite it. Changed inputs retain prior frozen evidence
with an explicit stale label.

No-path feasibility generation remains distinct. In 04, Generate initial proposal creates
only a starting proposal, confirms any replacement and stays in 04 for further editing.
Step 07 only optimizes; feasibility generation is available only in 04.
No-path generation fabricates neither an observed baseline nor an optimization run.

The comparison page has separate icon buttons for the following advanced operations.

Rework as a new rotation is the default path. It asks for a new name, creates an independent
identity/source-scenario link, copies the saved setup/date and promotes the accepted
arrangement to the new baseline once. The original scenario and result remain intact.
Current shared Job values are used for the next calculation; old Job profiles are not
restored. The copied date/setup can be edited through the ordinary steps.

**Replace original baseline…** is an explicit alternative. Its No-default warning explains
that the editable baseline changes, and that the original baseline survives only in the
retained old run until that run is replaced, or through Undo. Create a new rotation to keep
both permanently. Changed inputs make the old run stale; no-op changes invent no history.

All accepted actions use shared chronological Undo/Redo and Main Save. Duplicate creation
and selection form one coherent history action. Cancellation of a bounded solve preserves
and redisplays the previous accepted run. A retired project session cannot publish or
project a late result. Save As, backup and reopen retain the existing native24 records;
J07 adds no schema, codec, solver, dependency, threshold or fixture migration.


## Editing starting assignments and block clocks

Step 04 permits manual cell edits, Clear assignments and Generate initial proposal for
both a baseline (Yes path) and a proposal (No path). Clearing a baseline preserves Yes-path
intent with unentered cells; it does not switch to No observation. Generation is a feasible
starting example, not an observation or risk optimization. Explicit confirmation permits
replacing baseline assignments; Undo restores them. The previous kept run and its frozen
baseline remain recorded, becoming stale if current inputs differ. Step 04 stays open.
Normal optimization and Keep never promote results to the baseline.

Entered and solved matrices share clock headers: from/to ranges appear below block/duration
when every column has room. Crowded views retain compact headings; header tooltips always
retain complete known time ranges. Break pieces and overnight (+1) suffixes use the existing
minute projection. Missing clock information stays absent. Header presentation changes no
column minima, assignments, scientific results or project data. Step 08 arrows use the same
packaged next icon as application navigation.
