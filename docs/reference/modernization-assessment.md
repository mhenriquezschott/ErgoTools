# ErgoTools modernization assessment evidence

Recorded 2026-09-27. Retained from the first assessment; test results below were not rerun during the documentation revision. The current integrated code is the behavioral reference. The old PDF manual is historical supporting material only.

The governing proposal is [modernization-plan.md](modernization-plan.md). This evidence document preserves findings, numerical observations, test limitations and the dependency matrix; it does not prescribe copying legacy code into the new application. The numbered headings retain their original evidence identifiers.

## 2. Repository and environment inventory

Reference: branch `ergotools-plot-new-ui`, HEAD `1aeb2d056ea4d9dd60dbe2ea127389c7d858e4a9` (`Document JROT rotation scopes`), one worktree. Local `main`, `plot`, backup branches, and remote-tracking branches exist. No fetch/push was performed; synchronization with the remote is unverified.

Initial Git status had 14 modified tracked paths: README/docs, eight bytecode files, `src/index.html`, the comparative database, and two tests. Numerous fixtures, backups, design sources, bytecode files, and archives are untracked. Twenty-six `.pyc` files are tracked. **HEAD alone does not capture the working reference.** Do not clean, reset, stash, or blanket-stage this checkout.

Inventory: 498 non-Git files, including 62 Python files, 161 bytecode files, 209 PNGs, 13 Markdown files, five SQLite databases, eight database backups, four project descriptors, eight STL models, three PDFs, three HTML files, and UI/translation/SVG/XCF/DWG/XLSX/ZIP/JSON/text/launcher assets. The original assessment generated a complete hash manifest and definition-level inventory; these temporary audit artifacts are not prerequisites for reading this durable document. A complete module/line-count index is retained below.

| Area | Existing implementation |
|---|---|
| Main application | `src/main.py`, 9,425 lines: bootstrap, project operations, UI state, calculation orchestration, SQL, CSV, translation, VTK. |
| Calculators | `pyLiFFT.py` (373), `pyDUET.py` (116), `pyTST.py` (134): arithmetic plus color generation and historical data/comments. |
| PLOT | `plant_layout.py` (7,968), `visualworkertool.py`, `visualjobmarker.py`, `plot_position_repository.py`, `plotviewerdialog.py`, `multiselectcombobox.py`, `zcpwindow.py`; Qt graphics and Matplotlib. |
| JROT | `rotation_layout.py` (3,644), optimizer/repository/schema/scope modules, and three comparison/result windows. Active optimization already accepts plain data. |
| Persistence | `database.py`, `database_inventory.py`, `schema_migrations.py`, `jrot_database.py`, Job risk and placement repositories. Current schema v8. |
| Management | `worker_window.py` (2,903), `job_window.py` (1,448), `organization_window.py`, and individual hierarchy windows. Worker management also contains anthropometry features; preserve their status explicitly. |
| Transfer | Main imports `worker_transfer_window.py`; `tooltransferdialog.py` is active. Older `workertransferdialog.py` remains. |
| Tests/scripts | Fourteen test files mixing unittest, direct test functions, and top-level scripts. Three scripts inventory, fuse, and generate project fixtures. |
| Documentation | README, ten docs Markdown files, screenshots, 25-page case manual, LiFFT help PDF, historical plans and functional/database references. |
| Runtime assets | 61 processed icons in `assets/ui-icons`, old images, eight anatomical models. Preserve designer originals separately from runtime assets. |
| Legacy/experiments | `src/updatecode` contains 12,159 lines of alternate main/PLOT code; ZIP, `testmultiop.py`, solver logs, old method variants, generated UI and D3 experiment remain. Establish reachability before removal. |
| Build/configuration | Seven exact requirement pins; no root pyproject/setup, CI workflow, lockfile, packaging specification, or root `.gitignore` found. `run_ergotools.batz` uses WindowsApps Python. QSettings currently persists camera animation. |

Installed reference interpreter: `/home/mhenriquez/anaconda3/envs/ergotools/bin/python`, **3.10.18**. All seven pins match: VTK 9.5.0, PyQt5 5.15.11, PyQtWebEngine 5.15.7, pycountry 24.6.1, PuLP 3.2.2, Pyomo 6.9.3, highspy 1.11.0. Also installed: NumPy 2.2.6, Matplotlib 3.10.5, Pillow 11.3.0, PyQt5-Qt5 5.15.17. Pytest is absent. NumPy/Matplotlib are direct imports but unpinned; transitive Qt/SIP/solver components also need recording. Python 3.12/3.13 bytecode is not compatibility evidence.

## 3. Current architecture and data flows

```text
.ergprj XML -> main.openFilePath -> resolve DB -> migrations -> Qt project/context state

LiFFT / DUET / ST form -> task calculator -> main aggregates/formats
                                        -> labels, gauge, VTK
                                        -> legacy header/tasks on Save

Worker / organization / Job dialogs -> direct SQL and repositories
Job profile lifecycle + Job placement + Worker assignment -> workplace/provenance

PLOT -> normalized assessments + assignments + workplace contexts
     -> current approved Job profiles + placements + physical map positions
     -> applied filters -> individual / job / comparison datasets
     -> markers, charts, summaries, highlights, exports

JROT -> All Jobs or Workplace pool -> frozen profile targets -> schedule snapshot
     -> PuLP/HiGHS worker -> compare / Use as Current -> explicit scheme Save
```

Assessment identity includes worker, plant, section, line, station, shift, and tool. Main resolves selected assignments/context at `4714` onward, reads legacy headers/tasks in `_loadToolsData` (`6318`), and invokes three separate legacy saves at `6957`. Migrations 4/5 imported normalized records once; v8 reopening does not continuously re-import later legacy changes. Transfer/delete/export consumers also require coordinated cutover.

Job risk differs from individual measured exposure. Profiles preserve version, lifecycle, source/evidence, methodology, sample size/date, and tool measurements. PLOT uses current approved profiles; saved JROT targets freeze specific profile versions. Do not turn either into a generic query that erases this distinction.

JROT All Jobs is organization-neutral. Workplace scope uses active station/shift placements and worker assignments; the same Job in two placements is two targets. Current optimization uses mean probability across equal-count blocks, not time-weighted cumulative physiological damage. Single-tool minimizes the largest worker mean; all-tools minimizes the sum of tool ceilings, then ceiling-minus-floor spread with first-stage ceilings constrained within `1e-4`. Target occurrence totals, one target per worker/block, and at most one worker per target/block are preserved. Travel, training, rest, unequal duration, and production constraints are not modeled; adding them changes the product/model.

PLOT Individual counts enabled assessment results, potentially multiple per person. Job view counts placements. Comparison's applicable-job average is weighted through matching individual records, not necessarily distinct Jobs. Charts use NumPy population standard deviation; age often uses current year minus birth year. Missing, zero, disabled, and invisible are different states. Physical worker markers belong to assignments; station anchors are shared across tools/shifts. These semantics need explicit regression contracts.

## 4. Numerical contracts and scientific decisions

| Model | Current arithmetic | Required characterization |
|---|---|---|
| LiFFT | Metric arm /2.54 and N load /4.45. Imperial moment rounded to 0.1 before integer lookup; lookup saturates at 200 ft·lb. Task damage rounded to 4 decimals. Logistic argument `1.7229 + 1.0239*log10(D)`. | Lookup boundaries, saturation, invalid/zero/negative input, fractional repetition, rounding-before-summing, unit equivalence. |
| DUET | Eleven OMNI ratings index fixed per-cycle damage. Task damage rounded to 5 decimals. Logistic argument `0.573 + 0.747*log10(D)`. | All ratings, low values rounded to zero, invalid indices, accumulation. |
| Shoulder | Direction-specific load/arm moments, breakpoints 1.715 and 27 inches; UTS 681; fatigue exponent `(101.25-100*(moment*12/681))/14.83`. Damage rounded to 5 decimals. Logistic argument `0.864 + 0.928*log10(D)`. | Every direction including UI index remapping 1↔2, breakpoint neighbors, UTS assumption, extremes and invalid direction. |

Sources: model modules and main calculation methods `5561`, `5762`, `5958`. Main sums rounded task values, rounds probability percentage to one decimal, and displays `< 5` / `> 90`. Saves map these strings to 0 / 100. Preserve raw numerical, displayed, stored, and exported representations separately during extraction.

**Observed unit discrepancy:** LiFFT `(12 in, 10 lb, 1000 repetitions)` returns moment 10.0; equivalent `(30.48 cm, 44.5 N, 1000)` returns 133.0, with identical damage 0.0027. LiFFT and Shoulder multiply converted metric moment by an additional 9.81 after dividing by 0.73756. That multiplier conflicts with the source's ft·lb-to-N·m intent; damage is calculated before this display conversion. Obtain scientific confirmation and approve any correction, including treatment of historical saved moments/exports. Do not silently correct it in a refactor.

Probability methods require positive damage via logarithm; callers handle zero separately. Model APIs lack consistent invalid-input validation, even where UI validators restrict entry. Preserve known behavior first, then specify validation changes. Continuous tool colors differ intentionally from categorical gauge bands: 25% is Low, 37.5% Moderate, 50% Moderate High, and high risk is strictly above 50% (`risk_ranges.py`).

Worker anthropometry methods (`worker_window.py:2100,2342,2648`) include additional formulas, one described as a simplified example. Establish their scientific status and reachability; they are not automatically disposable because the principal request names five tools.

## 5. Findings and priorities

P0: baseline/integrity gate. P1: early migration. P2: subsequent structural/product work. These priorities do not authorize modifications now.

| ID | Priority / evidence | Finding and response |
|---|---|---|
| F01 | P0, source + observed | **Legacy/normalized divergence.** Main saves legacy tables; `plot_position_repository.py:59` reads normalized assessments. No synchronization triggers exist. Integrated fixture has 194 legacy headers versus 191 normalized assessments. A navigation-test context has a legacy header and 15 tasks but no normalized assessment. Reconcile explicitly without overwriting historical evidence. |
| F02 | P0, source | **Non-atomic assessment replacement.** Main LiFFT save commits task deletion, header deletion, header insertion, then task insertion separately (`7053–7151`); DUET/ST are similar. Failure can leave partial/lost data. Introduce transaction-level tests and one transaction per approved operation. |
| F03 | P0, observed | **Navigation fixture contradicts its test.** `test_worker_navigation_context.py:87` expects an absent result that is present in the legacy fixture. This establishes fixture expectation drift, not by itself a navigation algorithm defect. Preserve and fix the test setup deliberately in the future branch. |
| F04 | P1, observed/source | **Scientific representation discrepancies.** Metric moment and probability persistence need explicit decisions; see section 4. |
| F05 | P1, source | **Fragmented Save model.** Initial Save copies template/writes XML without saving form data; later Save calls only `saveToolsData`. Save As copies disk state with its pre-save call commented out. Subsequent Save does not rewrite language/unit descriptor values. |
| F06 | P1, source/risk | **Project operations lack a single commit point.** Save As updates in-memory paths before XML succeeds, copies multiple files, and does not rewrite stored Plant image paths to the renamed folder. Open changes session fields before full success. Test failure/cancel, portability, image lookup and restoration. |
| F07 | P1, source | **Presentation owns too much.** Main/PLOT total 17,393 lines. Parent objects, hidden controls, labels, dicts, and signal blocking carry state. Extract real workflow seams while preserving signal order/context. |
| F08 | P1, source/risk | **Migration safety has limits.** Backups, rollback, FK checks and version checks are good foundations. Checksum hashes descriptive metadata, not migration code (`schema_migrations.py:33`). File-copy backup has no cross-process ownership lock. No-pending-migration return skips full integrity validation. Freeze v1–v8 and add schema/behavior/concurrency tests. |
| F09 | P1, source | **Incomplete reproducibility.** Direct NumPy/Matplotlib imports are unpinned; generated bytecode is tracked; no automated release pipeline found. Record the existing full environment before approval of constraint changes. |
| F10 | P1, source/native pending | **Working-directory/platform dependencies.** Models use `../models/` (`main.py:9091`); old icon paths use `../images/`. README launches from root, developer guide from src. Windows launcher selects an unverified interpreter. Test unrelated working directories and installed paths. |
| F11 | P1, limited visual observation | **Geometry tests miss text truncation.** Default 1460×1060 offscreen PLOT capture truncates Choose Workplace and lower outcome text despite passing responsive checks. Native font/DPI impact remains unverified. Test text bounds and full VTK/body containment. |
| F12 | P1/P2, source | **Latent output-to-installation coupling.** `plant_layout.py:4295` rewrites `src/index.html`; D3 loads from a CDN. Triggering button is hidden in responsive UI (`2009`), so this is a latent path, not confirmed daily use. Determine feature status; move generated data outside installed resources if retained. |
| F13 | P1, gap | **Solver status/timeout coverage weak.** `Not Solved` is accepted; extracted schedules are checked per cell but not independently against all constraints. All-tools time limits apply per stage. Cancellation discards a completed result rather than interrupting solving. Test timeouts, incumbents, infeasibility, fallback, close-window and full feasibility. |
| F14 | P2, source | **Legacy ambiguity.** Old optimizer paths, archives and duplicate `saveRotationScheme` definitions (`1221,1284`) obscure ownership. Property getter/setter name pairs are not such defects. Prove reachability before deleting anything. |
| F15 | P2, source | **Partial localization.** TS/QM exist, translator setup is commented, Spanish disabled, strings/translation branches mixed into code. `float(text)` and Qt locale validators can disagree. Separate IDs/storage from localized formatting. |
| F16 | P2, source | **Documentation drift.** PLOT code minimum 1300×1045 versus older 1300×900 claim; some docs retain tool-marker ownership after assignment-marker migration. Main spec describes task/summary CSV but active headers are summaries. Schema doc credits main with creation although Save copies a v8 template and destructive `setupDatabase` is not called. |
| F17 | P2, source | **Help mismatch.** Help opens the LiFFT-only `assets/ergohelp01.pdf`; README links the 25-page case manual. Manual predates new profile/scope UI. Main spec says JROT documentation is future work although it exists. |
| F18 | P2, source | **Diagnostics inconsistent.** Broad exception dialogs and print debugging coexist with typed repository errors; no central logging setup found. Introduce contextual diagnostics without worker data. |

No current database corruption was observed. Integrity checks do not prove semantic agreement between independent representations.

## 6. Persistence inventory and strategy

| Database | Schema | Workers | Legacy headers | Normalized assessments | Rotations | Integrity/FKs |
|---|---:|---:|---:|---:|---:|---|
| Template | 8 | 1 | 0 | 0 | 0 | OK / 0 violations |
| Integrated | 8 | 28 | 194 | 191 | 5 | OK / 0 |
| Comparative | 8 | 28 | 194 | 191 | 7 | OK / 0 |
| Legacy JROT | 0 | 10 | 0 | absent | 5 | OK / 0 |
| Legacy test3 | 0 | 17 | 191 | absent | 0 | OK / 0 |

Read-only inspection used `mode=ro&immutable=1` after confirming no sidecars. Do not use immutable inspection on an actively changing database. Backups were inventoried/hashed, not restored into this checkout.

The v8 template has 30 tables: organization/reference/worker; legacy assessment header/tasks; contexts/placements/assignments; normalized assessment and three task tables; versioned Job profiles/measurements and compatibility measurement table; PLOT station/assignment/legacy markers; rotation scheme/scope/targets/assignments. Preserve composite keys, active/current flags, deletion protections and frozen profile links.

Proposed sequence: report legacy-only, normalized-only, mismatched and historical records by full key; establish authoritative ownership with the owner; add assessment services behind existing calls; reconcile copied projects through a new explicit migration; cut over every save/load/delete/transfer/export path; compare main→save→reopen→PLOT→export; retain old tables through a usable release checkpoint. A temporary compatibility adapter may write both representations within one transaction, but uncontrolled bidirectional synchronization is unacceptable. Do not invent Jobs or rewrite frozen rotation profiles to repair incomplete history.

Backups must include XML, DB and images. Future Save As should use a consistent SQLite snapshot or demonstrably quiescent DB, stage/validate output, rewrite relative paths and publish the descriptor last. Multi-file replacement is not inherently atomic; define recovery metadata and project ownership. Reverting code is not a database downgrade: restore a matching verified project snapshot.

## 8. Preservation and test strategy

### Assessment checks actually executed

- **33 unittest cases passed** across database safety/migrations, PLOT positions, Job risk, rotation repository/optimizer, comparative fixture and project fusion. Python 3.10.18 baseline; temporary writable fixtures; original database connections forced read-only; bytecode disabled.
- Five of six separate GUI scripts passed: assessment selection, PLOT risk-view rendering (**four unittest cases**), revised main/worker/organization smoke, PLOT responsive checks, and JROT profile/scope/optimization UI.
- Worker-navigation script failed at line 87 because the supposedly absent legacy assessment is present. Do not describe the full suite as green.
- Offscreen Qt, disabled/avoided VTK, and a substituted WebEngine widget in the PLOT rendering test limit these results. Native OpenGL and real WebEngine have not been certified.
- Visually inspected default PLOT and JROT workplace-scope captures. PLOT label truncation was visible; JROT's inspected scope/table/bottom controls fit. This is limited baseline evidence, not exhaustive visual approval.
- All five current databases passed integrity/FK checks; paired-unit pure-model probes confirmed the moment discrepancy.

### Required characterization corpus

Use deterministic synthetic or owner-approved de-identified fixtures: empty/default; every model; mixed units; 1/15/100 task rows; one worker with multiple contexts; duplicate station IDs across branches; unknown demographics; partial/unavailable results; each risk boundary; legacy PLOT/JROT; integrated v8; retired/current profiles; same Job at multiple placements; all PLOT modes; unplaced/hidden/disabled/locked markers; empty scopes; Unicode paths; missing/renamed images; malformed descriptor; newer schema; locked/read-only DB.

Record inputs, intermediate values, rounded task damage, totals, exact displayed strings/colors, stored values, exported rows and provenance. Require exact equality for legacy rounded outputs and formats; agree tolerances only for unrounded floating intermediates. A tolerance must not hide changed risk classification.

JROT checks should assert feasibility, target counts, block exclusivity, objective quality, profile versions and solver status/gap. Different equally optimal schedules are allowed unless deterministic tie-breaking is part of a specific fixture. Test no-incumbent timeout, feasible timeout, infeasibility, backend absence, cancellation and close while solving. Independently validate every returned schedule.

Persistence checks: failure injection after each mutation; rollback; context isolation; reconciliation; transfer/delete/export; failed-open preserving prior session; metadata/image portability; cancellation writing nothing; backup restoration/checksums. Exercise v0 and intermediate-schema copies: an already-v8 fixture passing a migration test does not demonstrate every upgrade path.

Standardize one runner covering unittest classes, direct functions and script assertions. Unittest discovery alone does not execute every current test. Do not install pytest/coverage without approval. Store exact runtime metadata and machine-readable results; verify original fixture hashes remain unchanged.

Every changed UI window must be visually inspected empty/populated/selected/expanded/error states at agreed sizes. Include text bounds, keyboard/focus, tooltips, long translations, mixed DPI, full VTK model, result cards and bottom controls. Offscreen screenshots complement native testing; they do not replace it.

## 9. Python and dependency matrix — evidence, not migration order

Availability checked on 2026-09-27 using primary release metadata. **No upgrades were installed.** Published wheel eligibility is not verified application compatibility. Every version/range change, including a disposable candidate environment, still needs owner approval. Target ordinary GIL-enabled CPython 3.13; free-threaded Python is outside this plan.

| Component | Reference | Proposed candidate / fallback | Evidence and remaining gates |
|---|---|---|---|
| Python | 3.10.18 | 3.13.15 | Latest listed 3.13 release. First run existing pins on approved 3.13 environment; keep reference until all gates pass. [Python releases](https://www.python.org/downloads/source/) |
| VTK | 9.5.0 | 9.7.0 later; retain 9.5.0 for first interpreter lane | Both publish cp313 wheels for Linux x64/ARM64, Windows x64, macOS Intel/ARM. Test QVTK, GL drivers, STL, camera, resizing/shutdown and packaging. [9.7.0](https://pypi.org/project/vtk/9.7.0/) / [9.5.0](https://pypi.org/project/vtk/9.5.0/) |
| PuLP | 3.2.2 | **3.3.2**, newest 3.x candidate; 4.0 separately | Inspected 3.3.2 published wheel source: `LpVariable.dicts`, integer solve status and `PULP_CBC_CMD` remain. 4.0 requires Python ≥3.12, changes variable ownership/solve return, and removes PULP_CBC_CMD. Current optimizer is not drop-in compatible. [3.3.2](https://pypi.org/project/PuLP/3.3.2/) / [4.0 migration](https://coin-or.github.io/pulp/guides/how_to_migrate_to_v4.html) |
| highspy | 1.11.0 | Latest 1.15.1 is not automatic pairing. Proposed PuLP 3.3.2 pairs with **1.13.0**; PuLP 4.0's `<1.14` constraint permits newest **1.13.1** candidate | PuLP 3.3.2 highs extra declares `highspy==1.13`; 4.0 declares `<1.14`. Baseline/candidates have cp313 wheels. Test statuses, gaps, threads, cancellation and numerical parity. [HiGHS](https://pypi.org/project/highspy/) / [1.13.0](https://pypi.org/project/highspy/1.13.0/) / [PuLP metadata](https://pypi.org/pypi/PuLP/3.3.2/json) |
| PyQt5 | 5.15.11 | Retain initially; latest listed PyQt5 | cp38-abi3 wheels admit standard CPython 3.13 on listed desktop platforms; SIP/Qt runtime must also resolve/load. No Linux ARM64 binding wheel in this release listing. [PyQt5](https://pypi.org/project/PyQt5/5.15.11/) |
| PyQtWebEngine | 5.15.7 | Retain initially | cp38-abi3 wheels available. Native subprocess/resources, D3/offline behavior, packaged startup/shutdown remain untested. [WebEngine](https://pypi.org/project/PyQtWebEngine/5.15.7/) |
| Qt6 bindings | Not reference | PyQt6 6.11.0 + WebEngine 6.11.0, or PySide6 6.11.2 | abi3 distributions accept 3.13. PyQt6 reduces binding-family change; PySide6 is a separate port. Audit enums, QAction location, QRegExp, signals/properties, exec_, Matplotlib/QVTK integration and ownership. Decide distribution/licensing requirements before selection. [PyQt6](https://pypi.org/project/PyQt6/) / [WebEngine](https://pypi.org/project/PyQt6-WebEngine/) / [PySide6](https://pypi.org/project/PySide6/) |
| Qt6 runtime | Qt5 distribution 5.15.17 | PyQt6 Qt/WebEngine runtimes 6.11.2 available | Listed Linux x64 wheels require glibc 2.34, ARM64 2.39. PySide6's listed macOS wheel requires 13+. Retain Qt5 for incompatible OS until an older Qt6 stack is separately verified. Binding version alone does not define runtime floor. [Qt runtime](https://pypi.org/project/PyQt6-Qt6/) / [WebEngine runtime](https://pypi.org/project/PyQt6-WebEngine-Qt6/) |
| Pyomo | 6.9.3 | 6.10.1 if retained | Python ≥3.10, cp313/pure distributions. Active worker uses PuLP, but old paths import Pyomo. Remove only after reachability review and dependency-removal approval. [Pyomo](https://pypi.org/project/pyomo/6.10.1/) |
| NumPy | 2.2.6 unpinned | Keep initially; 2.5.3 later | Both have cp313 wheels; newest requires Python ≥3.12. Test statistics, VTK arrays and missingness. [NumPy](https://pypi.org/project/numpy/2.5.3/) |
| Matplotlib | 3.10.5 unpinned | 3.11.2 later | Python ≥3.11, cp313 wheels. Test Qt backend, canvas reattachment, fonts and PNG/SVG/PDF output. [Matplotlib](https://pypi.org/project/matplotlib/3.11.2/) |
| pycountry | 24.6.1 | 26.2.16 later | Python ≥3.10, pure wheel. Reference-data changes can affect names/options; preserve stored identifiers. [pycountry](https://pypi.org/project/pycountry/26.2.16/) |
| Pillow | 11.3.0 transitive | 12.3.0 later | Python ≥3.10, cp313 wheels. Verify image decoding and exports. [Pillow](https://pypi.org/project/Pillow/12.3.0/) |
| SQLite, SIP, CBC, other transitive libraries | Environment-specific | Capture exact versions/binaries first | SQLite varies with interpreter build; fallback needs actual runnable CBC. Record Qt/SIP, BLAS, GL and solver binaries, hashes and notices rather than inferring them from seven pins. |

The revised plan schedules an approved target-stack compatibility experiment before production slices are built. The current 3.10 environment remains the reference environment, not a required architecture for the new application. Candidate fallback choices require review rather than silent adoption. Metadata alone does not establish full application compatibility.

### Key source references

- [Main project open/save](<../src/main.py:2202>)
- [Main assessment load](<../src/main.py:6318>)
- [Main assessment saves](<../src/main.py:6957>)
- [LiFFT numerical model](<../src/pyLiFFT.py:315>)
- [DUET numerical model](<../src/pyDUET.py:75>)
- [Shoulder numerical model](<../src/pyTST.py:66>)
- [PLOT normalized read model](<../src/plot_position_repository.py:59>)
- [PLOT summary semantics](<../src/plant_layout.py:6684>)
- [PLOT HTML output](<../src/plant_layout.py:4295>)
- [Rotation optimizer](<../src/rotation_optimizer.py:1>)
- [Rotation persistence](<../src/rotation_repository.py:322>)
- [Database safety](<../src/database.py:42>)
- [Migration entry point](<../src/schema_migrations.py:1429>)
- [Job profiles](<../src/job_risk_repository.py:26>)
- [Job placements](<../src/job_placement_repository.py:115>)
- [Navigation test failure](<../tests/test_worker_navigation_context.py:87>)
- [Development baseline](<../docs/development-workflow.md:1>)
- [Current database documentation](<../docs/database-schema.md:1>)
- [JROT specification](<../docs/jrot-functional-specification.md:1>)
- [UI and dependency rules](<../AGENTS.md:1>)

### Complete Python module index

This index includes runtime, test, script, asset and archive code; inclusion does not imply runtime reachability. Definition-level details were indexed during the original assessment.

| File | Lines |
|---|---:|
| [assets/D3-03/main.py](<../assets/D3-03/main.py>) | 25 |
| [assets/PlatLayoutWindowUI.py](<../assets/PlatLayoutWindowUI.py>) | 500 |
| [scripts/create_comparative_risk_test_project.py](<../scripts/create_comparative_risk_test_project.py>) | 263 |
| [scripts/fuse_test_projects.py](<../scripts/fuse_test_projects.py>) | 220 |
| [scripts/inventory_project_database.py](<../scripts/inventory_project_database.py>) | 29 |
| [src/compareopallrotation_window.py](<../src/compareopallrotation_window.py>) | 222 |
| [src/comparerotation_window.py](<../src/comparerotation_window.py>) | 159 |
| [src/database.py](<../src/database.py>) | 161 |
| [src/database_inventory.py](<../src/database_inventory.py>) | 84 |
| [src/job_placement_repository.py](<../src/job_placement_repository.py>) | 404 |
| [src/job_risk_repository.py](<../src/job_risk_repository.py>) | 545 |
| [src/job_window.py](<../src/job_window.py>) | 1448 |
| [src/jrot_database.py](<../src/jrot_database.py>) | 11 |
| [src/line_window.py](<../src/line_window.py>) | 625 |
| [src/main.py](<../src/main.py>) | 9425 |
| [src/multiselectcombobox.py](<../src/multiselectcombobox.py>) | 81 |
| [src/optimizedrotation_window.py](<../src/optimizedrotation_window.py>) | 74 |
| [src/organization_window.py](<../src/organization_window.py>) | 540 |
| [src/plant_layout.py](<../src/plant_layout.py>) | 7968 |
| [src/plant_window.py](<../src/plant_window.py>) | 684 |
| [src/plot_position_repository.py](<../src/plot_position_repository.py>) | 525 |
| [src/plotviewerdialog.py](<../src/plotviewerdialog.py>) | 116 |
| [src/pyDUET.py](<../src/pyDUET.py>) | 116 |
| [src/pyLiFFT.py](<../src/pyLiFFT.py>) | 373 |
| [src/pyTST.py](<../src/pyTST.py>) | 134 |
| [src/risk_colors.py](<../src/risk_colors.py>) | 24 |
| [src/risk_ranges.py](<../src/risk_ranges.py>) | 17 |
| [src/rotation_layout.py](<../src/rotation_layout.py>) | 3644 |
| [src/rotation_optimizer.py](<../src/rotation_optimizer.py>) | 162 |
| [src/rotation_repository.py](<../src/rotation_repository.py>) | 412 |
| [src/rotation_schema.py](<../src/rotation_schema.py>) | 284 |
| [src/rotation_scope_dialog.py](<../src/rotation_scope_dialog.py>) | 207 |
| [src/schema_migrations.py](<../src/schema_migrations.py>) | 1505 |
| [src/section_window.py](<../src/section_window.py>) | 610 |
| [src/shift_window.py](<../src/shift_window.py>) | 712 |
| [src/station_window.py](<../src/station_window.py>) | 719 |
| [src/testmultiop.py](<../src/testmultiop.py>) | 622 |
| [src/tooldatadialog.py](<../src/tooldatadialog.py>) | 95 |
| [src/tooltransferdialog.py](<../src/tooltransferdialog.py>) | 667 |
| [src/updatecode/main.py](<../src/updatecode/main.py>) | 7643 |
| [src/updatecode/plant_layout.py](<../src/updatecode/plant_layout.py>) | 4516 |
| [src/visualjobmarker.py](<../src/visualjobmarker.py>) | 152 |
| [src/visualworkertool.py](<../src/visualworkertool.py>) | 1065 |
| [src/vtk_camera_director.py](<../src/vtk_camera_director.py>) | 189 |
| [src/worker_transfer_window.py](<../src/worker_transfer_window.py>) | 519 |
| [src/worker_window.py](<../src/worker_window.py>) | 2903 |
| [src/workertransferdialog.py](<../src/workertransferdialog.py>) | 879 |
| [src/zcpwindow.py](<../src/zcpwindow.py>) | 25 |
| [tests/test_assessment_context_selection.py](<../tests/test_assessment_context_selection.py>) | 141 |
| [tests/test_comparative_risk_fixture.py](<../tests/test_comparative_risk_fixture.py>) | 108 |
| [tests/test_fuse_test_projects.py](<../tests/test_fuse_test_projects.py>) | 73 |
| [tests/test_job_risk_repository.py](<../tests/test_job_risk_repository.py>) | 569 |
| [tests/test_jrot_database.py](<../tests/test_jrot_database.py>) | 227 |
| [tests/test_jrot_profile_ui.py](<../tests/test_jrot_profile_ui.py>) | 394 |
| [tests/test_plot_position_repository.py](<../tests/test_plot_position_repository.py>) | 262 |
| [tests/test_plot_responsive_ui.py](<../tests/test_plot_responsive_ui.py>) | 531 |
| [tests/test_plot_risk_view_rendering.py](<../tests/test_plot_risk_view_rendering.py>) | 237 |
| [tests/test_revised_ui_smoke.py](<../tests/test_revised_ui_smoke.py>) | 253 |
| [tests/test_rotation_optimizer.py](<../tests/test_rotation_optimizer.py>) | 67 |
| [tests/test_rotation_repository.py](<../tests/test_rotation_repository.py>) | 146 |
| [tests/test_schema_migrations.py](<../tests/test_schema_migrations.py>) | 349 |
| [tests/test_worker_navigation_context.py](<../tests/test_worker_navigation_context.py>) | 100 |

