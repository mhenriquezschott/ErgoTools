# Current Job risk schema — native format 19, 2026-10-20

The owner removed Job risk-profile versions, evidence and approval/current/retirement.
One `risk_measurements` row per Job/tool is authoritative. `risk_profiles` and
`risk_metadata` are absent. All other functional tables and assessment ownership stay
unchanged. This section supersedes the historical inventories below.

| Column/key | Existing functional purpose |
|---|---|
| job_id + kind PK | One current LiFFT, DUET or ST value set per real Job; kind is a stable enum |
| job_id FK → jobs.id | Parent ownership; explicit Job deletion cascades its current risks |
| damage | Current dimensionless aggregate damage; NULL before calculation or when absent |
| probability | Current outcome on the 0-100 percent scale, zero distinct from absent |
| unit | Recorded calculation unit label, independent of current display/default units |
| source | Optional exact encoded task inputs and units/convention; NULL for direct entry |
| task_results | Versioned codec envelope with canonical source digest and exact moment/damage/contribution triples; NULL before calculation/direct entry |
| position | Stable tool-row ordering within a Job, unique with job_id |

Task inputs and task outputs have distinct functional purposes. They are the one current
calculator state, not alternate assessments or duplicate historical results. Numeric
edits clear stale aggregate/per-task outputs. Source/result shape and tool identity are
validated before publication. Surviving Job rows are upserted in place so assignment or
placement replacement cannot cascade away current risks. Job metadata/risks and affected
rotation-provenance invalidation share one transaction with rollback.

Rotation payload version 2 stores Job/placement target identities and worker arrangements;
it has no risk-profile ID or numerical risk snapshot. Saved schedules resolve current
Job values. Changing relevant numeric values retains arrangements and marks previously
optimized provenance manual; optimization requires explicit rerun. External conversion
keeps uniquely selected prior Job measurements, removes obsolete profile/evidence rows,
rewrites opaque schedule keys without changing arrangements, and fails ambiguous ownership.
Worker source/result payloads from formats 14-18 stay exact. Maintained fixtures are updated
in place; original files/reference checkout stay untouched.

See Job contract. Historical acceptance and
schema descriptions below document earlier checkpoints, not current profile functionality.

---

# Organization field cleanup — format 18, 2026-10-19

Native format 18 removes six Station attributes (task_description, equipment_used,
ergonomic_risk_level, performance_metric, power_consumption, materials_used) and
Plant number_of_shifts. Dates are canonical ISO calendar dates; operational_hours
is a daily decimal-hour duration in whole minutes from 0 to 24. The UI derives
Shifts in use from distinct active Job placements or worker workplace assignments
in that Plant. Unused project Shift definitions do not count; no new table is added. External formats 8–17 convert on a private copy. Existing
format-14/15/16/17 source/result payloads remain exact. Current native test projects
were updated in place. See acceptance.

---

# Shift metadata correction — format 17, 2026-10-19

The owner removed `incidents_reported` and `ergonomic_risk_events` from recurring
Shift records. Format 17 retains the same SQL tables and keys; those two attribute
pairs are absent from `work_catalog` JSON and rejected by the domain contract.
Format 16 requires the existing external conversion workflow, which removes exactly
these attributes without recalculating or changing unrelated rows. Original legacy
files remain unchanged; their converter now excludes these fields. Both maintained
native fixtures and the four-worker workflow file were updated at their existing
paths. See acceptance.

---

# Current format-16 database tables and their functional purpose

This inventory describes the complete current full-project schema: 17 required tables
and an optional project_display_settings table when display precision is stored. There is no
assessment-version table, flag, status, number or extra-value archive. One assessment per assignment/tool and one standalone assessment per worker/tool
are enforced by both domain values and SQLite. Context-bound older
diagnostic formats have their own actually used binding table; it is absent from the
current full-project schema. Each JSON/BLOB value is validated through its owning adapter.

| Table | Functionality | Identity and relationship protection |
|---|---|---|
| assessment_ownership | Direct worker/tool ownership with optional real workplace assignment | document_id PK; required worker_id; optional assignment FK; unique assigned and standalone owners |
| draft_documents | Canonical task inputs and recorded measurement units | project_id + document_id PK; checked against ownership and tool |
| draft_metadata | Task-source storage/codec compatibility marker | One validated format/version record; not assessment versions |
| saved_assessment_results | Sole calculator output bound to the exact saved inputs | project_id + document_id PK; source/result matching verified |
| jobs | Job definitions used by placements and risk profiles | Job ID PK; referenced identities protected |
| job_placements | Job availability at an exact station and shift | Placement ID PK; Job/workplace membership validated |
| worker_assignments | Worker doing a Job at a workplace/shift | Assignment ID PK; one active row per worker/context; closed referenced owners retained |
| work_catalog | Workers and Plant/Section/Line/Station/Shift organization | Singleton typed hierarchy; referenced worker/workplace membership validated |
| plant_layout_images | Embedded plant images for PLOT | Plant PK; image bytes validated; no sidecar dependency |
| plot_station_positions | Saved station geometry used by PLOT | Exact station ownership validated against hierarchy |
| plot_worker_markers | Saved PLOT marker geometry for worker assignments | Assignment PK; referenced assignments validated |
| rotation_schemes | Saved JROT grids, scope and optimization provenance | Scheme ID PK; workers/targets/frozen profiles validated |
| risk_profiles | Original Job risk-profile approval/current selection used by JROT | Profile ID PK; Job relationship and lifecycle validated; its original versions remain functional |
| risk_measurements | LiFFT/DUET/ST risk coefficients for each Job profile | Profile/tool identities and scientific scales validated |
| risk_metadata | Risk-catalog codec and project ownership marker | Singleton PK; format/version and exact project checked |
| project_metadata | Project identity, title, default units and file-format compatibility | Singleton format metadata; version here is the file schema, not assessment version |
| project_details | Description, creation timestamp and project language | Validated project detail record |
| project_display_settings | Owner-requested project-specific displayed decimal precision | Validated single settings record |

The source/result split stores inputs and their calculated output, never multiple
results for an assessment. File/codec markers and original Job risk-profile versions
are required by compatibility and approved optimization workflows; they are unrelated
to the removed duplicate-assessment feature. Foreign keys are enabled on repository
connections. Cross-feature and JSON relationships are also validated by the domain and
repository, with rollback on failed catalog changes.

The external upgrade replaces assessment_history with assessment_ownership and removes
the unused full-project assessment_bindings table. It changes only the verified empty
extra draft and schema bookkeeping in current format-14 conversions. Original files
remain unchanged outside the current format-16 copies. See single_assessment_ownership.md
for the exact rejection/publication/data-preservation policy and acceptance evidence.

Format-16 ownership, optional Jobs, migration and rollback: current contract. No new business table is added.


## Editing boundary — 2026-10-18

The same format-16 tables are edited through a private in-memory native connection
while a project is open. Only the main Save commits the complete accepted state to
the .ergprj file. Undo checkpoints, partial JROT drafts and creation-consent markers
are session-local application state, never additional business tables or assessment
versions. See [single project Save](single_project_save.md).


Shift time-editor follow-up, 2026-10-19: start_time/end_time remain optional clock
strings in existing organization metadata. The following-day control is inferred
from complete clock order (end <= start for the following day) and is not serialized.
No new table, column, redundant day attribute, schema/codec version or stored UI
placeholder is introduced. Unspecified remains None; actual midnight remains 00:00.
