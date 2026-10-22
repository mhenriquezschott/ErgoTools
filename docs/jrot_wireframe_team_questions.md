# Questions for the JROT team — October 15 wireframes

Subsequent owner answers and provisional decisions are tracked in
[jrot_wireframe_discussion.md](jrot_wireframe_discussion.md). Read that record before
treating the original questions below as unanswered or authorizing implementation.

Thank you for the workflow and mockups. The guided steps can reuse much of the current
ErgoTools implementation. To retain compatibility and produce the expected results,
we need to clarify the points below before defining the next development cycle.
Page references are physical PDF pages / PowerPoint slides, counting the two introductory
process pages. Printed screen numbers currently contain duplicates and gaps.

## Decisions needed before choosing the data and optimization model

**Q01 — What does “station” mean in this workflow? (pages 6, 8–12)**
Does it mean a physical location, an activity/Job such as Wire cutting, or a specific
Job performed at a physical station? Can several Jobs share a station, and can one Job
be performed at several stations? If their task inputs differ by location, should they
be distinct Jobs? Our current application keeps Job risk values separate from physical
station identity. Would a simple display such as “ST01 — Wire cutting” satisfy your
workflow while retaining those separate records?

**Q02 — What time period do task inputs and direct risk values represent? (pages 1, 5, 10–12)**
For each tool, are repetitions per full workday, per shift, per block, or a rate? What is
the reference duration for an existing directly entered risk/damage value? Please give
one worked example with two Jobs, unequal block durations, task repetitions/damage,
expected worker result and expected report result. This determines whether time changes
only schedule weighting or also the dose/risk calculation.

**Q03 — How are shift duration, equal blocks and breaks defined? (pages 1, 3–5)**
Where should the user enter total analysis duration and the common block duration when
blocks are equal? Do blocks include breaks? Are all workers on the same timeline?
Should block lengths sum to the selected Shift duration, and how are overnight shifts
handled? Is the 30-second increment a hard requirement or display preference? The
illustrated unequal blocks sum to 600.5 minutes; please provide a consistent example.

**Q04 — What exactly are worker restrictions? (pages 7, 14)**
Please distinguish forbidden stations/Jobs, required qualifications, and a worker who
must stay at one station. Are these hard constraints or preferences, and do they apply
to the whole project, one Shift, or one rotation plan? Can they differ by block? Are
we storing operational rules only, rather than medical details? A forbidden station and
a fixed worker require different rules.

**Q05 — What staffing and capacity must the plan preserve? (pages 8, 9, 14)**
Must every station be staffed in every block? May a station have more than one worker,
including workers doing different Jobs there? Can workers be idle or on breaks, and
what happens when worker/station counts differ? Should total time at each Job remain
unchanged? On page 14, fixed Worker 03 shares Station 03 with another worker in blocks
2, 3 and 4. Is that intentional parallel staffing, or illustrative data to correct?

**Q06 — What is the optimization objective, and what does “improvement” mean? (pages 14–15)**
Our current single-tool model reduces the highest worker average; the multi-tool model
reduces the per-tool ceilings and then their spreads. With fixed Job use counts and equal
blocks, this redistributes exposure but leaves the overall mean unchanged. The mockup
shows a lower mean as well. Is that only illustrative, a different statistic, or a new
exposure/workload model? May the user optimize one selected tool, all three, or any
subset? Please provide expected results for a small example, including an unchanged
optimum and an infeasible case.

**Q07 — What should baseline results mean when rotation already exists? (pages 8, 13)**
Should the summary show each worker's full schedule exposure, per-block exposure, or
individual station hazards? The current-rotation matrix gives each worker several
stations, while the baseline summary shows just one station per worker. For the no-
rotation branch, may we repeat the primary assignment across the planned blocks to
compare the same workers, workload and time horizon? Are current permanent workplace
assignments merely starting suggestions, or should accepting a plan modify them?

**Q08 — Which risk thresholds and interpretation should be used? (pages 13, 15)**
Are the proposed common bands 0–25%, 25–50%, 50–75% and 75%+ intentional changes or
illustrative colors? Which measure does each band classify, and what happens exactly
at 25%, 50% and 75%? Current tools have established classifications that differ from
these common bands. Please provide the scientific basis/approved rules if changing
those interpretations. Also, should the page 13 warning refer to LiFFT 68% rather than
DUET? Its table currently places 68% under LiFFT and 42% under DUET.

## Workflow, data entry and reporting details

**Q09 — How should existing project data be reused? (pages 3–7, 10–12)**
Can the wizard select existing Workers, Jobs, physical stations and current risk values,
rather than create a separate set? Should it also support a project without organization
information by selecting Jobs directly? Station Information is optional in the notes;
please clarify how rotation targets are chosen when that page is skipped. Are count
fields simply a shortcut for preparing entry rows?

**Q10 — Are task names shared between tools? (pages 10–12)**
Are task names optional descriptions, or does the same named task have to be linked across
DUET, LiFFT and ST? Should the task name remain when copying an existing worker
assessment into a Job? Current task inputs have stable identities but no user-entered
name. A shared task and three independent named rows imply different data requirements.

**Q11 — What do Skip, Finish and validation mean? (pages 10–12)**
Does Skip mean “not relevant to this analysis,” “not assessed yet,” or “use an existing
value”? Can users finish a station with only one selected tool, then optimize that tool?
Should a complete zero-repetition task be valid? Page 12 shows 0.0 as missing; currently
blank and zero are different. Should a partially entered row block that tool while
unused blank rows are ignored? Which valid ST task categories correspond to “Lift”?

**Q12 — Which units and values are intended in the calculator examples? (pages 10–12)**
Please identify lever-arm and load units, including metric/imperial options. Is DUET's
“% damage” raw damage or percentage contribution? Are the sample results placeholders?
The LiFFT page shows one task with damage 5.890 and total 0.13665; the ST page shows
damage 65.000 with zero repetitions. A validated example for each tool would prevent
these illustrations being mistaken for new calculation requirements.

**Q13 — What does Approve & Compare do, and what must survive reopening? (page 14)**
Should it simply preview/compare and explicitly apply a proposed plan, or is formal
approval by a person required? Must baseline and proposed arrangements both remain
available after saving/reopening? We suggest keeping project Save in the main toolbar
and using Finish/Next only to accept valid edits, so users do not need several Saves.
Does this meet your expectation? Changing task values should make old proposals stale.

**Q14 — How are report statistics defined? (pages 1, 15)**
For each tool, should mean/max/SD/range summarize worker full-schedule values, all matrix
cells, or intrinsic station values? Is SD population or sample? What is the threshold
count/percentage denominator, and what happens to unassessed tools? Are the three
headline values means, maxima or another metric? Should differences display percentage
points, relative percent change, or both? For example, 44.0% to 36.3% is −7.7 percentage
points and −17.5% relative change. Please supply one internally consistent report example.

**Q15 — What report output and “compliance” are required? (pages 1, 15)**
Does Save Report mean export to a file or store a report inside the project? Which
formats and minimum contents are needed, including units, assumptions, date and solver
status? Does “compliance” refer to a named standard or formal sign-off? Without that,
would “Rotation analysis report” be acceptable? Must an exported report retain its exact
historical numbers after later Job edits? Current saved schemes reevaluate current Job
values; a historical exported report is a different deliverable.

**Q16 — Can you provide the complete intended screen sequence? (pages 2–15)**
Is Risk Preview missing from the files or merged with Baseline Risk Summary? Both
assignment matrices say Screen 6, Screen 10 is missing, and the flowchart points to
Slide 16 although the file contains 15 slides. Please confirm which sections may be
skipped when data already exist, whether the sidebar allows Back/jumping without losing
inputs, and the expected behavior on Cancel. One consistent scenario for each branch
would resolve several of the questions above at once.

## Suggested material to send back

Please provide a small, consistent example for each branch: existing equal-block
rotation, no current rotation, and unequal blocks. Include Worker/Job/station identities,
selected tools, time basis, task inputs or direct values, restrictions/capacity,
expected baseline/proposed matrices and expected per-tool report numbers. Mark which
illustrations are placeholders and which rules are requirements. These examples can
become acceptance cases after the owner approves the next-cycle scope.
