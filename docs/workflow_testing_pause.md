# Current bookmark — developer prototype authorized, hands-on tests still paused

The owner authorizes the disposable JROT Yes-path mockup in jrot_prototype.md. This
does not resume or mark passed the production Job or four-worker workflow tests below.
The existing workflow project remains unchanged during prototype work. Resume Job UI
testing from the empty summary rows when the owner is ready. Later discussion answers
are recorded in jrot_wireframe_discussion.md; historical discussion-only restrictions
below are superseded solely for this isolated prototype, not production redesign.

---

# Owner testing bookmark — 2026-10-20

The owner confirms workflow_4_workers.ergprj opens from Recent Projects, and
Workplace → Jobs opens empty with LiFFT/DUET/ST summary rows empty. This is expected:
the workflow project contains no Jobs yet. No direct Job value, calculator input or
worker-copy acceptance has been performed by the owner. Resume Job UI testing here,
one step at a time, then return to the earlier worker/workplace workflow bookmark below.

The owner has returned and asks to discuss the JROT proposal one screen at a time,
starting at physical PDF/PowerPoint page 3 (Line Setup, Screen 1). Both hands-on test
sequences remain paused. The owner rejected the uniform toolbar widths; exact previous
sizing is restored separately. No JROT redesign is authorized. No answers to the Station
versus Job clarification have been supplied yet; record later answers without assuming
team intent.

---

# Maintenance note — 2026-10-20

The authorized Job change updates this same workflow file in place to native format19.
Worker inputs/results, demographics, organization, workplace assignments and Ana's
association stay exact. No interactive workflow step below has been performed or marked
passed. Resume only after the owner reviews the Job change and directs continuation.

---

# Owner-paused four-worker workflow testing

The owner paused interactive workflow testing on 2026-10-19 to discuss a longer Job
Management simplification/calculator task. Resume only when the owner requests it;
this is a testing bookmark, not a new migration milestone.

## Saved project checkpoint

`test_projects/native/workflow_4_workers.ergprj`, metric, native format 18.
Read-only verification after the owner's Save/reopen found twelve assessment sources
and twelve calculated results. All source/result rows exactly match the baseline in
`artifacts/explicit_context_creation/owner_saved_database.json`.

Ana W01's existing LiFFT document `67b7fa81855940969e54eb51df6487dd` is associated
with active assignment 2: Workflow Plant / Packing / Line A / ST01 / Shift 1 / No Job.
Its probability remains 13.190999733969136%, displayed as 13.2%. Assignment 1 is an
older inactive row at the same workplace; only assignment 2 is active. Ana's DUET/ST
and the other workers' assessments remain standalone (eleven standalone owners).
There are no Jobs or Job placements in this workflow project.

## Owner-verified behavior

- Worker Management assignment retention and main Save/reopen.
- Explicit contextual Create assessment: one blank fifteen-task grid.
- Standalone versus workplace navigation retains separate data.
- Existing contextual assessment offers Open, not another Create.
- Undo removes a newly created assessment with warning; recreation works.
- Temporary blank workplace assessment undone before association.
- Associate assessment links Ana's existing LiFFT to ST01 without changing inputs/result;
  the association button disappears once assigned, as intended.
- Main Save/reopen retains the association and 13.2% result.

## Exact next test — proposed but NOT performed

Stay on LiFFT with Follow worker selected. Select Bruno W02: expect his standalone
assessment, 24.2%, without Ana's ST01 context. Select Ana W01 again: expect ST01 / Shift 1
and 13.2%. No input change or Save is needed for that navigation check. The owner paused
before reporting this test, so do not mark it passed.

The subsequent Jobs work must preserve this saved worker assessment checkpoint.
Any owner-approved native format change updates this file and the maintained comparison
fixture in place; test migration on private copies first. Current fixture identity/data
must not be confused with obsolete acceptance hashes from earlier intentional UI saves.
