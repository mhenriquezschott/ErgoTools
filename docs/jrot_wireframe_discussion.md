# JROT wireframe discussion — owner clarifications, 2026-10-20

Discussion and requirements only. No JROT redesign, database/configuration change,
restriction enforcement or solver extension is authorized for implementation here.
The owner requests following the first-page numbered workflow one section at a time,
initially following the Yes / existing-rotation branch. This record distinguishes owner
choices from assumptions and questions still requiring the JROT team. The original
review and sixteen-question document remain historical analysis, not sixteen unanswered
blocking questions or an approved development plan.

## Owner interpretations and intended reuse

- Project corresponds to our .ergprj container. Retain Plant/Section/Line hierarchy
  rather than limit a project to one line. A simple company can define one real branch;
  no artificial defaults are implied.
- Existing Shift start/end fields can supply elapsed duration. Team question remains:
  should the analyzed duration be the full start/end interval or exclude breaks?
- Current blocks are ordered/equally weighted, without stored durations. The walkthrough
  assumes equal blocks over the shift. Unequal durations are shown in the proposal;
  their eventual requirement and exposure model have not been resolved by this assumption.
- Worker count refers to participants in this rotation, reusing existing Worker records.
- Owner recalls the team using workstation and Job interchangeably. Provisionally read
  their workstation as our Job, while proposing they retain our separate physical
  Station and Job concepts. This terminology still needs team confirmation. Both current
  All Jobs and workplace-scoped analysis should remain available.
- Task entry during guided matrix setup should reuse the same Job values/calculators.
  Job Management remains available for prior data and subsequent edits; no separate
  wizard assessments or duplicated risk store. Existing usable values should be reused.
- Task Name is new source metadata with main-UI/copy/persistence implications. Owner
  will ask whether task numbers suffice or an optional name is essential; not decided.
- Baseline summary question remains: show intrinsic Job values, worker full-schedule
  averages, or both? These are distinct quantities under the existing calculation.
- Owner confirms comparison mockup numbers are placeholders. They are not expected
  calculator results or a requirement to reduce the population mean. The interpretation
  of any new report measure remains to be specified.
- Report question remains: required content/formats, and whether compliance refers to a
  specific standard/criteria or simply a rotation-analysis summary.

## Owner-defined initial behavior

### Selected tools

Allow optimizing any nonempty subset of LiFFT, DUET and ST: one tool, any of the three
pairs, or all three. Existing implementation supports single-tool and all-tool routes;
any-pair optimization is an extension, not existing functionality. The objective/backend
for that extension still needs a concrete design; no new dependencies are approved.
Missing/unselected tool data must not become zero risk.

### Operational restrictions

Support both fixing a worker to a single Job and excluding one or more Jobs for a
worker. Also prevent two high-risk Jobs back to back. These are proposed new solver
constraints; none are implemented by this discussion. Use existing high-risk
classifications initially. The owner's reply accepts the proposed interpretation of a
Job as high risk if any tool selected for the optimization classifies it as high risk.
Do not reinterpret percentages or change existing scientific calculations.

The owner wants currently code-defined risk thresholds to become configurable through
a suitable persistent mechanism later. Database versus application preference, scope,
validation, scientific interpretation and effects on existing views/reports remain later
design decisions. This does not authorize a table, schema change or implementation now.

### Staffing

Initially require exactly one worker per participating Job in each block. Avoid parallel
staffing/vacancies for this first scope. Under one Job per participating worker per block,
participant and Job counts must match; this implication has been explained. Existing
solver capacity is at most one per target/block, not a new implemented exactly-one rule.
Current target multiplicities remain a separate constraint to assess during future design.

## Provisional boundary and question to send

The owner's initial preference is to apply the no-consecutive-high-risk-Job rule only
within the analyzed shift. This is **provisional**, and the owner explicitly requests
asking the team:

> Should the restriction against consecutive high-risk Jobs apply only within a shift,
> or also between the last block of one shift and the first block of the next?

Across-shift enforcement would require explicit worker continuity and prior/next
schedule context that the current single-scheme solve does not receive. Do not infer
such relationships from recurring Shift clock definitions or silently enforce a wrap
from the last block to the first block of the same scheme.

## Current state

Toolbar widths were restored exactly at the owner's request and verified separately.
Hands-on Job UI and earlier worker/workplace workflow tests remain paused. Resume the
requirements discussion at the current first-page workflow point; no full-flow lecture,
new milestones or development implementation follows from this record.
