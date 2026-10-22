# Assignment-aware presenter — F48

AssignmentSelector connects saved classified assignments to the historical
workspace selection/creation capabilities. This is the presentation-logic step
of worker/job workflow migration; it does not add Qt controls.

Refresh obtains a workspace JobSnapshot and publishes an AssignmentCatalog.
Options retain explicit assignment IDs and job display metadata. Preparing a
request requires an exact eligible assignment for the selected worker/model;
there is no fallback to a workplace label or the first available assignment.

Active assignment and placement flags govern eligibility; job activity and dates
remain excluded, matching the established assessment lookup behavior. Closed
assignments are excluded from this active-work presenter. Historical browsing can
use the explicit assignment-aware workspace path separately.

Catalog and request object identities reject equal copies, foreign callbacks,
refreshes and project-handle changes. Requests also capture the active session
and revision; source edits invalidate prepared requests. Workspace job refresh or
replacement invalidates the published catalog. Failed presenter refresh clears old
authority before I/O. Success consumes the request; cancellation or recoverable
failure permits retry if its source/catalog remain current.

create validates model identity before workspace actions and accepts explicit
document/version/currentness inputs. It creates draft status; it never demotes
another current version or allocates version numbers. Selecting afterward resolves
the saved current version, which need not be the newly created noncurrent document.
The host must resolve pending widget text before preparing a request.

These are in-process freshness guards, not live subscriptions to external SQL
changes. Options reflect the last saved job snapshot. Repositories still validate
history, membership and conflicts on actual operations, but selection does not
lock assignment activity across processes. Refresh policy and final UI eligibility
checks remain host integration work. Worker captions/hierarchy options are separate
from this job snapshot and are not claimed as one combined database snapshot.

Four integration scenarios cover active/closed eligibility, missing and foreign
worker choices, copied/stale requests, dirty consent, changed drafts, job refresh,
failed refresh, project close, model mismatch, creation failure/retry, current
conflicts and explicit noncurrent creation. All 455 tests pass; total coverage
98.97%, new presenter 100%. Ruff/format, strict mypy (100 files), architecture and
builds pass. Extracted-wheel selection/creation also pass. All 500 original files
and the dependency lock are unchanged; see f48_validation.json.

Next: adapt the classified-context dialog to assignment-aware requests and compose
host pending-text/dirty-choice handling, with required native visual checks. Current
version transitions remain a separate lifecycle task. No schema, dependency,
scientific or UI change occurred in this checkpoint.
