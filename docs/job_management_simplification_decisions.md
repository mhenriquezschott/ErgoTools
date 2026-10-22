# Job Management simplification — owner decisions, 2026-10-20

Interactive worker/workplace workflow tests remain paused at the exact bookmark in
workflow_testing_pause.md. This is owner-requested follow-up, not a new migration
milestone. Linux migration/cleanup remains complete; original-reference, dependency,
architecture, documentation, localization, units and validation protections continue.

## Approved contract

- Remove Job risk-profile versions, evidence fields, approval/current/retirement
  workflow and their obsolete database storage. One authoritative risk set per Job,
  containing independent LiFFT/DUET/ST measurements.
- Retain direct cumulative-damage entry and existing damage-to-probability behavior.
- Compact calculators live inside Job Management, without the avatar/full main UI or
  another nested calculator window. Initial blank grid has one task; add/remove tasks
  as needed, up to 100. Calculate and Clear use the established scientific behavior.
- Calculator inputs persist per Job/tool across main Save/reopen. No alternate input
  versions or risk profiles. Shared project Undo/Redo covers accepted edits, task count,
  removed inputs, calculation, clearing and copied worker data. Main Save publishes.
- Saved JROT schedules use the Job's updated risk values. Their worker/Job arrangements
  remain intact; risk evaluation updates and optimization requires explicit rerun.
  No hidden retained old Job profiles or numerical risk snapshots substitute for the
  rejected multiple-profile model. Adapt JROT references, eligibility, evaluation,
  comparisons, history, persistence and conversion as required by this contract.
- Migration retains each Job's currently selected measurements and removes older
  profile/evidence data. Preserve worker assessment inputs/results, hierarchy, images,
  assignments, placements and schedule arrangements. Validate staged private copies
  before migrating the existing native fixture paths in place; do not add duplicate
  maintained projects or automatic backup files. Keep the maintained integrated
  fixture compatible alongside the workflow and comparison files.
- Job Management also offers an explicit selection of a worker assessment of the
  selected tool, standalone or workplace-assigned, to copy its values. This never
  associates the worker assessment with the Job, changes ownership or establishes a
  live dependency. Subsequent worker and Job edits must remain independent.

## Final owner authorization — 2026-10-20

Owner confirms copying exact task inputs AND their matching calculated values into the
Job, retaining those tasks on main Save/reopen. Mini-calculator inputs likewise persist.
Owner confirms ErgoTools is saved and closed and explicitly authorizes complete work,
in-place migration and necessary PLOT/JROT adaptations. Resolve later routine questions
using judgment, recording choices for review rather than stopping. Worker workflow tests
remain paused. No dependencies, formulas or original-reference changes are authorized.

## Rollback record

One explicitly documented task recovery archive exists at
artifacts/job_simplification/pre_change_rollback.tar.gz. baseline_files.json records its
exact source/doc/native-fixture hashes. It excludes reference checkout/environment and
runtime assets. This is a finite task rollback point, not application backup behavior or
a second maintained fixture set. Retain through migration acceptance; list its deletion
at final handoff after tests. No automatic backup files will be added to test_projects.

## Implementation decisions for later owner review

- Retain every per-task calculator moment/damage/contribution alongside exact task
  inputs and aggregate values. This fulfills the approved input-and-calculated-value
  copy contract; display rounding never changes stored numbers. Edited tasks clear all
  stale outputs until Calculate, and blank extra rows follow the existing evaluator.
- Native format 19 stores current Job/tool rows only. Existing format-18 files convert
  externally; versions 14-18 keep worker source/result payloads exactly. No runtime
  old-profile decoder or new business table is introduced.
- Keep inactive historical worker/placement links in saved rotations. Resolve current
  Job numbers at display, preparation and main Save, including a JROT draft whose window
  is closed. Numeric changes invalidate optimization provenance while preserving cells;
  no automatic optimization occurs. Unrelated Job changes do not invalidate an optimum.
- Update surviving Job parent rows in place during catalog replacement. Deleting and
  reinserting parent Jobs would cascade-delete current risks; regression tests explicitly
  protect risk values and task sources during placement/assignment changes.
- Keep direct input and independent calculators as explicit methods. Removing retained
  tasks, clearing populated tools and replacing copied data require consent; cancellation
  preserves the prior source. All accepted changes use the existing shared project
  history and sole main Save.
- Compact output cells use project decimal conventions and retain exact values underneath.
  The Job window keeps all three summary rows visible and uses ordinary scrollbars for
  task overflow. No plant-image scrollbar or unrelated workflow redesign is added.

Implementation and Linux verification are complete; see job_management_simplification_acceptance.md. No user acceptance or unperformed workflow step is marked
passed. The rollback archive is retained through final verification and listed for cleanup
once the owner accepts the change.

- Task-output storage includes the canonical source digest. Corrupt same-sized input
  changes cannot reopen with stale calculated rows. This is a codec/binding marker, not
  assessment versioning or an additional stored input/result history. Fractional
  repetitions retain the original models' float semantics; copied rounded displays
  never truncate their exact inputs.

- A Job ID is required before risk entry is enabled. Clearing it cannot silently discard
  entered task data; acceptance asks for correction. Existing inactive Job flags survive
  risk/metadata edits. Expanded calculators reserve room for every summary/bottom control;
  collapsing restores the previous compact window height. Complete task headers/choices
  determine column minima, and spare width is distributed before scrolling is needed.
- Editable direct damage displays exact input precision. Read-only calculated summaries
  and JROT captions are compact; matching source/output data remain exact underneath.
  Missing or stale calculations cannot be copied or used as current solver coefficients.

- Worker-copy rows show optional Job ID/name with workplace context. Context tooltips identify the exact source assessment and active/previous assignment. This is source selection information, not Job profile/evidence storage or a live dependency.

- Native source inventory: workflow_4_workers has four complete worker results for each tool. The two comprehensive fixtures each have 103 complete LiFFT results; their existing DUET/ST worker results are marked partial. These statuses and payloads remain exact. Such rows stay visible but require Calculate before copying; no result is silently recomputed or promoted during migration.
