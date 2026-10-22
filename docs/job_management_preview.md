> Historical component/checkpoint record. For current operation use [the user guide](user_guide.md), [development](development.md) and [STATUS](STATUS.md). Early pending-feature statements below are historical; M11 inventory records any actual remaining gap.

# Runnable Job Management preview — F68–F70

From the **new project root**, run:

```bash
.venv/bin/python -m ergotools.bootstrap --job-management-demo
```

The command creates `.cache/job-management-demo.ergprj` only when absent and
reopens it on subsequent runs. It contains a synthetic empty assessment and no
jobs/workplace hierarchy initially. Use New job, enter its ID/name and at least
one damage value, then Save changes. Use New version to edit evidence; Approve
saves that evidence and makes it current. This is a persistent demo, not a
read-only mockup. Existing demo files are never overwritten by its creator.
An alternate `--settings PATH` places the demo next to that preferences file.
The default LiFFT preview command remains available without the new option.

A supported new-format project with an assessment can instead be opened with:

```bash
.venv/bin/python -m ergotools.bootstrap --job-management /path/to/new-project.ergprj
```

This entry point requires format seven and an existing assessment because the
current workspace owns an active assessment document. It does not import or
upgrade an original application project. The empty demo can create jobs and
profiles; workplace assignment requires a supported project with a populated
hierarchy. Tests use small synthetic populated projects for that workflow.

## Working controls

The original `JobWindow.setupUI`, evidence tab and date controls supplied the
layout code. Original processed icons and applicable original stylesheet rules
are packaged locally. Window geometry remains 1120x740, minimum 980x720. Modal
execution blocks normal main-window interaction, matching the single-user app.

- Job selection, first/previous/next/last navigation and exact-ID modal search.
- New job and combined job/profile Save, with validation and retry after failure.
- Evidence fields, optional date/sample size and LiFFT/DUET/ST measurements.
- New version, atomic edited approval, Use as current and confirmed retirement.
- Confirmed Delete with assessment-history protection (F69).
- Discard changes and Close with the original no-implicit-save behavior.
- Nested workplace assignment dialog and refreshed placement count. Returning
  from that dialog retains unsaved job/profile text, including on Cancel.

The window calls the application workspace; it contains no SQL or model formulas.
The workspace retains assessment ownership; management actions do not save or
replace assessment edits. Programmatic combo/table loading blocks corresponding
signals, followed by an explicit display update.

## Differences and incomplete work

Delete is now enabled. It removes job-owned profiles/placements and retains
unclassified worker assignments. Jobs referenced by assessment history cannot be
deleted; this preserves the previously implemented history rules and is stronger
than the original behavior. See [deletion details and limits](job_deletion.md).
Rotation-reference checks remain a requirement for the later JROT integration.
English/Spanish form translation is implemented (F70). The preview uses saved
language preferences, or a temporary `--job-language en` / `--job-language es`
override. [Language behavior and validation](job_management_language.md). Remaining work also includes
final main-window navigation, remembering the selected job across window lifetimes,
legacy project import and the comprehensive copied-project acceptance run.

The native combo menu delegate made selected text white on a white background in
the original window on this environment. A standard styled item delegate applies
the existing teal/white selection palette correctly; screenshots show before and
after. Search buttons now use processed search/close icons rather than native
system icons, as required by the UI asset rule. Save success wording is currently
one generic message instead of the original three branch-specific messages.
The earlier measurement/Save differences remain documented in `job_risk_table.md`
and `job_management_save.md`; no scientific formula was changed.

## Verification

Six integrated tests exercise real controls over synthetic SQLite projects:
creation/versioning/approval/currentness/retirement/reopen; validation and write
failure retry; nested modal workplace save with retained form text; navigation,
search, discard and modality; exclusive demo creation; actual launcher cleanup.
The complete suite passes 580 cases with 98.40% statement/branch coverage, plus
Ruff, formatting, strict mypy, architecture checks and wheel/source builds.
An isolated built-wheel workflow creates and approves a job through the real
modal window, then reopens its saved project.

Native XCB inspection covers the original and migrated empty layouts at 1120x740
and 980x720, populated approved/draft measurement and evidence tabs, selection,
expanded profile choices, nested workplace tree, search and validation messages.
Adjacent panels and bottom controls fit at minimum size. There is no VTK region
in Job Management. This is native Linux visual evidence, not Windows/macOS
acceptance. The reference capture extracts the original class for layout only:
its damage handler is stubbed and operational database loading is disabled.
All migration tests/captures use synthetic data; original source and dependencies
remain unchanged. See `f68_validation.json` and `reference/f68-capture.py.txt`.

Overall application completion remains unquantified following withdrawal of the
previous unreliable 67% estimate. This checkpoint delivers a runnable management
workflow; it does not complete the integrated ErgoTools application.

## F71: opening from the assessment preview

Launch `.venv/bin/python -m ergotools.bootstrap`, then Open a **new-format-seven**
project, for example `.cache/job-management-demo.ergprj` created by the separate
demo command above. The header's Job Management button opens the same original-
layout modal. It is disabled without a compatible project, for older project
formats, or while an assessment field has unapplied input. Existing older
projects are not upgraded implicitly.

The modal uses the preview's language and display-unit selection; existing
measurement unit identities remain preserved. Its last stored job selection is
remembered for the same project location during this preview window session.
Missing selections fall back to the first available job. Unsaved new identifiers
are not remembered. This is not persistence across app restarts. The standalone
management launcher still uses the project's default units.

Save/Close retain assessment edits and undo state. Close does not save unsaved
management fields. Returning does not rebuild the assessment editor or clear its
results. Save now loads the selected risk profile once, avoiding the previous
intermediate current-profile render when saving a draft.

Native empty/populated preview states were inspected at 960 × 680 in English and
Spanish; approved measurements and draft evidence were inspected at 980 × 720.
The header button, results and bottom controls fit. No VTK view is present in this
temporary preview. Evidence: `f71_validation.json`; reproduction scripts are in
`docs/reference/f71-capture.py.txt` and `f71-verify.py.txt`.

This is an integration checkpoint for existing forms, not an additional completed
form or a replacement for the original final main-window layout.
