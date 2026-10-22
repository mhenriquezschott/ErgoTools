# Legacy historical sources and cached evidence — F130

All 191 normalized historical assessments and 3,532 task rows in the comprehensive
copy now have a tested read-only compatibility mapping, with exact assignment/
version/current/status identity, units, source inputs, notes and cached evidence.
Next: reconcile three older records absent from normalized history, map PLOT/JROT
assets/provenance, and implement explicit atomic destination conversion before
integrated copied-project UI validation. Raw ST selector interpretation still
requires the documented scientific/UI decision; no implicit conversion is made.

Source mapping: schema_migrations.py IndividualAssessment and LiFFTAssessmentTask/
DUETAssessmentTask/ShoulderAssessmentTask, with main.py save/load/calculation paths.
Historical numeric IDs remain source_id; deterministic document IDs use
legacy-assessment-<id>. Assignment ownership is never reassigned to a worker's
current job. Existing AssessmentHistory validation rejects ambiguous current
versions and missing owners. Source task_index determines ordering and stable
legacy-task-<index> identity; gaps and empty rows are retained rather than packed
or deleted. The full source mapping is validated on one read-only transaction.

LiFFT and DUET map to existing immutable drafts. Arm/load retain their recorded
Metric or Imperial source meaning; DUET retains optional original unit evidence
without inventing physical conversions. Unknown physical units fail explicitly.
The comprehensive database stores 2,802 exact empty-string input fields in numeric
DUET/ST columns. The original main.py saves untouched line-edit text this way.
Only that exact input representation maps to None; zero remains zero, and other
malformed numeric text fails. Immutable original_tasks retains every original
row/storage value for future explicit conversion and evidence preservation.

Original Shoulder type_of_task is a UI selector index, not TstDirection. main.py
loads it into the combo and swaps 1->2 and 2->1 before calculation, conflicting
with its visible labels (already documented in F21/F79). LegacyShoulderSource
therefore retains selectors 0/1/2/None explicitly with the original numeric inputs.
It does not create a TstDraft, silently change labels, resolve the scientific
ambiguity or bypass the existing ST review gate.

Cached total damage/probability, task moment/damage/share, assessed time and notes
are separate evidence on LegacyAssessment. Reading never recalculates them,
marks them fresh, promotes an assessment or saves a destination file. Blank/zero
cached evidence remains distinct. Every normalized assessment and task field was
compared directly with source values, including immutable raw ST selectors.

The source also retains older WorkerStationShiftErgoTool/LifftResults/DuetResults/
TstResults tables: 194 summaries and 3,577 task rows. Three context/tool records
are absent from the normalized history, explaining 45 extra old task rows.
They are not silently merged into the 191 normalized records. A complete import
must reconcile this older-table evidence explicitly, along with PLOT/JROT data,
extra source metadata and ST interpretation, before publishing a converted file.
The audit records counts without altering the original or pretending conversion
is complete. See f130_legacy_audit.json for exact counts/source hashes.

Focused synthetic regression tests cover closed/superseded/current ownership,
three tool sources, mixed units, gaps, blank/zero/empty-string distinctions,
separate cached results, wrong-model tasks, unknown selectors/units and malformed
numeric storage. The independent extracted wheel reads the complete copied
history and all raw evidence without importing the editable source package.
No application UI changed; F127 native integrated UI evidence remains applicable.
Overall completion percentage and finish date remain unvalidated.

Validation: 1030 tests pass; 96.71% coverage. Ruff/format, strict mypy, architecture and builds pass. Extracted-wheel compatibility checks pass. All 500 reference hashes and the dependency lock are unchanged. No UI change. Evidence: f130_validation.json and artifacts/f130-*.log.
