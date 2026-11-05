# Three-worker guided JROT walkthrough

This walkthrough describes the three-worker example in
`test_projects/native/jrot_workflow_optimization_test01.ergprj`. Work on a private
copy when changing its inputs or saved rotations.

## Prepared data and remaining input

Existing workers, worker assessments/results, J01 direct results and J02 LiFFT
source/results are retained. ST03 is added to Workflow Plant → Packing → Line A.
J01 Manual packing, J02 Box loading and J03 Pallet transfer have placements at
ST01/ST02/ST03 in Shift 1. Ana, Bruno and Carla have workplace assignments on that
Line; Diego remains available through All project workers. Assignment to a workplace
is distinct from a participating rotation row or a permanent Job classification.

J02's missing DUET/ST inputs and J03's tools are prepared with real calculator
sources. J03 LiFFT deliberately needs **800 repetitions**; its lever arm is 70 cm
and load 196.2 N. No saved rotation or optimized result is added to the example file.
Use the prepared test rotations for independently checked optimizer examples.

| Job | LiFFT | DUET | ST |
|---|---:|---:|---:|
| J01 Manual packing | 13.191% | 45.700% | 41.500% |
| J02 Box loading | 13.191% | 16.823% | 39.213% |
| J03 Pallet transfer, after entering 800 | 73.744% | 52.918% | 72.340% |

These are current Job values, with established formulas and units unchanged. J01
intentionally demonstrates direct results; J02/J03 demonstrate task-based values.

## Guided test sequence

1. Load the project, open JROT. The **Saved rotation** combo selects an existing
   record; the uncreated entry is explicitly identified as such. In step 01, set
   **Rotation name** to `Packing trial`, planned date 2 November 2026, then Create.
   This name belongs to the same record selected at the top; it is not a second ID.
2. Choose Workflow Plant → Packing → Line A, Shift 1; enable Job placements in
   this Line/Shift. Copy Shift timing and edit the independent rotation timing to
   three equal blocks, 08:00–16:00, no breaks. Each block is 160 minutes. Choose Yes
   to enter a baseline. No constraints are needed for the initial test.
3. In step 02 select the three Job positions. Check search, available name initials,
   complete identifiers, ancestry and bounded colored result columns. Cancel first
   if desired, reopen, then accept. Selection itself does not copy risks or create Jobs.
4. In step 03 inspect the selected-Line worker view (Ana, Bruno, Carla), switch to
   All project workers to see Diego, then restore the Line view and select the first
   three. Test surname initials and search. Hidden checks are counted and retained;
   All visible/None affect only visible records. Create/edit workers opens the same
   shared worker-management window used by the Main UI.
5. In step 04 enter Ana → J01 in all three blocks; Bruno → J02 in all three; Carla →
   J03 in all three. This is **nine assignment cells using three Jobs**, one worker
   per Job in every block. Full Block headings replace B1/B2/B3.
6. In step 05 choose J03 → LiFFT and enter 800 repetitions. The existing inputs
   calculate automatically; Calculate remains available. Review the other tools.
   Test Undo/Redo for this edit. Completing a Job updates its step 02 summary too.
7. Review step 06's Job values and baseline worker indices. Start with LiFFT only,
   optimize in step 07, inspect and Apply the preview. The actual backend is CBC.
   Repeat with all three tools to exercise the real two-stage HiGHS route.
8. Review step 08; close JROT, use Main Save, close/reopen the project and return
   to the saved rotation. Verify the top selection and editable name refer to it.

For this equal-block, unconstrained setup a complete cycle gives every worker each
Job once. The independently checked worker-index lower bounds are **33.3754 LiFFT**,
**38.4803 DUET** and **51.0177 ST**. Equivalent row/block permutations are valid.
The maximum exposure decreases while the population mean stays fixed; workers
previously assigned only a low-risk Job need not individually improve. These are
schedule comparison indices, not individual injury probabilities.

## Shared input selection

In Main, Jobs and guided JROT, click an input cell and Shift-click another to select
a rectangle of visible editable fields. The aqua highlight and Copy N cells caption
show the range. Copy cells or Ctrl+C copies that range as full-precision quoted TSV
with matching headers. Escape or an ordinary input click clears it. With no range,
Copy cells retains its existing full-input export; native single-field text copy and
text Undo remain native. Calculated output columns are not included in the rectangle.

The Task names button retains its quick Add/Rename menu, now separated from tool
labels by 8px in normal editors. The full catalog manager remains under Workplace →
Task names. Task-name management behavior was a question, not an instruction to replace it.

## Presentation and pending work

Split/Remove cursors shrink from 36px to 31px (approximately 15%); Join remains distinct.
Rotation replaces Your rotation on the sidebar. Guided tables use bold, taller headings,
36px row minima (multi-line result rows gain 15%), and content-aware columns. A tree
delegate increases height without overriding required identifier/icon/checkbox width.
Risk colors use exact coefficients rather than rounded displayed percentages.

Pending at owner request: live Settings previews for gauge markers/range labels and
other appearance options where useful. Recorded in review_register.md; no Settings
redesign or additional database/preference field is included here.
