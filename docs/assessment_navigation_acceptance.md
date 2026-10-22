# Owner-approved assessment navigation repair — 2026-10-12

## Scope and reference

Implements the owner's supplied updated-reference behavior after Linux acceptance
identified the mandatory Open picker and worker navigation gaps. This is an explicitly
approved follow-up, not a new migration milestone. Fixed migration/cleanup ledgers and
their denominators remain unchanged. Original checkout, original projects, native test
fixtures, dependency baseline, formulas and native project format 14 are unchanged.

## Functional contract

- Work Setup contains Organization and Jobs and Risk Profiles with existing processed
  icons. Jobs leaves the main toolbar; project/PLOT/JROT/export/settings/help remain.
- Follow worker is the initial mode; remembered **saved** contexts are validated per
  stable project ID, worker ID and tool, then first saved context is used. This matches
  the updated reference's remembered-context eligibility. Keep context preserves the
  workplace during worker navigation. Neither filters workers.
- Open automatically selects available data, preferring LiFFT, then DUET, then ST.
  Projects with workers but no assessments remain browsable without writes.
- Tool switches preserve workplace and retained drafts/undo history. Worker/context/
  project departure resolves all drafts using existing Save/Discard/Cancel. Invalid
  widget text blocks tool switches rather than disappearing.
- Classified picker leaves show Saved/New and exact hierarchy, shift and Job. Choosing
  a context changes only the view. Clean New previews create no database record.
- Status distinguishes Ready, New assessment, No assessment, Select context and Job
  required. Calculator Incomplete/Review required remains visible when applicable.
  Unclassified saved data is readable and cannot be updated until classified. Existing
  closed classified historical editing behavior is retained.
- First Save confirms other saved workplaces for the same worker/tool/Job, listing
  locations. Different Jobs/tools and the same workplace are excluded.

## Architecture and persistence

Application AssessmentNavigation resolves ownership and preference keys; domain values
and scientific models remain unchanged. ProjectWorkspace owns the one active session
plus retained tab sessions, dirty consent and copy preparation. Presentation owns Qt
controls, translated labels, dialogs and the confirmation. SQLite and JSON stay in
infrastructure adapters. Settings version 4 adds context preferences and reads versions
1–3 without discarding language, units, recency, decimals or animation preferences.

First Save inserts a new source, historical owner and its available calculated result
inside one SQLite transaction. Save/Save As include edited retained tabs. Untouched
saved sources/results remain unchanged. Save As prepares edits in the private SQLite
backup before validation/exclusive publication; write failure leaves the source and
nonexistent destination untouched. A complete copy may remain only if final reopen
fails after successful publication. Blank previews and Undo histories are not stored.

## Focused regression catalog

`tests/test_assessment_navigation.py`: automatic Open, all workers with/without saved
active-tool data, Follow/Keep, remembered context across preferences reload, exact
Saved/New picker, localized Work Setup/icons, deferred creation and same-Job warning
accept/cancel, retained multi-tool inputs with Save/Save As, discard and failed first
Save rollback/retry, empty-assessment project navigation. Existing tool/calculation,
legacy-conversion, startup/recency, menu and snapshot tests retain their data and error
checks while replacing obsolete mandatory-picker/rejected-worker expectations.

## Visual acceptance

Twelve final native XCB captures were inspected in
`artifacts/assessment_context_review`: English/Spanish saved, missing, New, expanded
selected picker, Work Setup menu and enlarged main window. Checked at 1548×1040 and
1800×1120 with real VTK. Context group remains below the workspace/above the footer;
mode controls, picker status column, result cards and bottom controls fit. Existing
minimum-width translated task-header/long-footer fit limitations remain recorded from
M5; no unrelated visual repairs were added. Native inspection walks all 28 workers
with DUET selected in both languages and verifies project bytes are unchanged.

Final required gate: **1293 tests passed, zero failures/skips; 96.02% combined statement/branch coverage**. Strict mypy checks 251 source/tool modules. Ruff/format, architecture, naming, both documentation checks and Hatchling wheel/source build pass. The inventory contains 403 reviewed Python/stub files, 2,709 functions, 395 classes and 301 constants; zero structural gaps or pending reviews. Coverage is not a pass-rate percentage. [Machine validation](assessment_navigation_validation.json).

## Substantive documentation review

Reviewed the changed application/presentation/infrastructure bodies, their callers and
regressions against the prior delivered source, not only docstring headings. Contracts
cover retained-session ownership, exact assignment identity, deferred first Save,
transaction rollback, publication timing, settings compatibility and translated
selection behavior. Corrected the optional-icon argument description and first-Save
result argument; documented new private/nested operations and escaping errors. Renewed
certification for exactly the 25 changed/new maintained files; unchanged file/shell
certifications retain their earlier evidence. The generated inventory is refreshed only
after that review; both structural and hash gates remain required.
