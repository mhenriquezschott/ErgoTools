# F90 — complete migrated-project snapshots

Project > Save As copies the entire migrated SQLite project, including all saved
assessments, workers, hierarchy, jobs, assignments, historical links and profiles.
Validated pending task input is included only in the selected assessment in the
copy. The original is not implicitly saved. Successful Save As activates a clean
session in the copy, updates recent history and releases the original handle;
source/project/assignment identities and recorded units are retained. The new
session has fresh undo history; undo does not cross files.

This follows the accepted plan's default no-implicit-original-save proposal and the
owner's authorization to continue the incremental migration. It differs from the
reference's raw database/file-folder copying: SQLite backup safely includes
committed WAL pages, and pending edits are explicitly included in the new source.
Save As currently retains project metadata. The original Name/Description details
form and external image-folder copying are not implemented by this slice: description
and legacy sidecar content are not yet part of the migrated project format.
This is a usable new-format workflow, not complete legacy Save As parity.

Backup saved project copies persisted data without switching project, updating
recency or committing pending editor text. The menu caption, tooltip and success
message explicitly say unsaved edits are excluded. Saving first is required if
the user wants those edits in a backup. Backup is a separate external-file effect,
not an assessment Undo command or a restore operation.

## Ownership and failure ordering

Application SnapshotProject is an optional typed capability; portable workspace
code owns the transition and the adapter owns filesystem/SQLite work. No new
schema, dependency, renderer behavior or scientific conversion policy was added.

The adapter copies to a uniquely named temporary file in the destination directory,
checks SQLite integrity, validates metadata/catalogs and all source documents, then
optionally saves the current draft into that temporary copy. Its connection closes
before exclusive hard-link publication. Both preflight and publication reject an
existing destination, including a same-file alias or a file created during copying.
The UI asks for a new filename rather than offering overwrite. A filesystem that
does not support hard links reports an error; no unsafe overwrite/partial-copy
fallback is used. Native Windows/macOS/filesystem acceptance remains later work;
crash/power-loss durability is not certified.

Cancelled location selection leaves pending text untouched. Existing destinations
are rejected before accepting input. Invalid input blocks Save As and remains
visible. Valid accepted text is an ordinary edit in the current session even if
a later snapshot write fails. Copy/publication/validation failures preserve the
original session and its edit history. Temporary files are removed on ordinary
errors. A fully published valid destination is retained if final reopening or
workspace postcondition validation fails; no automatic deletion of that potentially
useful user copy occurs. Cleanup errors propagate or produce the existing lifecycle
warning as appropriate.

Activation occurs only after metadata and active-source postconditions pass.
Failed recency writes or original-handle cleanup after activation are separate
warnings, not reversal of successful Save As. Backup releases its copy handle and
retains the original session, preferences and location.

## Validation and visual acceptance

Eleven focused regression cases cover actual three-tool menu Save As, whole-catalog
preservation, selected-source isolation, original protection, picker Cancel,
existing-target rejection, invalid input, saved-only backup with invalid/dirty
input, publication failure/retry, temporary cleanup, committed WAL content,
exclusive publication races, copy-source write failure and recency warnings.
The required native gate passes with 703 tests, 96.62% combined coverage, strict
mypy on 141 source files, lint/format, architecture and both builds.

Native inspection covers English/Spanish populated and disabled/closed Project
menus, selected owned Save As/Backup file pickers, Cancel with pending input,
all three copied-tool main views, Backup retaining invalid text, and Spanish copied/
closed layouts. The minimum 1550 by 1015 preserves native avatar, result cards,
labels, headers and bottom controls. The unchanged native VTK capture method
composes its framebuffer with the Qt window. Pickers use the existing styled
chooser and processed Save/Cancel action icons; stock chooser controls remain as
in the previously migrated chooser. Actual Cancel and filename/suffix acceptance
were checked, along with repeated picker use in ordinary and native-VTK windows.
A nested wait in screenshot automation stalled; captures were separated and use
scheduled callbacks instead. This was not treated as a production defect.

An isolated extracted wheel passes three-tool menu Save As/backup, complete
ownership/catalog preservation, unchanged original sources and renderer cleanup.
All 500 reference hashes and the approved lock remain unchanged. Only synthetic
projects/preferences were used. Evidence: f90_validation.json,
artifacts/f90-check.log, artifacts/project-snapshots/ and the archived
reference/f90-capture.py.txt, f90-picker-capture.py.txt, f90-picker-probe.py.txt and
f90-verify.py.txt.

Next is assessment export, followed by worker transfer and remaining menu/settings
integration. Legacy import/sidecars, final project-details parity, View/Help, full
localization/decimal settings, scientific review gates, remaining overlays/camera
animation, PLOT/JROT and final copied-project/platform acceptance remain. The
former 67% overall estimate remains withdrawn; no reliable replacement percentage
or finish date has been established.

## F99 optional original details step

Integrated full-project Save As now shows the original prefilled metadata form
before accepting task input. Requested metadata is written only into the copy;
source identity/data/units stay intact. Backup and save_as without metadata keep
previous behavior. See [copy metadata and limitations](save_as_details.md).
