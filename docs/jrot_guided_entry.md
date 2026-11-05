# JROT — guided rotation planning

With a project open, use the main **JROT** button or **Tools → JROT**. This is the
production guided window; Developer mode is unnecessary. Accepted scenario and Job edits
use shared project history and the sole Main Save.

For compatible older schemes, Settings → General → Compatibility → **Show Legacy menu
for this session** exposes **Legacy → Legacy JROT…**. The switch defaults off after each
restart and is independent of Developer mode. Legacy omits guided records and cannot
replace/delete them, including unsupported timing, restrictions or saved result models.
Opening an older scheme in normal JROT preserves its unresolved date/timing until explicitly
entered; editing through normal JROT promotes it to the guided representation. It then
belongs to normal JROT and is no longer editable through Legacy. Back up before this change.
The disposable meeting prototype and its sample/default runtime paths have been retired.

## Saved scenario entry

Opening an empty scenario catalog creates nothing. Enter a rotation name, planned local
start date and optional description, then choose Create rotation. Internal identity stays
fixed when its name changes. Opening restores the remembered rotation, falling back to the first name/ID-ordered
record. A kept result opens step 08 with the drawer collapsed; an unsolved selection
opens step 01 with the drawer expanded. Combo selection follows the same rule. Hover or click the
visible left rail to reveal the drawer. Its notch moves with the right edge; the
icon-only pin at the heading’s right keeps it open for this window.

The eight numbered pages cover setup, Jobs, workers, current assignments, tasks/validation,
input review, optimization and comparison/report. Back, Continue and the drawer allow free
review of any page. Incomplete setup does not prevent looking ahead. Invalid pending input
must be corrected before leaving it. Closing an uncreated named form asks before discarding
that form; it does not discard accepted project edits. Optimization runs the real planner with an explicit Keep optimization result boundary. The comparison page shows frozen before/after cards, statistics, optional worker/schedule details and a High Risk Notice;
report export remains disabled pending the team specification.

Choose a real Line and Shift using the hierarchy/clock picker. All Jobs offers active
project Jobs as unique global activities. Workplace scope offers exact active Job placements
within that Line and Shift; repeated placements retain separate position identities.
Selecting participating workers does not create/change permanent workplace assignments.
Create / edit Jobs opens the existing dedicated Job Management window, including its
placement editor. Create / edit workers opens the same Worker Management used by the
Main window. Worker selection initially shows existing active assignments in the selected
Line; switch to All project workers to include unassigned people or other Lines. Search
and the shared surname/Job-name alphabet filter without discarding hidden checks; counts
make those retained checks explicit. Job risk columns remain content-sized while names
or workplace context use the available width. Organization opens the existing editor.

The top Rotation selector chooses a stored record. Step 01's Rotation name edits
that same record; the uncreated selector entry explicitly directs naming in step 01.
There is no second user-entered rotation ID. The sidebar heading is Rotation. Tables
show full Block headings, bold taller headers and more comfortable rows. Catalog summaries
include workplace context and current colored tool results. See [three-worker walkthrough](jrot_walkthrough.md)
for the prepared project, missing repetition input and independently checked 3 × 3 outcome.

Use Shift timing explicitly copies its current template. Without a template it proposes
four equal blocks (or fewer for a very short Shift). Edit rotation timing uses the existing
break/equal/unequal timeline editor on the scenario copy. Breaks separate uninterrupted
numbered blocks; equalization confirms moving breaks while retaining names/durations. Future Shift template edits do not
change that copy, and scenario timing edits never write the source template. A completed
copied clock is independent of later recurring Shift clock changes. The rotation start/end
controls accept a complete 24-hour pair; end at/before start means next day. Relative breaks
and earlier unequal block durations are retained. Invalid shortened budgets remain
correctable; they are not silently rescaled or erased. Clearing timing keeps
entered matrix cells and their horizon available for later completion.

For new entry, Yes supplies an existing baseline, usually an observed rotation. Explicit rework can promote
a saved result to a reference baseline without claiming a new observation. It can be selected before participants are
chosen: the saved empty observed matrix is different from No observation. Choosing workers,
Jobs and timing creates only unentered cells, without a balanced/default schedule. Each
matrix combo changes exactly one cell. On the No path optional entered cells belong to the
proposal; Generate initial proposal runs a real feasibility model and stores only the proposal,
confirming replacement if needed, while staying in step 04. Removing workers,
positions or blocks reports how many entered cells would be lost and requires confirmation.

## Shared Job assessment controls

Tasks & validation lists the selected unique Jobs and the number of selected tools with
complete values. Repeated physical placements use the same Job data. The editor reuses
JobTaskEditor/AssessmentTaskGrid, source-unit validation, automatic calculation, task names,
Excel preview/paste, +/- Task, direct colored results, totals, gauge and risk ranges.
There is no separate calculation formula or alternative result profile. Personal gauge
markers and animation settings are inherited from the application preferences.

Copy worker assessment and Copy from Job use the maintained read-only hierarchy/source
pickers, including optional task subsets. Accepted data are independent copies, not links.
Editing here changes the project's one current value set for that Job/tool, which can make
other saved scenarios' accepted runs stale; their frozen original evidence remains intact.
Missing values stay absent. Selected analysis tools and the displayed calculator tool are
separate choices. The review page shows only selected-tool current Job risks and explicit
missing-input diagnostics. It does not invent worker exposures or optimization results.

## History, saving and ownership

All accepted data use the existing workspace transactions and shared chronological project
Undo/Redo. Clean page, scenario, Job, blank source-method and tool navigation use the same history; structural
changes preserve surviving cells by exact identity. Main Save alone publishes the private
working project. Closing retains accepted edits; no dialog-specific Save or rollback of
unrelated project work is introduced. Pending calculator failures remain correctable and
cannot be reported as saved. Expected-state/session and matrix-generation guards reject
stale completions. Duplicate creates an independent scenario; Delete warns and replay
restores the record and coherent selection together.

Native 23 introduced the compatibility marker, allowing Yes with an empty observed matrix
before participant selection. Native 22 introduced the scenario codec but could not represent
that draft. Legitimate native22 guided rows/runs upgrade exactly; unsupported new drafts
hidden under an old marker are rejected before conversion. Native24 now adds strict rule/boundary payloads and weighted run identity without changing
tables, columns, scientific calculators, source units, dependencies or thresholds.
Keep pre-upgrade files with the matching older code/package for recovery; changing a marker
manually is not a downgrade.

## Real planning and remaining integration

See [jrot_planning.md](jrot_planning.md) for duration weighting, all tool subsets, hard
restrictions, explicit neighboring-run checks, real generation, cancellation and explicit optimization retention.
See [jrot_comparisons.md](jrot_comparisons.md) for comparisons, saved-result reopening,
explicit generated proposals and advanced duplicate-first rework. Report export remains disabled pending the team specification.

The timing editor now treats work and pauses as uniform segments: both can move/resize, and Remove extends their actual immediate neighbors. Both count/equality groups are available; coordinated review preserves total time and explains changes to the other type. See rotation_timing.md for exact rules.


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


## Tool selection and optional neighboring results

Step 06 uses a compact joined strip of icon-bearing tool buttons, styled like PLOT.
Teal pressed buttons
identify included tools; unselected buttons stay neutral. Choose one, two or all three;
at least one remains selected. Roomy guided review/optimization/comparison tabs and tool
result headings use the same processed LiFFT/DUET/ST icons as the main UI. Narrow table
headers remain text-only where icons would crowd the data.

Step 03 Across-shift checks starts collapsed with a visible summary. Expand for preceding/
following result buttons, literal linked rotation names and a prominent help area. Hover
or keyboard focus explains chronology, activation and optimizer effects. Selection enables
only when a worker has No adjacent High plus the corresponding boundary flag. Retained
links are never removed when a rule is disabled; Clear link explicitly removes one. A
requested missing/stale link still blocks solving; no constraint is silently ignored.

Worker restrictions says Fixed Job and Excluded Jobs. A fixed Job is not offered for
exclusion; excluded Jobs and Jobs already fixed to another worker are disabled as fixed
choices. Other impossible static assignments revert immediately with visible guidance,
using existing one-worker-per-Job matching validation. Exclusion proposals that cannot
staff all Jobs keep the previous set. These are UI safeguards, not a relaxation of hard
rules; the optimizer still validates temporal and other constraints independently.
