# M04 complete — project lifecycle and original-data compatibility

All three fixed M04 criteria are verified. **85.25/100 overall; 4/12 milestones
complete; 11.25/26 remaining-baseline points earned, 14.75 still to earn.**
M04 earns its fixed 2.5 points. M05 is next, not started. No milestone/weight or
scope expansion; one comparison and one bounded correction batch completed.

## Changes and owner decision

Original New now starts editable unsaved work without destination/details prompts.
The existing SQLite ports use owned temporary backing, excluded from recent
projects. First Save collects the original destination and Name/Description,
then exclusively publishes and adopts the copy. Cancellation or failed writes
retain work. Successful Save/Open/Close releases backing after its repository.
Pre-save management/PLOT/JROT/export availability follows the original lifecycle.

Open now adopts a validated empty project and its real catalogs without inserting
an assessment. Worker/Organization/Jobs, Properties, Save As, backup and Close
remain available; nonempty projects still require exact assessment selection.
Existing atomic source/result Save and failure paths are reused, not redesigned.

The owner resolves legacy worker units: interpret the raw numbers using the
project's declared Metric/Imperial setting, normalize editable destination values
to cm/kg, and retain exact raw archive/originals. No added import decision dialog.
An Imperial height 72.5 and weight 150 becomes 184.15 cm and 68.0388555 kg;
display back in Imperial restores 72.5 in and 150 lb. Metric numbers remain
unchanged. Missing/zero values remain missing/zero. No claim is made that unknown
historical entry units can be recovered. The comprehensive project declares
Metric, so its ten nonempty worker measurement pairs are numerically unchanged.
New-format body fields already use canonical units and display-only conversion.

## Acceptance evidence

- M04.1: prior 136 packaged lifecycle/transfer/export tests; 49 current focused
  cases including first-Save modal Cancel, failure/retry, temporary cleanup,
  recent exclusion and empty Open/backup/Save As/reopen. Built-package native
  New/first-Save Cancel/Save/empty Open and management modal actions pass.
- M04.2: reuse F150/F153 all-tool source/result atomic Save/Save As/failure
  evidence; required full regression gate passes after these lifecycle changes.
- M04.3: built-package disposable comprehensive conversion, archive/backup and
  independent reopen; all 194 original summary identities/damage/full percent
  precision/recorded units match CSV, including BOM/CRLF. Focused Metric/Imperial
  fixtures prove normalization occurs once and raw archive/original bytes survive.
  F138 full typed source/map/rotation identity evidence reused.

Full gate: **1,162 passed; 96.44% combined coverage**. Ruff check/format, strict
mypy, architecture and wheel/sdist build pass under approved Python 3.13.14.
All 500 reference manifest hashes and the exact dependency lock remain unchanged.
Current wheel SHA and evidence paths are in m04_validation.json.

Eight new individual native captures inspected: EN unsaved 1550×1015, ES unsaved
1800×1200, empty/populated first-Save details, ES first-saved 1550×1015, empty Open
1550×1015, empty Worker and Organization dialogs. Full avatar viewport, result
cards, labels, context/footer and bottom controls fit; native VTK is composited
into owned CPU Qt captures with adjacent pixels checked unchanged. Current copied
EN/ES Properties and prior source-derived Details/Save As/Transfer comparisons
also remain valid. No layout redesign or broad UI parity claim is made here.

Known Spanish Transfer explanatory text remains assigned to M09. Full shared
localization/unit/resize/VTK matrix remains M09; PLOT/JROT/final cross-feature
acceptance remains in fixed M05–M12. Windows/macOS VM evidence is deferred under
CR001, not reported as passed. No additional work was added to M04.
