# Development

ErgoTools uses Python 3.13.14 and a modular desktop architecture. See
[architecture](architecture.md), [coding standards](coding_standards.md),
[API contracts](api_contracts.md) and the [database reference](database_tables.md).

## Environment

Install Git and uv following the [installation guide](installation.md), then run:

```bash
uv python install 3.13.14
uv sync --locked --extra desktop --python 3.13.14
bash tools/run.sh
```

On Linux, `tools/run.sh` defaults to Qt XCB and removes `XDG_SESSION_TYPE` from
the launched process when using XCB. You do not need to prefix the command with
`env -u XDG_SESSION_TYPE QT_QPA_PLATFORM=xcb`. An explicitly configured
`QT_QPA_PLATFORM` is respected; other operating systems keep their native defaults.

The development environment includes Ruff, mypy, pytest, coverage and Hatchling.
`uv.lock` records exact dependencies so installations can be reproduced. Keep it
under version control; update dependencies deliberately and review compatibility.
Windows and macOS setup is described separately in the installation guide.

## Verification

```bash
bash tools/check.sh
```

The check script runs formatting/lint, strict types, architecture and naming checks,
documentation structure and substantive-review checks, tests with coverage, and
wheel/source builds. Documentation review metadata is maintained in
`cleanup_documentation_inventory.json` and `cleanup_documentation_reviews.json`;
these are verification inputs, not application data.

Review changed file and function contracts before updating review hashes. Refreshing
the inventory does not certify a substantive review. UI changes also require visual
inspection, including the VTK avatar and populated, empty and resized states.
Use private copies of example projects for checks that modify data.

## Packaging

```bash
.venv/bin/python -m hatchling build
```

Builds produce a wheel and source archive in `dist/`. The wheel includes the
application and its resources; the external legacy-project conversion utility
remains separate under `tools/project_migration/`.

Keep domain and application code independent of Qt, SQL, solvers and rendering.
Adapters implement those integrations. Preserve scientific calculations, units,
localization and project integrity when changing interfaces.

## Shared assessment presentation

Use [AssessmentTaskGrid and AssessmentEditorSection](shared_assessment_editor.md) for
new ergonomic task editors. Main, Jobs and compact copy previews share these controls.
Keep host source acceptance, unit conversion, validation, calculation, history and
saving outside the grid; do not add another per-window row/header implementation.
Guided JROT also composes this shared editor; do not restore the retired scratch calculator.


## Documentation map

[The documentation index](README.md) distinguishes current operating/API guides from
historical component records. Public guides must not link to personal checkpoint notes
or ignored local evidence. Retired widgets/modules must be identified as removed rather
than documented as active interfaces. Screenshot projects are private copies with fictional
records; do not modify maintained fixtures to prepare README images.


Current integrated projects use native24. Reusable task metadata and clipboard services
are described in shared_assessment_editor.md and database_tables.md. When extending the
grid, keep name widgets separate from numeric input indices, validate references through
the project adapter, and exercise focused-cell Save plus repeated Undo/Redo. Conversion
remains external; never test migrations on the maintained/operational original file.


For timing UI, reuse RotationTiming/ShiftClock and RotationTimeline rather than duplicating
minute/overnight/break math in a wizard. The Shift editor is available in Organization;
guided JROT copies timing templates into independent rotation timing. Keep complete projection
and pending invalid-input handling separate. Test coalesced mouse release, Escape, real
Enter and still-focused closing, plus template references in every hierarchy write path.

For scenario lifecycle, reuse RotationScenarioRepository and the pure rotation_scenarios
helpers. Preserve None baselines, partial entered cells, exact expected states and separate
run context. Never implement another save/history stack or rewrite permanent assignments
when selecting/applying a plan. Compatibility-only presentation is isolated in legacy_jrot_*
modules; shared application/domain/solver/storage names remain neutral.

Normal JROT opens guided real-data entry. Optional session-only Legacy and Developer menu
visibility are independent; neither is required for production. The scratch runtime has
been removed. Reuse neutral drawer/scope selectors and the shared Job assessment editor;
never create sample/project data as a side effect of opening a window.
Read jrot_guided_entry.md. Native23 protects empty Yes-path observation intent; retain the
pre-upgrade native22 files with their matching packages when testing recovery.

## Guided JROT planning checks

Read jrot_planning.md for model2, typed restrictions and the native24 capability boundary.
Use independent rational examples alongside actual HiGHS output; solver status alone
is insufficient acceptance evidence. Native worker cancellation is cooperative publication
cancellation, with bounded ownership retained until the stage finishes. Exercise preview,
explicit Keep, shared replay, stale Job/neighbor evidence and real Main Save on private copies.
Legacy omits guided rows and the storage guard rejects stale identity collisions. Exercise
both menus and settings without a project, compatible old schemes, and mixed guided/old
projects; saving through Legacy must retain exact guided evidence.

## Guided comparison boundary

See jrot_comparisons.md. Pure rotation_comparison projects frozen run distributions and
same-context deltas; it has no live catalog or solver dependency. JrotResultTable is shared
by preview, saved and compact comparison matrices. JrotComparisonPanel projects exact
saved or valid preview evidence, retaining stale/unsupported status. Rework uses existing
scenario lifecycle/history ports; no schema/codec or alternate Job profile is introduced.
Main Save remains the only project publisher. Normal/Legacy promotion remains J08.


## Spreadsheet integration

Use the shared [import/paste panel](assessment_import.md), not per-window parsers or
spreadsheet widgets. The adapter is pinned to openpyxl 3.1.5 / et-xmlfile 2.0.0. The
application core consumes detached strings through a reader port; it imports no Excel
library. Read-only workbook access does not evaluate formulas. Stage edits and Settings
samples never accept a project source. Keep per-tool personal profiles separate from
project history and use host acceptance for one atomic imported rectangle.


Optional task columns must use the central semantic schema and the shared grid. Never
hide a required input or clear its source value to achieve presentation changes. Timing
visual tools must propose complete immutable models against a frozen gesture origin;
accept only once on release through the existing Shift/scenario history port. Retain
manual pending-input guards and generation checks when adding clock/duration controls.

Timing editor proposals must have one interval per work block. Keep older stored timings readable; opening a separated preview must not persist it. Do not join work across a break or silently relocate pauses. Equalization requires confirmation and keeps duration/name metadata. Use the shared measured tool tab bar rather than per-window hard-coded widths. Task names use the existing catalog/history ports, not a second data model.

## Uniform segment editor update — 2026-11-01

The current editor uses application.rotation_segments for both work and pauses. Removal extends immediate neighbors (sole neighbor at an edge, half to each inside). It may extend breaks; the host confirms reduced work time. Move applies to both types with local translation or whole-segment reordering; all interior boundaries resize neighbors. Coordinated equal/count edits preserve type totals and honor both equality choices; Equal breaks shares the existing pause budget. Positive-budget impossibilities reject without implicit deletion or extra work blocks. Break equality is inferred from saved durations, not a new stored field. Both tables have matching controls and keep full shift coverage. This supersedes earlier editor statements requiring removal of a break before removing adjacent work; explicit Join still preserves intervening intervals. Existing expected-state/scenario consent/history and native24 remain unchanged.

## Visual preferences and display reports

See [Settings previews and diagnostics](settings_previews_and_diagnostics.md) for the
reused gauge/bar controls, packaged avatar recording, launch flags, per-OS report
locations and read-only DPI observation. Reporting defaults on for Windows/macOS
and off for Linux; it never changes the platform scaling policy or project format.
