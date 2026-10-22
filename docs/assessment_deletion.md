# F86 — saved assessment deletion

The reference `main.py` LiFFT/DUET/ST Delete handlers were reviewed read-only. They
confirm removal of saved results and tool association for a worker/station/shift,
then reload the tool. Reset remains a separate input-clearing operation.

The migrated format stores assessment source documents and versioned ownership,
not the legacy result tables. Delete therefore removes the open source document and
its ownership row. The confirmation retains the reference Data Exists/Yes/No
interaction, defaults to No, and adds explicit version/unsaved-edit scope. This is
a necessary versioned-format clarification, not deletion of all historical versions
at a matching workplace. Other versions/tools/assignments and all worker/job/workplace
catalogs remain intact. Deleting a current version leaves no current version in its
group; no older assessment is automatically promoted.

No leaves pending input, source and history intact. Yes explicitly authorizes
abandoning unsaved edits, including invalid pending text, and commits deletion
immediately. It does not save those edits first and does not add an Undo command.
After success the active session is released, results/overlays are cleared, the
selected tool's empty layout/captions remain, and source-specific controls are
unavailable. Existing assessments can be loaded explicitly via another tool/worker
or Open. New source creation is always explicit; remaining empty-state creation and
menu/settings integration are the next planned workflow work. Unbound/unsupported
sources keep Delete unavailable. Deleting the last saved document leaves the project
and its catalogs intact and reopenable.

`DeletableHistoryRepository` exposes one portable atomic operation.
`ProjectWorkspace.delete_active_assessment` applies it to the confirmed active
identity, releasing the session only after success. The SQLite adapter owns
`BEGIN IMMEDIATE`: saved history comparison, exact owner/source deletion and
position compaction commit together or roll back together. Compaction preserves
history order and permits future insertions without unique-position collisions.
No schema, library, Python or environment changes were required.

Five focused cases cover the three tool-button workflows (No, injected storage
failure, Yes, exact persisted scope, retained older noncurrent version, localized
confirmation/caption and explicit other-tool recovery), failure between owner and
source deletion using a SQLite abort trigger, history position compaction/future
insertion, stale/missing requests and last-source deletion/reopen. Visual checking
found and corrected empty DUET/ST cards reverting to LiFFT; the sidebar now receives
the selected empty tool identity separately from an absent source.

The required gate passes with 678 tests and 96.82% combined coverage,
strict mypy on 139 source files, lint/format, architecture and both builds. Native
captures under `artifacts/assessment-deletion/` include actual confirmation,
No/pending and Yes/empty states for all tools; ST uses Spanish. At 1550 by 1015,
no new clipping was observed around the native avatar, result cards, labels or bottom
controls. Actual VTK framebuffers are composed using the F78 method. Qt stock Yes/No
button labels remain those of the current baseline; application confirmation text
is localized. Full Qt stock-dialog language integration remains a broader acceptance
item. This is scoped visual acceptance, not final whole-app UI parity.

The independently extracted wheel passes actual default-No/refusal/Yes operations
for each tool, reopened persistence, untouched other ownership/catalogs, empty states
and renderer cleanup. All 500 recorded reference hashes and the approved lock remain
unchanged. Evidence: `f86_validation.json`, `artifacts/f86-check.log`, archived
`reference/f86-capture.py.txt` and `reference/f86-verify.py.txt`. Only synthetic
projects were deleted in testing; no operational dataset or reference checkout was
modified. Scientific review gates remain unchanged.
