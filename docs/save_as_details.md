# Original prefilled Save As details — F99, 2026-10-06

Integrated Project > Save As now shows the original Project Details form after
choosing an exclusive destination. Its Name and Description controls are prefilled
from saved metadata; missing older descriptions display blank. The same source-
derived component used by New retains automatic sizing, native standard buttons,
field order and English/Spanish captions. Literal Unicode/multiline values are
retained. Cancel closes without parsing pending assessment input, changing source
history, preferences, location or project metadata. Existing destinations are
rejected before opening the form or accepting edits.

After acceptance, the host trims the optional name (blank falls back to the
copy's filename stem), retains the description and records the copy's current
local second-precision timestamp, UI language and display-unit default. These
follow the reference src/main.py:saveFileAs behavior. Original saved assessment
values/source units and worker/job/ownership relationships remain unchanged;
only the currently accepted active draft is included as already defined by F90.
A fresh copy session starts clean, the header displays its new stored title, and
Properties displays its details. The original database is never saved by Save As.

## Copy-only storage boundary

ProjectWorkspace.save_as accepts optional immutable requested metadata. The
optional MetadataSnapshotProject port supplies copy-only editing; the workspace
rejects project-identity changes and validates the returned metadata and source
before activation. Existing callers omitting metadata retain unchanged snapshot
behavior, including Backup. No Qt, paths or SQL enter the portable core.

The SQLite adapter backs up the complete database into the existing temporary
same-directory copy, then transactionally writes requested details there. Full
format-seven projects gain project_details and version eight in the copy only;
format-eight copies replace their details. The source keeps its previous version
and bytes. Assessment source replacement and validation also occur before the
existing exclusive publication step. Failures roll back/remove the temporary
copy, retain the old active session/history and never replace destinations.
As previously documented, final reopen failure after successful publication may
retain a valid published copy; filesystem hard-link/power-loss/platform acceptance
limits are unchanged.

Earlier partial formats (one through six) retain their ordinary Save As capability
without this metadata editor or implicit application-schema migration. The
integrated host enables the details step only for full job-risk project formats
seven/eight. The temporary standalone harness retains its unchanged copy behavior.
Backup remains saved-data-only, preserves metadata exactly and leaves the active
project untouched. Source identity, ownership, source units and scientific gates
are unaffected; changing the copy's default units only affects future assessments.

This supersedes F90/F98's statement that integrated Save As always preserves
creation metadata. Direct save_as without metadata and Backup still do. Exact
reference unsaved-New/first-Save timing, XML/sidecar copying, final localization
and F95 native message parity remain unfinished. Blank title fallback is the
existing explicit nonblank-title contract rather than the reference empty-title
behavior. No dependency or packaged asset change occurred.

## Validation

Nine new focused cases in tests/test_save_as_details.py cover actual prefilled
modal Cancel on all three tools with invalid pending text; accepted Spanish copy
metadata/defaults with source values, ownership/catalogs and original bytes
preserved; format-eight literal prefill and blank-name fallback; injected SQL
failure after details insertion; foreign identity and partial-schema rejection.
Earlier snapshot tests now supply the new details step and validate requested copy
metadata. Required gates pass: 769 tests, 96.34% combined coverage, Ruff check/
format, strict mypy over 156 source files, zero architecture violations and both
builds.

Native xcb captures in artifacts/save-as-details compare the extracted reference
saveFileAs form with its migrated prefilled English/Spanish, edited and expanded
states. Copied Properties and the integrated VTK/cards/bottom controls at 1550 by
1015 and 1920 by 1200 were inspected. The same-platform/style/DPI comparison uses
source extraction and synthetic data; it is not full application acceptance.
The isolated extracted-wheel check covers actual prefill/Cancel, format-seven
copy upgrade, unchanged original bytes/ownership, edited details, Backup/reopen
and second format-eight Save As. Its synthetic tool switches explicitly discard
prior dirty test edits; no real user consent is bypassed in production.
All 500 reference hashes and the approved lock remain unchanged. Evidence:
f99_validation.json, artifacts/f99-check.log and archived
reference/f99-capture.py.txt / reference/f99-verify.py.txt.

Next is PLOT's original plant/layout selection and saved-layout loading workflow,
starting from plant_layout.py, plotviewerdialog.py and plot_position_repository.py
rather than screenshots. Existing architecture and final integrated UI targets
remain. Overall completion percentage and finish date remain unvalidated.
