# Historical assessment persistence — F45

This checkpoint implements the storage portion of the documented worker/job
migration. AssessmentProjectFile.create_historical explicitly creates version-six
projects with assignment-scoped assessment ownership. Older formats and the default
version-two factory remain unchanged; no existing project is upgraded automatically.

create_historical_assessment commits a new source and its AssignmentAssessment
record under one BEGIN IMMEDIATE transaction. Existing history, current hierarchy,
assignment membership and source model are validated. Duplicate document/version/
current-owner conflicts and SQL errors roll back both records. Closed assignments
may retain assessments; no activity or date filter moves ownership to a successor.

load_history reads hierarchy, jobs and source links in one SQLite snapshot.
Opening a project also rejects missing sources/assignments, model mismatch,
malformed ownership flags and mixed context-only ownership. Tables preserve record
order and enforce version/current uniqueness; typed adapter checks enforce the
remaining model, status and cross-table references. Direct SQL writes are unsupported.

Job replacement now accepts an injected historical-reference guard, executed under
the existing write lock before replacement. Referenced assignments cannot disappear
or change worker/workplace. Once classified, their placement ID cannot change, and
that placement cannot change job ID or workplace. Closing a row, creating a successor,
updating dates/notes/activity and renaming job display metadata remain allowed.
Initial classification of an unclassified referenced row is also allowed, matching
the reference transition semantics. A rename does not snapshot old display text.

Version six disables the context-binding API explicitly rather than pretending
worker/workplace/model identifies a historical assessment. It rejects any populated
context-only binding table. Existing version-three/four/five APIs remain unchanged.
The current selector/workspace context flow therefore needs an assignment-aware
capability before it can use version six; this is an opt-in repository feature,
not an upgrade to the temporary desktop harness.

No API yet changes which existing version is current, attaches an existing source,
deletes historical assessments or imports legacy records. Historical assessed-at
metadata, calculated result snapshots and complete legacy assessment lifecycle
behavior remain outside this ownership slice. Source content stays editable through
the existing draft API; ownership identity protection is not an immutable audit log.

Eleven new tests cover separate historical/successor assessments, protected rows,
missing owners, version/current conflicts, model mismatch, injected late SQL failure,
reopen corruption detection, initial classification, incompatible context binding,
older formats and closed handles. All 446 tests pass; combined coverage 98.93%,
new storage module 97.18%. Ruff/format, strict mypy (98 files), architecture and
builds pass. An extracted-wheel smoke repeats creation, reassignment, reopen and
referenced-row protection. See f45_validation.json. All 500 original files and the
approved dependency lock remain unchanged. No scientific or visual change occurred.
