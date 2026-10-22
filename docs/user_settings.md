# F7 — user settings and recent documents

Completed 2026-09-28 without dependency changes. `application/settings.py` defines immutable UserSettings and a SettingsStore port. Language now belongs to this application contract; presentation.localization re-exports the same enum so existing imports and translator behavior remain compatible. Domain calculations never import presentation language settings.

## Preferences and recent history

Defaults are English and imperial, consistent with the initial reference defaults. These are user defaults only: existing drafts retain their own explicit unit metadata. Changing settings neither converts nor relabels stored values and does not modify document history. UI application of new settings remains pending.

Recent locations are immutable, opaque caller-normalized strings. `remember` moves a successfully opened location to the front, removes an exact duplicate and retains at most ten entries (a local implementation choice, not a legacy format requirement). `forget` explicitly removes an entry; `clear_recent` keeps language and units. No method opens, resolves, migrates, deletes or checks the existence of listed files. Missing/moved locations stay visible until the owner forgets or replaces the entry. Symlink/case/relative-path normalization and missing-file UI are future platform-adapter concerns. Do not call remember before a successful open/save workflow.

## Settings file

`infrastructure/settings_store.py` receives an explicit user-scoped path and performs no constructor I/O. The caller chooses the platform directory and creates it deliberately. JSON version 1 has exactly format=`ergotools.user-settings`, version=1, language, default_units and recent_documents. Unknown/missing/extra fields, unsupported enums/versions, duplicate members/locations, blank/oversized history and invalid UTF-8 are rejected. A missing file returns defaults without writing anything; corrupt or inaccessible files do not silently become defaults. Loading settings reads only the settings file, never the listed projects.

Save first validates any existing settings file to avoid overwriting an unsupported/corrupt version. It writes a uniquely named temporary file beside the destination, flushes/fsyncs it, then uses os.replace. Failures before replacement retain the previous file and attempt temporary-file cleanup; successful replacement has no subsequent cleanup I/O that could misreport it as a failure. Missing directories are not silently created. File permissions for the replacement follow the temporary-file creation policy. This is a single-writer adapter with no lock, merge, recovery/reset UI, directory fsync guarantee or certified power-loss durability. Cleanup can itself fail under filesystem faults; such errors propagate for caller handling. No real user settings path is wired or altered in this slice.

## Verification

Twelve new tests cover default/no-write behavior, language/units/history round trips, unchanged assessment units, bounded recency and exact deduplication, forgetting/clearing, invalid settings, immutable input ownership, corrupt/future formats, UTF-8 failure, injected replacement and fsync failures, retry, absent parent directories and retention of missing/invalid project locations without opening them. All 94 tests pass; combined coverage 99.08%, new modules 100%. Existing risk/Spanish catalog tests still pass after moving Language. Ruff/format, strict mypy (27 source/tool files), architecture and package builds pass. `f7_validation.json` records isolated package/source/lock evidence.

Next: project metadata and connection ownership, integrating successful open with recent-history updates. A settings-write failure after a successful document open must be reported separately, not undo the open or falsely report that the project failed. Save As policy needs confirmation before that workflow. No GUI, scientific calculation, operational database or dependency change occurred.
