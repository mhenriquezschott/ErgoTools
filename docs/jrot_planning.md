# Guided rotation planning

Normal JROT runs duration-aware planning on the project's selected Jobs and workers.
The separately optional Legacy editor retains only compatible older equal-block schemes.
Guided comparisons and rework are described in [jrot_comparisons.md](jrot_comparisons.md).
Report contents/formats remain deferred; the export button is disabled.

## Scores and objectives

For worker `w` and selected tool `k`, the planning index is
`sum(block_productive_minutes × assigned_Job_risk_percent) / averaging_minutes`.
The denominator is productive shift time when breaks are subtracted, otherwise the full
shift duration. Breaks have no assignment cells. This is a weighted Job-risk index, not a
new individual injury probability, accumulated damage, dose or physiological recovery model.
The scientific LiFFT/DUET/ST calculators and existing risk boundaries are unchanged.

All seven nonempty tool subsets are supported. Every tool subset uses direct HiGHS. There is no solver preference or fallback.
Both routes use the same model and
first minimizes the worst worker's index, then minimizes worker spread without
increasing that maximum beyond the existing tolerance. Two or three tools use the
approved HiGHS runtime: first minimize the sum of tool-specific worker ceilings;
then minimize the sum of spreads
while preserving **each** first-stage ceiling within 0.0001 percentage points. This is the
accepted staged objective, not a claim of a unique global optimum across all ceiling vectors.
Every stage receives the selected time budget and the existing 1% relative-gap policy.
User-facing results retain that qualification without backend implementation names; a feasible incumbent is not proof of
an exact mathematical optimum. No fallback solver or silent relaxation is used.

Exactly one worker occupies each selected position in every productive block. All Jobs
uses unique Job identities; Workplace uses exact placement keys, so different placements
of the same Job remain distinct positions. Because all positions are staffed, the overall
population mean is invariant for a fixed Job set and timing. Optimization redistributes
exposure and can reduce the worst worker's index; it cannot lower that invariant mean.

## Hard restrictions and neighboring runs

The worker form prepares fixed-to-position, excluded-position and no-consecutive-High
rules. Fixed means that exact position in every productive block. High means High in any
selected tool under the existing thresholds (strictly greater than 50%). An unselected tool
cannot change this classification. Breaks do not reset adjacency.

A no-consecutive-High rule can also check the previous run's last block and/or following
run's first block. Each side must be selected explicitly from an actual accepted supported
run. The saved reference freezes that source's identity, exact run signature, local start/end
and per-worker boundary coefficients. It neither infers a recurring Shift nor wraps the
same schedule automatically. Overlap and reversed temporal order are rejected. A gap is
allowed for an explicitly selected neighbor and grants no assumed recovery effect.

Only workers present on both sides form a cross-boundary pair. A matching worker's missing
selected-tool coefficient blocks the check; it is never treated as zero. A requested missing
or stale source is **not checked** and blocks solving. Renaming a source scenario alone
keeps it valid; changing its numerical inputs/run makes the stored boundary stale. Immediate
sources are checked independently; this does not recursively certify their own neighbors or
optimize several rotations jointly. Clearing a link retains its requested rule intention,
so the user must resolve the missing source rather than silently weakening the restriction.

## No observed rotation, preview and application

No means there is no observed baseline. Generate initial proposal runs a real feasibility
model, optionally without risk values if no High rule needs them. Its result is explicitly
not risk-optimized. Step 04 accepts it as the starting proposal after any replacement confirmation;
the observed baseline stays absent
and no optimized run is created. Optimization may also run directly without a generated
proposal when selected-tool Job coefficients are complete. Partial entered matrices remain
savable but must be completed or cleared before optimization.

The solver receives detached immutable input on an owned worker thread. Project reads,
confirmation, result retention and history remain on the GUI thread. Cancel suppresses publication;
it does not terminate native solver work. Closing requests cancellation and waits for the
bounded worker before releasing the window. Every optimization subset may consume two pass budgets; feasible proposal generation
uses one. Historical one-pass single-tool results remain readable with a rerun
suggestion, and new run settings explicitly record secondary balancing.

The matrix tabs display the same returned schedule with each analyzed tool's Job risks and
worker indices; switching tabs does not solve again. Successful optimization remains a preview until **Keep optimization result** (or
**Keep result & compare**) explicitly rechecks session/scenario, inputs, coefficients and
neighboring sources, then retains it as one shared history edit. This never changes the
original baseline. Replacing an existing retained result requires confirmation. Retired,
failed or cancelled results cannot replace current data. Main Save stores a kept result;
Undo/Redo restores the prior run/evidence. Closing with an unkept preview offers Keep,
Discard or Cancel. In step 04, Generate initial proposal runs with a cancellable progress
window, accepts only the requested starting proposal and stays in step 04; replacement
of entered proposal cells requires confirmation. Continuing then visits steps 05 and 06.
Generation is available only in step 04; step 07 only optimizes.
Comparison and advanced rework details are described in
jrot_comparisons.md.

## Storage and recovery

Native24 adds no tables or columns. Guided codec2 stores typed restrictions and frozen
boundaries; model2 identifies the weighted planning contract. Codec1/model1 runs are retained
as historical evidence but are not promoted to current-model results. A native22/23 marker
cannot contain codec2 data. Migration validates that capability before advancing the marker
and preserves every older row and timestamp, including fingerprints and original run bytes.

Use the matching pre-J06 package and retained native23 backup for recovery. Changing the
compatibility marker manually is not a downgrade. Migration experiments use private copies;
the maintained fixtures are publication destinations only after exact-table validation.


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
