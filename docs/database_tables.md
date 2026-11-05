# Current native database — format 24

A `.ergprj` file is a self-contained SQLite project. It stores organization, workers,
Job values, assessments, plant images/geometry and production JROT schemes. The integrated
application edits a private working database; main Save publishes accepted data. Backup
copies the durable baseline. Foreign keys and typed cross-catalog validation protect
relationships; multi-record edits use transactions with rollback.

## Functional tables

There are 17 functional tables plus optional `project_display_settings`. No risk-profile,
evidence/currentness or assessment-version tables participate in the current full format.

| Table | Current purpose | Identity / relationship |
|---|---|---|
| project_metadata | Project ID, title, default units and native compatibility marker | One typed metadata record; file version is not an assessment version |
| project_details | Description, creation time and language | Validated project details |
| project_display_settings | Optional display precision/default-unit, assessment disclosure and rotation selection | One optional record; source measurements are not rounded by display changes |
| work_catalog | Workers and Plant/Section/Line/Station/Shift organization | Typed hierarchy with exact scoped station and shift identities |
| jobs | Activity definitions | Job ID; names/descriptions and active state |
| job_placements | Jobs available at an exact station/shift | Placement ID plus Job and workplace membership |
| worker_assignments | Worker workplace/shift, with optional Job placement | One active owner per worker/context; referenced closed owners retained |
| assessment_ownership | Worker/tool source ownership, optionally assigned to a workplace | Document ID; unique assignment/tool or standalone worker/tool |
| shift_timing_templates | Optional reusable work/break timing per project-wide Shift | Shift ID; strict relative-minute payload; membership and clock duration validated under writes |
| task_definitions | Reusable activity names and optional descriptions; no shared numeric values | Project-local definition ID; assessment rows keep independent row IDs and inputs |
| draft_documents | Canonical assessment inputs and original measurement units | Project/document key; model and owner checked |
| draft_metadata | Task-source codec compatibility | Storage marker, not selectable assessment versions |
| saved_assessment_results | One source-bound calculator result per assessment | Exact input/result binding; missing result differs from zero |
| risk_measurements | One current Job/tool value set, optionally with exact task inputs/results | Job/tool key; parent Job and scientific scales validated |
| plant_layout_images | Embedded encoded layout images | Exact Plant identity and validated image bytes |
| plot_station_positions | Shared station anchors | Complete station ancestry |
| plot_worker_markers | Assignment-owned map position/style | Assignment ID, original-image pixels, scale and visibility flags |
| rotation_schemes | Compatible JROT schemes and independent named guided scenarios with accepted-run context | Scheme ID, worker and Job/placement links; current Job values resolved on load |

## Assessment and Job ownership

Each worker/tool may have one standalone assessment. Each workplace assignment/tool may
also have one assessment. Historical observations keep their original assignment after
worker reassignment. A Job is optional for a workplace assessment. There is no New version /
Set current workflow. Scientific inputs and their matching calculation are separate
functional records, not duplicate result archives.

Job risk data use `job_id + kind` as the key. The current measurement holds damage,
probability, recorded unit, optional encoded task source and source-bound per-task results.
Direct values have no task source. Editing task inputs invalidates stale calculations.
Copying a worker/Job source creates independently editable values rather than a live link.
The removed `risk_profiles` and `risk_metadata` tables are absent from the current format.

## Assessment actions and map ownership

Add assessment creates source/ownership and, if necessary, an unclassified workplace
assignment atomically. Confirmed blank replacement retains the existing source identity.
Delete removes only the chosen source/results; its workplace assignment remains.
Transfer creates independent source identities at standalone or active workplace targets.
Approved selected-target replacement, exact result copying and Move-source removal share
one transaction. Historical owners and unselected tools remain. No schema change is needed
for these transfer destinations or replacement consent.

PLOT Job squares reuse assignment positions from `plot_worker_markers`; Jobs do not gain
a separate per-Job geometry table. The same assignment point is used in Individual, Job
and Comparison views. Zoom/pan are session view state, not stored scientific geometry.

## Display and organization data

`project_display_settings.context_expanded` is nullable: NULL means no explicit visibility
choice; 0/1 are collapsed/expanded. Missing optional display storage is read without writes.
An accepted display edit creates the needed private storage through the existing adapter;
main Save publishes it. Gauge/animation/history-limit preferences belong to application
settings, not the project schema.

Organization metadata contain optional ISO dates and recurring Shift times. Plant shifts
in use are derived from distinct shifts referenced by active assignments or Job placements.
Recurring Shift records omit dated incidents/events. Station attributes omit the removed
task/equipment/risk/performance/power/material fields. Plant operational duration is stored
in hours at whole-minute resolution; dates and times are edited through dedicated controls.

## Conversion and compatibility

The desktop opens current full native projects directly. Older full formats use the
separate external conversion tool; the application contains no original-schema decoder.
Conversion preserves compatible source/results and selected Job values, removes obsolete
profile/evidence data and validates ownership. Original files stay unchanged. Converted
copies require an explicit first Save. Lower-level diagnostic formats have separate
capabilities and are not the current integrated full-project contract.

See [API contracts](api_contracts.md), [architecture](architecture.md),
[Transfer](assessment_transfer.md) and [recovery](recovery.md).

## Task names and compatibility

Task rows may contain an optional literal name and a reusable `task_definition_id`,
selected explicitly or linked by accepted Paste. Identical names do not merge existing
definitions. Accepted mapped names reuse a matching entry or create a new one as part
of the same undoable input operation; previews and canceled imports create nothing. References are checked
against the project's `task_definitions` on worker and Job writes. A referenced
identity cannot be removed. Renaming a definition changes its displayed name everywhere;
source fallback text, numeric inputs and saved source-bound result bytes remain intact.
A local name override detaches that occurrence from the definition.

Unnamed task sources keep their existing nested encoding. Named LiFFT/DUET use source
codec 2; named ST uses codec 3 with its explicit recorded direction convention. The outer
assessment envelope and scientific result envelope are unchanged. Format-19 to format-20
conversion adds an empty catalog and updates the native marker, preserving every previous
table value. Current full-format 8–23 conversion is external and produces native 24.
All four maintained native fixtures are now format 24; original fixtures remain unchanged.


## Shift timing templates

Native 21 adds `shift_timing_templates(shift_id, payload)` for the Organization → Shifts
rotation-timing editor. There is at most one current template per Shift. The strict codec
stores full daily duration, ordered shared break offsets/names, positive productive minutes
per work block, equal/unequal mode and the subtract-breaks averaging policy. Clock origins
remain in Shift metadata; no duplicate absolute-clock or calculated piece cache is stored.
Typed project writes validate Shift membership and compatible duration. Both ordinary
hierarchy replacement and combined worker/hierarchy writes enforce these references.

Opening a Shift editor does not create a template. Valid explicit edits use shared project
history; only main Save publishes. Removing a Shift or changing its duration requires
clearing its template first. Moving both clocks by the same amount keeps relative timing
valid. Source tasks/results, Job risks, PLOT geometry and current JROT arrangements stay
independent. New scenarios will own copies; no live rotation linkage exists in this slice.

The external format-20 upgrade adds only this empty table and updates the native marker.
All previous table values, including reusable task definitions and named source/result
bindings, remain exact. Full-format 8–22 conversion is external; current native 24 opens
without it. Existing untimed schemes stay untimed and templates are never inferred.

## Named rotation scenarios — native 22

The existing rotation table now also accepts a strict tagged scenario payload. Compatible
codec-2 rows retain their exact bytes/timestamps; no second rotation/profile table is added.
New plans keep a required local date, exact IDs, name, optional description and independent
current inputs. Older dates/timing remain explicitly unknown. Baseline=None differs from a
saved partial matrix with None cells. Only complete schedules can form accepted run context.

The optional immutable run freezes exact Job sources/results/labels, timing, selected tools,
arrangement, backend, ordered statuses, settings, model version and UTC completion timestamp.
Its fingerprint binds its stored context. Later current edits never reinterpret those values.
Last-viewed ID is an optional project_display_settings column, independent of scientific
inputs; ordinary precision/disclosure updates preserve it. Guarded scenario edits and
selection share project transactions/history and main Save. The 21→23 converter changes only
the marker and preserves every earlier table value. See [scenario contracts](rotation_scenarios.md).

## Guided entry draft capability — native 23

Native23 permits an empty entered observed/proposed matrix before participant selection;
None continues to mean absent. Workerless accepted runs remain invalid. No new tables or
columns are added. The external 22→23 upgrade validates native22 first and preserves every
previous row/timestamp exactly. Older-marker hidden drafts are rejected. See
[guided entry](jrot_guided_entry.md) for the current development entry and remaining integration.

## Weighted guided planning — native24

No table/column is added. Rotation scheme payload codec2 adds strict typed rules and frozen
neighboring-run snapshots; run model2 identifies duration/subset planning. Codec1 rows,
original fingerprints, all other tables and timestamps survive marker-only conversion
unchanged. Native22/23 reject codec2 before migration; current writes require native24.
See jrot_planning.md for score units, supported constraints and source freshness.

## Comparison/rework presentation — native24 unchanged

J07 uses existing frozen run payloads, scenario provenance and shared project edits.
Comparisons, charts and preview discard introduce no stored caches or tables.
Default rework creates a scenario; explicit baseline replacement uses the same record.
