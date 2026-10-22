# Localized workplace editor lifecycle — F60

JobWorkplaceDialog now accepts an explicit Language, defaulting to English.
Labels, title, tooltips, hierarchy level names, status templates and error text
use the shared desktop catalog. Stored job names, station paths and shift IDs
are untouched; language selection cannot convert source units or mutate data.
Language is selected when opening the dialog; live retranslation of an already
open modal window remains outside this slice. Count templates retain the original
station(s) convention rather than introducing a general pluralization engine.

The former raw exception popup is replaced with a localized recovery message
preserving local selections and advising reopening after project data changes.
The exception type is logged through standard logging, without raw database
messages, paths or worker data. This is a generic save-error recovery contract;
structured error codes, richer diagnostic routing and application-wide localization
remain future integration work. The original controls and their layout are retained.

JobWorkplaceHost composes the presenter and real modal dialog. It takes explicit
job, language and optional preferred shift, rejects reentrant opening, and returns
a typed JobWorkplaceResult only after accepted Save. The result contains the
persisted view and preferred shift; the owning screen decides how to remember
that shift per project/job. Cancel returns None. Dialog close/deleteLater runs on
both normal and exceptional exits, and the busy guard resets even after loading
or modal execution failures. No source-save prompt or parent state lookup is
introduced: placement changes remain independent of assessment edits.

Four new tests cover Spanish/data separation and localized save errors, matching
translation format parameters, real modal save/cancel/reentry, and load/exec
failure cleanup followed by retry. All 510 tests pass; combined coverage 98.98%.
The host has 100% combined coverage, dialog 99.14%. Ruff/format, strict mypy
(105 source files), architecture and builds pass. Extracted-wheel verification
executes Spanish Save/Cancel through the host. All 500 reference files and the
dependency lock remain unchanged; no schema or scientific formula changed.

Native XCB inspection covers Spanish collapsed/expanded/selected, filtered,
empty-shift and empty-hierarchy states at 720 x 500, plus Spanish and English
error popups. Complete labels, tree and bottom controls fit without clipping.
English collapsed, expanded and minimum-size captures have identical hashes to
F59; original-source comparison captures remain included. No VTK/results region
exists in this dialog. Evidence: f60_validation.json, reference/f60-capture.py.txt
and reference/f60-verify.py.txt.

The host is ready for the owning screen but is not yet called from a fully migrated
Job Management screen or final application menu. Next: migrate the owning job
record/profile workflows and their existing screen wiring. Full worker records,
project setup navigation, integrated assessments, PLOT/JROT, comprehensive copied
project acceptance and platform packaging remain incomplete.
