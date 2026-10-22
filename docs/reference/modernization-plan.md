# ErgoTools modernization plan — revised architecture and implementation standards

Revision 2 · 2026-09-27 · **Proposal awaiting agreement. No implementation or migration is authorized by this document.**

This replaces the strategy in the earlier temporary plan. The accompanying [assessment evidence](modernization-assessment.md) retains the repository inventory, code paths, findings, test results and dependency matrix. The plan and evidence now live in the current repository's `docs/` directory, as requested. Existing application code, assets, configuration, dependencies and data remain unchanged.

## 1. Requirements and corrections

The **current integrated working code and its observed behavior** establish what ErgoTools does. `ErgoToolManual.pdf` is an old reference, not an architectural, functional or visual specification. Tests and documentation are evidence to reconcile with the code, not authorities when they contradict it. Scientific correctness is a separate question requiring authoritative model references and explicit decisions; current behavior can contain defects.

LiFFT, DUET, Shoulder Tool, PLOT and JROT already coexist in one application. The target preserves that integration while separating responsibilities. Historical branches do not imply separate present-day products.

The migration will construct a cleaner implementation component by component: review, redesign where justified, standardize, document and test each component. Keeping the old tree runnable supplies the reference; it does not justify filling the new application with unchanged legacy modules, `OldWorking` variants, or permanent compatibility scaffolding.

Python/library modernization is part of the migration, not an optional final exercise. Candidate versions and API changes are evaluated early and approved explicitly under the repository dependency rule. The old environment remains available for reference comparisons; new components target the agreed modern environment. Different versions are compared intentionally, not presented as proof of compatibility with the old baseline.

Mandatory foundations from the first slice:

- One integrated application, with separately testable assessment, PLOT and JROT responsibilities.
- Multilingual UI and messages; English and Spanish proposed as initial release languages, extensible to others.
- Metric and imperial support based on an audit of the implementation already present.
- Project/session lifecycle, save semantics, recent projects, settings and undo/redo architecture.
- Reusable core without dependencies on a particular UI, so future tablet/mobile work remains possible.
- Explicit code/documentation standards and enforceable acceptance gates.

These are architectural requirements now. Complete translated screens, recent-project UI and particular undoable operations are delivered as planned slices, not silently deferred beyond modernization.

## 2. Architecture: modular monolith with ports/adapters and desktop MVP

Use a **modular monolith**: one application, one composition root, well-defined feature modules. Within it use **ports and adapters** to isolate persistence, optimization and rendering. Use **Model–View–Presenter (MVP)** for desktop interaction: views display data and emit intent; presenters coordinate use cases and build view state. This combination fits a scientific desktop application without introducing distributed services or a framework-heavy abstraction layer.

Domain models are plain Python objects/functions, not Qt item models. Qt's table/tree models remain presentation adapters. Dependency injection is explicit constructor wiring in the composition root, not a service locator or global active window.

### Proposed organization

```text
src/ergotools/
  domain/
    assessments/       lifft.py, duet.py, shoulder.py, inputs.py, results.py
    work/              workers, organization, jobs, assignments, risk profiles
    plot/              filter definitions, populations, summaries, comparisons
    rotation/          schedules, scope, constraints, objective definitions
    quantities.py      explicit quantities, units and conversion policies
    errors.py          domain validation errors
  application/
    assessments/       calculate, load, save, transfer, delete
    projects/          create, open, save, save_as, close, backup
    jobs/              profile/placement/assignment use cases
    plot/              build applied view; marker commands
    rotation/          prepare, optimize, compare, apply, persist
    contracts/         repository, solver, settings, clock and file-store ports
    session.py         project sessions and operation state
    history.py         UI-independent reversible edit commands
    events.py          small explicit application notifications
  infrastructure/
    sqlite/            connection factory, unit of work, repositories, migrations
    projects/          .ergprj, project package and snapshot adapters
    optimization/      PuLP/HiGHS adapter and solver result conversion
    exports/           CSV/report writers
    settings/          desktop settings storage
    resources/         installed/read-only assets and writable-path resolution
    diagnostics/       logging configuration and diagnostic reports
  presentation/desktop/
    shell/             integrated navigation, project actions and command routing
    assessments/       assessment views and presenters
    plot/              PLOT views/presenters and Qt map models
    rotation/          JROT views/presenters and schedule models
    management/        worker, organization and Job editors
    widgets/           shared styled controls, validated quantity editors
    rendering/         VTK body and Matplotlib/chart adapters
    localization/      desktop translator and number/date formatting adapter
    theme/             palette, typography, spacing, icons and tooltips
  bootstrap.py         dependency wiring and process entry point
resources/             icons, models, translation catalogs, read-only templates
tests/                domain, application, adapter, integration, GUI, platform
docs/                 architecture, decisions, calculations, format, user workflows
```

`tests/` and `docs/` are repository-root directories. Package names express responsibilities; final fine-grained filenames follow real use cases rather than creating empty abstraction layers in advance.

### Ownership and dependency rules

| Component | Owns | May depend on | Must not own/import |
|---|---|---|---|
| Ergonomic domain | Formula constants, rounding rules, scientific model identity, typed input/results | Standard library and domain quantities | Qt, SQL, file dialogs, VTK, Matplotlib, translated strings |
| Work domain | Identity/context, assignment and profile lifecycle invariants | Other domain value types | Widget state or SQL connection lifetime |
| PLOT domain | Population selection semantics, aggregation, missingness, risk comparison | Domain work/assessment values | Qt scenes, SQL cursors, current-window discovery |
| Rotation domain | Target/schedule definitions, constraints/objective specification, independent feasibility checks | Domain work/risk values | PuLP objects or Qt workers |
| Application | Workflow sequencing, authorization/validation boundaries, transactions through ports, session/history | Domain and contracts | Concrete Qt/SQLite/solver implementations |
| Infrastructure | SQLite, XML, solver APIs, export encoding, platform storage | Domain/application contracts | Decision-making based on widgets |
| Presentation | User intent, view state, localized display, interaction/rendering | Application interfaces and domain result types | SQL, scientific formulas, solver model construction |
| Bootstrap | Concrete implementation selection and lifecycle | All layers | Business rules |

Enforce these rules with import-boundary checks and review. No domain import initializes Qt, VTK, WebEngine or a solver. Feature modules do not import each other's windows. For example, PLOT requests an assessment-open action from the application shell; it does not call a main-window widget method. Job risk queries serve both PLOT and JROT through explicit contracts: PLOT requests current approved profiles; JROT requests frozen historical profile versions.

Representative flow: assessment view → presenter → calculate/save use case → domain calculator/repository port → SQLite adapter → result/application notification → relevant presenters refresh. PLOT receives an immutable applied filter and dataset. JROT receives an immutable schedule/risk snapshot; a background runner invokes the solver adapter and validates the result before presenting it. User edits invalidate stale asynchronous results through session/revision identifiers.

### Why this fits ErgoTools

The difficult boundaries are already visible in the code: reusable formulas, evolving SQLite repositories, integrated windows, and a mostly plain-data optimizer. Formalizing these boundaries preserves useful work while removing coupling. One process keeps local projects simple; ports permit changing Qt, solver APIs or storage without rewriting formulas. MVP makes state/navigation testable and avoids hiding application logic in signal handlers. No generic event bus, ORM, microservice, plugin system or dependency-injection framework is required initially.

## 3. Coding and documentation standards

These are proposed binding standards for all new/migrated code, not claims about the current codebase.

| Area | Standard |
|---|---|
| Style | PEP 8 conventions, four spaces, UTF-8, LF, automated formatting; project code line length 88, prose/docstrings wrapped where readable. The 88-column limit is an explicit project choice. |
| Naming | English identifiers; `snake_case` modules/functions/methods/variables; `PascalCase` classes; `UPPER_SNAKE_CASE` constants; `_name` implementation details. `lifft.py`, `LifftCalculator`, `calculate_assessment`, `worker_id`, `probability_percent` are representative names. User-facing LiFFT/DUET/ST branding remains unchanged. |
| Framework exceptions | Keep required framework override names such as `closeEvent` and `paintEvent`; user-defined handlers use names such as `on_save_requested`. Map old schema fields at repository boundaries; do not rename stored keys just for style. |
| Types/data | Type all public functions/methods and domain/application boundaries, including return values. Use dataclasses/value objects/enums for stable contracts. Use `None` for absence, not empty strings or zero. Avoid positional dict/tuple conventions for rich records and mutable default arguments. |
| Numerical names | State dimension/scale in type or name; distinguish `probability` (0–1) from `probability_percent` (0–100), `mass_kg` from `force_n`. Scientific symbols are acceptable inside a documented formula, not as ambiguous cross-module fields. |
| Functions/classes | One coherent responsibility; prefer pure functions for arithmetic and composition for services. Constructors establish state; they do not migrate databases or start expensive work. No hidden file/database mutation on import. |
| Imports | Explicit package imports, ordered standard/third-party/project; no wildcard imports, sys.path hacks, circular imports or global current-window lookup. |
| Errors | Typed errors with stable code and structured context; validate at boundaries. Catch expected exceptions near recovery points; broad catch only at a process/UI/task boundary with diagnostic recording. Do not silently swallow errors or treat missing risk as zero. |
| Persistence | Parameterized SQL in adapters only; one application transaction per command, explicit rollback, connection/foreign-key policy. Repositories never display dialogs or commit midway through a use case. |
| Resources/config | pathlib and shared resource resolver; installed resources read-only; generated HTML/logs/settings/projects use approved writable locations. No working-directory assumptions or machine-specific absolute paths. |
| State/concurrency | Explicit owners; no mutable module globals. Qt objects remain on the GUI thread. Background tasks receive snapshots, report typed results/progress, and cannot query widgets. |
| Hygiene | No `Old`, `OldWorking`, numbered alternate implementations, commented-out code, production experiments or duplicated definitions. Keep provenance in Git/decision records. No unused imports or unexplained magic constants. |
| Testing | `test_<behavior>`, deterministic inputs, explicit setup/teardown and temporary data. Assertions test contracts, boundaries and failure modes; no dependence on mutable personal working fixtures. |

PEP 8 supplies naming/layout conventions; PEP 257 supplies docstring conventions. Project-specific rules above settle remaining choices. [PEP 8](https://peps.python.org/pep-0008/) · [PEP 257](https://peps.python.org/pep-0257/).

Document public APIs with concise purpose, units, parameters/results, errors and side effects. Use Google-style sections consistently where detail is needed; type hints carry type information. Formula docs record sources, model version, constants, limits, rounding and reference examples. Comments explain scientific/engineering reasons, not restate syntax. Each migrated workflow updates architecture/format/user documentation and an architecture decision record when a tradeoff changes. Do not claim the old manual defines acceptance.

Proposed enforcement: Ruff for formatting/import/lint rules and mypy for type checking, with strict domain/application checks and localized documented exceptions for external GUI bindings. Exact tooling versions and any test/development dependencies require approval before installation; none are installed now. Existing baseline unittest/script tests remain executable for comparison. Architecture checks, tests, type/lint checks and documentation review become gates for each new slice. [Ruff documentation](https://docs.astral.sh/ruff/) · [mypy documentation](https://mypy.readthedocs.io/en/stable/).

## 4. Shared services, state and standard desktop workflows

Shared functionality has one named owner: quantities/conversions, risk classification policies, context identifiers, profile lifecycle, project persistence, settings, localization, command history, resource resolution and diagnostics. Do not create a catch-all `utils.py`, a universal repository, or a giant shared manager. Extract proven common behavior while keeping scientific/model-specific differences explicit.

| State/service | Proposed contract |
|---|---|
| User preferences | Language, default units, recent files, camera/display preferences; user-scoped settings port and versioned adapter. |
| Project metadata | Project format/model versions, paths and explicit project defaults; saved with project. |
| Assessment record | Original unit metadata, scientific inputs/results and exact assignment/tool identity; never inferred from global language. |
| Session | Active project and selected context, draft documents, save status, pending tasks and revision; explicit application-owned object. |
| PLOT state | Pending UI filters separate from immutable applied analysis; visual marker edits separate from risk data. |
| JROT state | Editable schedule, optimization snapshot/result, profile provenance and explicit apply/save. |
| View state | Selection, expanded panels and focus; presentation-owned, persisted only where specified. |
| Logging | Standard logging interface, operation/error IDs and technical context; redact personal data, no unconditional print debugging. Diagnostic paths and retention are settings. |

Configuration is typed, validated and versioned. Use defaults → user preference → explicit project/record setting where appropriate; an existing record's units always govern interpretation. Transient overrides affect presentation only unless explicitly applied. No global setting silently relabels persisted values.

### Undo/redo and save semantics

Use a **Command pattern** for reversible document edits, with history owned independently of Qt. A Qt action adapter exposes Undo/Redo, action labels and enabled state; do not maintain a separate competing Qt/application history. Text editors can use their local typing undo; focus-aware command routing prevents Ctrl+Z from undoing a different document while editing a field.

Proposed undo scope: task add/edit/delete, assignment of a schedule cell, applying an optimized schedule as one operation, marker move/scale as a coalesced drag operation, and reversible draft metadata changes. Each command records minimal before/after data, validates execution and undo, and belongs to a project/document identity. Undo restores source edits; derived calculations are recomputed deterministically. A new edit after undo clears that history's redo branch.

Save writes draft state transactionally and marks a clean revision; it does not itself become an undo command. Undo after save creates a dirty draft. Switching documents routes to the appropriate history; closing a project releases it after dirty-state handling. Calculation/optimization previews do not write data; applying a result is undoable. File open/export/backup, schema migrations and irreversible external effects are not ordinary edit commands. Published/approved risk-profile changes require a new explicit revision or compensating workflow, not destruction of historical evidence by Undo.

Bind platform-standard Undo/Redo shortcuts: Ctrl+Z and corresponding redo on Windows/Linux; Command equivalents on macOS, with supported alternate redo shortcuts determined by the binding/platform. Menus show the actual action and shortcut. Test focus, multi-field edits, merged drags, save/undo/redo, project changes and failed commands.

Recent projects use a settings-backed service with missing/moved-file handling and a clear-history action. Listing recent files must not open or migrate their databases. Project open/save/save-as/close use explicit dirty checks and cancellation; failed operations leave the current session usable. Recommended Save As includes pending validated edits in the new snapshot, with an explicit decision about whether the original project is also saved; default proposal is no implicit write to the original. Confirm this policy before implementing the project slice.

## 5. Multilingual and metric/imperial support

### Existing behavior to preserve and clarify

`main.py:1364` already derives LiFFT/Shoulder labels from recorded units. `1705`/`1711` switch measurement settings; `5404` changes selected system and labels, with a comment questioning conversion of existing data. `_loadToolsData` loads assessment-specific unit values. LiFFT/Shoulder already convert cm and N to internal inch/lb inputs. Worker measurements have cm/kg labels. `getCurrentMetricSystem` returns `English` for imperial, illustrating inconsistent naming. TS/QM and translation branches exist; the Spanish menu is disabled although system locale can select its action. These are concrete starting points, not a greenfield unit/language problem.

### Required target contracts

- Language, locale and units are independent settings: Spanish does not imply metric; English does not imply imperial. Use stable language and unit identifiers, not translated labels in business logic or storage.
- UI text comes from catalogs from the first view, including dialogs, tooltips, menus, validation, risk labels, accessibility and export/report headings. Qt translation facilities belong in the desktop adapter; domain errors return code/parameters rather than translated sentences.
- English and Spanish are the initial proposed coverage gate; additional catalogs do not require changing scientific code. Use complete messages with plural/context support, no sentence concatenation. Fallback is controlled and visible in QA. Test language switching, longer text, layout and locale-formatted numbers/dates.
- Quantities carry dimension/unit. Unit conversion is centralized; metric and imperial input/display/export work throughout the integrated application. Force N versus mass kg, and pounds-force versus mass, require explicit definitions; never use one undifferentiated `load` unit conversion for all measurements.
- Preserve original recorded inputs/units and model provenance. Do not bulk-convert historical values or mandate universal SI storage before numerical characterization. A domain conversion policy can normalize inputs internally while preserving the model's documented calculation units, legacy constants and rounding until a scientific correction is approved.
- A user-facing unit switch converts displayed quantities without changing physical exposure or cumulative results. Reinterpreting an entered number as another unit is a separate explicit correction, never an accidental label change. The discrepancy with current behavior is documented and accepted as an intentional workflow correction.
- Display precision is separate from calculation/storage precision. Localized decimal parsing is validated at UI boundaries; internal numeric values and machine-readable exports have explicit invariant conventions. Test metric→imperial→metric, saved/reopened units, mixed-unit projects, locale decimal separators, rounding extremes and legacy records.

The previously observed metric moment multiplier and `<5`/`>90` storage rules remain owner/scientific decisions. Cleaner architecture does not authorize silent result corrections; it makes those rules explicit and testable.

## 6. Migration strategy: a clean implementation in usable slices

The old application remains the working reference in its current tree. The new location holds only reviewed target code, tests, approved resources and documentation. Initially it may offer a smaller, explicitly identified set of migrated capabilities; it is not declared a replacement until feature parity and acceptance gates are satisfied. Each checkpoint remains runnable for its completed scope while the existing application provides the full operational feature set.

Do not import the old application at runtime, copy its monolithic windows wholesale, or maintain parallel `old/new` implementations in the production package. Small proven functions may be retained after review, normalization, documentation and testing; equivalent behavior does not require rewriting correct arithmetic unnecessarily. Reference outputs and separate test-only oracle runners remain outside the production package. Old project-format readers are deliberate compatibility adapters, not a license to retain obsolete application code.

### Ordered stages

| Stage | Scope / affected components | Prerequisites and validation | Acceptance, risks and usable checkpoint |
|---|---|---|---|
| 0 — Approve design and capture reference | Architecture/standards, feature inventory, exact environment and source/data manifest; characterization fixtures | Agree this plan and destination. Reconcile existing dirty/untracked state; capture code-derived behavior and known failures. Reference tests run with existing baseline versions. | Agreed architecture and numerical/UI contracts. Preserve all operational files. Checkpoint: current application remains usable and its reference evidence is reproducible. Risk: treating a stale test/manual as authority. |
| 1 — Target-stack experiment and clean foundation | Approved Python 3.13 target; candidate Qt/VTK/solver versions; package boundaries, bootstrap, settings, quantity/localization/history contracts, CI/tooling configuration | Explicit approval for exact runtime and tooling changes. Use earlier matrix as researched candidates, not proof of integrated compatibility. Exercise imports, native Qt/VTK rendering, solver, translations, resource lookup and packaging feasibility. | Select/document an actually tested target stack before production slices depend on it. Checkpoint: small runnable integrated shell with architectural checks. Risk: platform binary/API constraints; report alternatives before changing targets. |
| 2 — Calculations and first complete assessment | Typed model APIs, audited constants/units, repository transaction boundary, one assessment view/presenter, project create/open/save, edit history | Characterization of current formulas and rounding; approved data-conflict policy. Golden vectors plus both units/languages; save/reopen/undo/redo and failure injection. | A full vertical slice calculates, persists and reloads correctly with modern standards. Checkpoint: one documented assessment workflow works end-to-end. No unexplained result differences. Risk: legacy normalization gap and changing precision accidentally. |
| 3 — Remaining assessments and shared project/work management | All three tools, workers/organization/Jobs/profiles/assignments, transfer/delete/export, recent projects, settings, Save As/backup | Reuse established contracts. Verify exact context isolation, profile lifecycle, atomic saves, unit/language switching, recent-file errors, dirty prompts and snapshots. | All individual/work-management workflows migrated; no duplicated conversion, save, validation or style logic. Checkpoint: usable integrated assessment application with ordinary desktop lifecycle. Risk: mixed schema consumers; cut over coherently. |
| 4 — PLOT | Population/aggregation services, normalized queries, maps/charts/presenters, marker history, three risk views | Stable work/assessment contracts. Compare counts, probabilities, standard deviation, filters, current profiles, missingness and markers against reference. Native/offscreen visual and export checks. | Individual/Job/Comparison modes preserved with explicit semantics. Checkpoint: assessments and PLOT operate together in new application. Risk: denominator changes, grouping/deduplication and coordinate conversion. |
| 5 — JROT | Scope/targets, solver adapter, background lifecycle, result validation, schedule editing/history, comparisons and persistence | Stable profiles/placements; approved solver stack. Validate both scope modes, objective/constraints, frozen provenance, timeouts, infeasibility, cancellation and redo of applied schedules. | Equivalent feasibility/objective behavior, complete independent validation, no GUI access from solver. Checkpoint: all five tools coexist in new application. Risk: alternate optima, backend status/API changes and stale async results. |
| 6 — Full parity, native release and cleanup | All verified remaining workflows including anthropometry/hidden features as agreed; installers/resources; manuals and release records | Feature coverage ledger closes every item as preserved or explicitly approved changed. Linux/Windows/macOS native acceptance, clean installation, restore drill, complete translation/units/history coverage. | New release replaces old only after approval. No orphan legacy code or unsupported implied features. Checkpoint: independently installable supported application. Risk: hardware/platform packaging and unnoticed secondary features. |

Recent projects, undo/redo, localization and unit contracts start in Stage 1 and gain real workflow acceptance in Stages 2/3; they are not left as an unspecified future backlog. Broader reporting formats, additional optimization constraints or scientific model corrections remain separate, explicitly approved enhancements.

### Definition of migrated

A component is migrated only when its current behavior is understood; its new ownership/API is documented; code satisfies standards and dependency boundaries; characterization and workflow tests pass; persistence and failure behavior are verified; unit/language/history requirements for its scope are met; changed UI states receive visual inspection; intentional differences are approved and recorded; and no production dependency on the old tree remains. "It opens" or "the imports work" is insufficient.

### Git, data and folder isolation

After agreement, use an owner-approved separate folder/branch. A Git worktree shares administrative metadata; if even that must remain unchanged, choose an independent clone. Preserve current dirty/untracked work as reference evidence without resetting, cleaning, stashing or committing this checkout.

A worktree checks out tracked old files by default. Do not present that checkout as the clean target architecture: in the new branch, explicitly establish the new package/resource layout and remove inherited obsolete production paths before treating it as a target milestone. All such changes occur only in the separate location after approval. Keep legacy history accessible in Git and reference execution in the original tree. An independent repository is an alternative if a cleaner physical starting point is preferred; retaining Git ancestry is useful but does not dictate the production layout.

Use one reviewable slice per commit/PR, with source/environment/schema/fixture identifiers. Run candidates against copied projects only. Project format migration includes verified backup and semantic reconciliation; restoring data is separate from reverting code. Never resolve legacy-versus-normalized assessment conflicts by silently choosing the newest-looking row or discarding one representation. No automatic pushes, merges or changes to the current tree are part of this plan.

## 7. Testing, equivalence and evidence

The previous assessment found a useful existing suite: 33 database/optimizer cases passed, and five of six GUI scripts passed; navigation's empty-context expectation contradicted its fixture. Those are prior results, not a claim that tests were rerun for this documentation change. Existing tests also do not establish comprehensive numerical, native-graphics or cross-platform coverage.

| Level | Required evidence as each slice is built |
|---|---|
| Domain | Golden inputs/intermediates/results for all model branches; units/rounding/zero/extremes; risk thresholds; Job lifecycle and rotation feasibility rules; no GUI/DB/solver imports. |
| Application | Fake repository/solver/settings ports; transactional use-case boundaries; selected-context state; dirty/save/failed-open behavior; error contracts; command execute/undo/redo and async invalidation. |
| Adapters | SQLite integrity/FKs/rollback and migration idempotence; descriptor/image portability; solver statuses/binaries; resource paths; serialization/encoding; no writes into installed code. |
| Integration/equivalence | Current reference and new implementation run separately on matched copied inputs. Compare scientific, persisted and exported results, context identities, PLOT populations, JROT constraints/objectives and profile provenance. |
| GUI | Both languages and both unit systems; empty/populated/selected/expanded/error states; keyboard/history, filters, dialogs, full text bounds and consistent ErgoTools styling. |
| Native/platform | Linux, Windows and macOS as supported; VTK body/camera, real WebEngine if retained, solver/background lifetime, DPI/fonts, paths, installer and offline startup. |

Use exact equality for established rounded outputs and strings; justified tolerances for unrounded floating values. Do not mask changed risk categories with a wide tolerance. Equally optimal JROT schedules may differ: compare feasibility, counts and objective quality unless exact tie-breaking is required. Scientific validation against reference publications is separate from equivalence to the current software.

Maintain a behavior ledger: source path/entry point → observed contract → reference fixture → new API → tests → intentional delta → approval. Known bugs become explicit decisions: preserve behavior temporarily, or approve a correction with a reproduction and migration note. Do not blindly encode a bug as the permanent target requirement.

Shared-state tests include multiple assessment contexts, missing demographics, inactive placements, retired/current profiles, marker enable/visible distinction, unsaved changes, invalid number entry, locale separators and switching projects during a background operation. Use immutable reference fixtures and temporary writable copies; do not rewrite working examples while testing.

For every changed UI, follow existing AGENTS.md: processed icons/palette/type/spacing/tooltips, and visual inspection of complete VTK model, cards, labels and bottom controls. Profile Approve/Use current/Retire icon concepts remain known gaps; styled text controls are acceptable until matching assets are supplied. No unrelated icon substitution.

## 8. Platform and future tablet/mobile boundaries

Desktop remains the implementation target now. Domain/application APIs are UI-independent and exchange typed, serializable data, never Qt objects, SQL cursors or PuLP variables. Resource/filesystem/settings/network capabilities are adapters. Calculation results and command/error schemas carry versions where interchange requires them.

This permits a future browser/tablet frontend to call the same Python services, or a native/offline frontend to reuse the core where a supported runtime exists. If a platform requires another runtime, shared golden vectors and explicit scientific contracts validate a port. It does not guarantee Python/Qt/VTK/HiGHS run unchanged on a phone. Server-side computation versus local/offline storage/optimization, synchronization and simplified rendering are later decisions. Do not implement a web API, synchronization service or mobile interface now merely to anticipate them.

Linux testing must cover supported GL/Qt backends and distro/glibc floors. Windows needs explicit interpreter/launcher, file locks, Unicode/long paths and scaling. macOS needs native rendering, bundle resource paths and both Intel/Apple silicon if supported. Target OS/architecture floors influence the early dependency experiment, not just final packaging. Owner hardware validation is necessary for platforms unavailable in the development environment.

## 9. Documentation deliverables and decisions before implementation

Documentation lives alongside the new code and changes with its contracts: architecture/module map, coding guide, architecture decision records, model/units specifications, project/schema/migration format, development/runtime setup, test/fixture guide, packaging/recovery procedures and current user workflows. Retain historical manuals clearly labeled; update user documentation from the implemented integrated application.

Decisions to settle in order:

1. Approve or adjust the proposed architecture, standards, clean-slice strategy and target-folder/Git arrangement.
2. Confirm reference datasets/features and initial language coverage (English/Spanish proposed), supported OS/architectures, and how previously observed defects should be characterized.
3. Approve exact target Python/library and development-tool versions for the early compatibility experiment; select Qt binding based on real platform/API results.
4. Agree data reconciliation, physical unit definitions and any scientific corrections; preserve original inputs/provenance.
5. Confirm Save As pending-edit policy, document history boundaries and treatment of historically approved/persisted operations.
6. Confirm native test hardware and release/distribution requirements before packaging.

No approval is inferred from requesting this revision. Until agreement, work remains documentation and assessment only.

## 10. Requirement-to-plan checklist

| Clarification | Where addressed |
|---|---|
| Code is current truth; manual is old | Sections 1 and 7; assessment evidence preface |
| PLOT/JROT already integrated | Sections 1–2; staged integration acceptance |
| Durable documentation inside current tree | This file and modernization-assessment.md |
| New codebase must be reviewed/clean, not copied legacy | Section 6 and definition of migrated |
| Explicit architecture and dependency pattern | Section 2 and ownership table |
| Naming/coding/documentation conventions | Sections 3 and 9 |
| Avoid duplicated functionality | Sections 2 and 4 |
| Configuration/state/logging/errors | Sections 3–4 |
| Undo/redo, recent projects, ordinary lifecycle | Section 4 and Stages 1–3 |
| Multilingual and metric/imperial foundation | Section 5, with existing-code evidence |
| New Python/library compatibility part of migration | Stage 1 and retained researched dependency matrix |
| Incremental tests and behavioral equivalence | Sections 6–7 |
| Future tablet/mobile without implementation now | Section 8 |
| No code/dependency/migration changes before agreement | Status, Sections 1 and 9 |
