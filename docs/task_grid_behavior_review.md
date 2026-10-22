# Task-grid behavior audit — 2026-10-18

Historical audit: the owner subsequently approved the bounded implementation.
See [implementation and evidence](task_grid_resize_acceptance.md).

At the time of this audit, the owner requested review before implementation. Independent scope is explicitly
clarified as **per project, per worker, per tool**. The owner expects unused rows to
be ignored, data-preserving growth/shrink, default 15, maximum 100, and exact shared
Undo/Redo restoration. No source, dependency, schema or reference file was changed.
Owner workflow testing pauses here; do not reset/re-enter Ana merely to eliminate
unused rows. Her existing 15-row, one-populated-task case is valid for the intended
workflow and should be retained as an acceptance scenario.

## Findings

| Requirement | Current implementation | Required correction |
|---|---|---|
| Visible unchecked checkbox | Missing outline reproduced in EN/ES | Correct shared checkbox theme, including unchecked/checked/disabled/focus states |
| Independent project/worker/tool count | Stored as each assessment's source-row length; not an application preference | Preserve existing scope; no global count/default infrastructure needed |
| Independent LiFFT/DUET/ST counts | Separate sources and commands | Already supported |
| Default 15, allowed 1–100 | Blank factories use 15; dialog/presenters/commands enforce 1–100 | Preserve |
| Wholly unused rows ignored | Numerical aggregation excludes blank-row damage, but required-field issues mark the result PARTIAL | Exclude unused slots from completeness validation and warnings; keep row positions and real entered data |
| Increase 15 → 20 | Replaces every row with a fresh blank task | Keep original 15 rows/IDs and append 5 default blank rows |
| Decrease 15 → 10 | Replaces every row with a fresh blank task | Keep first 10 rows/IDs; remove only trailing 5 |
| Apply same count | Also replaces every row with blanks | No-op, preserving data/results/history |
| Undo/Redo | Current destructive reset is one reversible action; exact original values/IDs return | Reuse shared history for non-destructive resize, including truncated data/results |
| Settings wording | Describes clearing/reset and confirmation for all changes | Describe changing row count; request consent when populated trailing rows will be removed |

Sources: `preferences_dialog.py` (Assessment page), `theme/dialogs.py` (shared style),
`lifft_window.py` (preferences host and blank factories), three tool presenters and
`application/assessments/{lifft,duet,tst}_commands.py` / `evaluation.py`.
Saved status also drives main result cards and export/recorded-result presentation;
changing unused-row handling must cover those consumers rather than only hide a label.

### Checkbox cause

`DIALOG_STYLE` groups `QDialog QLabel, QDialog QCheckBox, QDialog QRadioButton` under
`background: transparent`. A minimal offscreen Qt comparison with four styles shows:
unstyled checkbox and text-color-only checkbox retain the unchecked box; transparent-
background checkbox and the shared dialog style lose the unchecked outline, retaining
only the checked tick. The actual Settings dialog reproduces the owner's appearance
in both languages. This is style rendering, not an absent/disabled checkbox or data
binding error. Fix the shared indicator/theme rule and inspect other affected controls;
do not add a control-specific cosmetic workaround.

### Count ownership

Count is part of an assessment's stored source, keyed by project/document identity
with worker/tool ownership and optional real assignment. It is not in personal
settings. Selecting another worker/tool uses that source's count; new blank sources
start at 15. Existing assignments retain their separate source ownership. No additional
project-wide shared-count policy was requested after the owner's clarification.

### Blank versus entered rows

Wholly unused slots must not make Ana's one populated task incomplete. Numeric values
including zero are entered data, and default DUET scale/ST direction selectors alone
must not make every unused slot populated. A started row with missing required input
is a different case: retain explicit validation rather than silently invent data or
claim full calculation. An entirely empty assessment must not be presented as a
calculated zero-risk assessment. Numerical formulas/units must remain unchanged.
These boundaries and old saved partial-result presentation need focused regressions.
Do not rewrite Ana's saved result or project during this review.

### Reference comparison (read-only)

The original `src/main.py` has `default_num_task = 15`, the count spinner range 1–100,
and separate `num_task_lift`, `num_task_duet`, `num_task_tst` variables. On load it
restores each count from that worker/context/tool's saved rows (around 6695–6723).
The original `numTasksSetButtonClicked` (1298–1349) removes/rebuilds the active tool
tab and clears its inputs. Thus preserving retained rows is an owner-requested
improvement over that behavior, not something currently implemented incorrectly
relative to the original reset. Original calculations continue through complete rows
and zero/moment-only outputs for missing rows, but also show a generic incomplete-
input warning (LiFFT around 5766–5840). The new persisted PARTIAL classification is
an explicit modern representation, not a reference database status. The owner's
current direction supersedes treating all unused slots as incomplete.

## Actual audit evidence

- 23 focused existing tests pass (`task_count_integration`, `lifft_grid_workflow`,
  `settings_navigation_theme`) under Qt offscreen. They characterize the current
  destructive reset/partial-row policy, not acceptance of the newly requested behavior.
- Nine command/history probes cover three tools × growth/shrink/same-count with 15
  populated tasks. All currently discard the retained prefix; Undo restores exact
  original values/IDs and Redo restores the reset.
- Three grid-calculation probes with one complete + 14 unused rows all return PARTIAL:
  LiFFT/ST 42 required-field issues, DUET 14. This reproduces the semantic gap.
- Four settled full-dialog EN/ES unchecked/checked captures and one style-isolation
  image inspected. The checkbox failure is reproduced. Native XCB startup was blocked
  by automatic approval-review timeout; these are offscreen observations, not native
  acceptance of a repair. The owner's supplied screenshots independently show it.
- No full gate repeated, no new maintained tests/source, no native project writes,
  no original reference modification. Migration/cleanup remain 100%; last accepted
  code gate stays 1,406 tests/94.29%. No new milestone/dependencies/assessment versions.

Evidence: `artifacts/task_grid_behavior_review/` contains logs, probes and captures.

## Owner follow-up before implementation

Owner reaffirms that the old clearing behavior was a limitation and requests that
Settings clearly identify whose task count is being changed. Show the active worker,
tool and standalone/workplace context (including Job when present), not only LiFFT/
DUET/ST. Implementation remains paused while assessment ownership is clarified.
Current native16 contract remains one standalone assessment per worker/tool and one
per real assignment/tool; assignment includes station/shift with an optional Job.
Explicit association moves the same standalone document to its assignment without
copying it or changing other tools. Another assignment may own a separate assessment;
ordinary navigation does not duplicate or relocate one. Row counts remain independent
for each assessment. No alternate assessment/version feature is requested.

## Proposed bounded implementation

Correct shared checkbox styling; change existing three count commands/presenters to
preserve retained rows and pending valid inputs; validate wholly empty versus started
rows consistently across all tools; update EN/ES labels/consent/status/export behavior
and substantive code documentation. Preserve source IDs and the existing shared history,
main Save boundary, metric/imperial conventions and each assessment's independent count.
Tests must include lossless expansion, shrinking past populated rows, same-count no-op,
Undo/Redo restoring removed inputs and matching results, cancellation/invalid pending
text, Save/reopen, independent workers/tools and the actual one-of-15 owner scenario.
Review changed UI states in EN/ES and run the required code-slice gate after changes.
Implementation has not started under this audit request.
