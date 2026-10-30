# Current native database — format 19

A `.ergprj` file is a self-contained SQLite project. It stores organization, workers,
Job values, assessments, plant images/geometry and production JROT schemes. The integrated
application edits a private working database; main Save publishes accepted data. Backup
copies the durable baseline. Foreign keys and typed cross-catalog validation protect
relationships; multi-record edits use transactions with rollback.

## Functional tables

There are 15 functional tables plus optional `project_display_settings`. No risk-profile,
evidence/currentness or assessment-version tables participate in the current full format.

| Table | Current purpose | Identity / relationship |
|---|---|---|
| project_metadata | Project ID, title, default units and native compatibility marker | One typed metadata record; file version is not an assessment version |
| project_details | Description, creation time and language | Validated project details |
| project_display_settings | Optional display precision/default-unit and assessment disclosure choices | One optional record; source measurements are not rounded by display changes |
| work_catalog | Workers and Plant/Section/Line/Station/Shift organization | Typed hierarchy with exact scoped station and shift identities |
| jobs | Activity definitions | Job ID; names/descriptions and active state |
| job_placements | Jobs available at an exact station/shift | Placement ID plus Job and workplace membership |
| worker_assignments | Worker workplace/shift, with optional Job placement | One active owner per worker/context; referenced closed owners retained |
| assessment_ownership | Worker/tool source ownership, optionally assigned to a workplace | Document ID; unique assignment/tool or standalone worker/tool |
| draft_documents | Canonical assessment inputs and original measurement units | Project/document key; model and owner checked |
| draft_metadata | Task-source codec compatibility | Storage marker, not selectable assessment versions |
| saved_assessment_results | One source-bound calculator result per assessment | Exact input/result binding; missing result differs from zero |
| risk_measurements | One current Job/tool value set, optionally with exact task inputs/results | Job/tool key; parent Job and scientific scales validated |
| plant_layout_images | Embedded encoded layout images | Exact Plant identity and validated image bytes |
| plot_station_positions | Shared station anchors | Complete station ancestry |
| plot_worker_markers | Assignment-owned map position/style | Assignment ID, original-image pixels, scale and visibility flags |
| rotation_schemes | Production JROT arrangements, scope and optimization provenance | Scheme ID, worker and Job/placement links; current Job values resolved on load |

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
The removed `risk_profiles` and `risk_metadata` tables are absent from format 19.

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
