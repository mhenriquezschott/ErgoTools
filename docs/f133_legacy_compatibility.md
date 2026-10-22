# Legacy saved JROT compatibility — F133

All seven original saved schemes now map to the established typed JROT models,
including 45 frozen target records, 179 assignment cells, exact scopes and original
manual/single-tool/all-tool provenance. Existing forms load every copied scheme in
EN/ES; actual CBC and HiGHS/Apply pass on the small saved source scheme. Next:
explicit atomic destination conversion with complete source evidence preservation,
then integrated copied-project validation. ST direction choice is still pending.

Source mapping: rotation_repository.py load_rotation_scheme and version-eight
RotationScheme/RotationSchemeScope/RotationTarget/RotationAssignment. Scheme IDs,
names/descriptions, scope contexts and grid dimensions remain exact. Worker order
uses original SQLite NOCASE ASCII folding and block_index stays zero based. Target
row IDs map to opaque RotationTarget keys without parsing display text. Exact
assignment/placement/profile versions remain frozen; current successors are never
substituted. Closed assignments and retired approved risk versions remain valid.
Raw original rows retain database IDs, timestamps and fields for conversion evidence.

The reader rejects holes, mismatched dimensions, worker-owner changes across
blocks, foreign/ambiguous cell targets, invalid scope, draft profile references
and false optimization provenance rather than repairing saved schemes. Source
mode/primary_tool_id are retained as manual, single_tool/LiFFT or all_tools/None;
no mode inference from risk scores or scheduling layout. Source records contain
four manual, one single-tool and two all-tool schemes. All linked catalogs are
validated with the existing domain rules. No solve or save occurs during reading.

Seven focused tests characterize the three modes, frozen retired/closed links,
shape errors, conflicting ownership and invalid risk/provenance. Copied-source
native checks then load all seven schemes through the actual combo activated
signal, confirming each complete grid and scope. A read-only snapshot host feeds
the existing view and deliberately rejects save/delete; no operational import or
main-application legacy opening is claimed. CBC and HiGHS/three-tab comparison/
Apply run against recorded job risk evidence on TEST-All-2x3 without persistence.
The same native controls/backend checks pass from the independently extracted wheel.

22 native captures inspected: all seven saved forms at minimum size in EN/ES,
large eight-block and workplace-scoped forms enlarged/scrolled, actual CBC results
and HiGHS comparison with the ST tab selected. Both panels, toolbar and bottom
controls remain visible. Wide/tall tables intentionally scroll like the source;
fixed headers remain visible and existing narrow recommendations elide. No avatar
belongs to original JROT. This checkpoint changes data adapters, not UI code;
these captures exercise copied saved data and do not establish final whole-app parity.

The full read/reconciliation path now accounts for 194 assessment summaries and
3,577 task rows, four plant image companions, mapped station/assignment positions,
raw older display metadata, and seven saved rotations. No source records or cached
results were rewritten. Complete publication is not implemented yet. The owner's
ST choice (displayed directions with calculation gated, or executed formulas with
changed labels) is required before converting those source indices. Other scientific
review gates remain unchanged. Overall percentage/finish date remain unvalidated.

Validation: 1046 tests pass; 96.69% coverage. Ruff/format, strict mypy, architecture and builds pass. Extracted-wheel compatibility checks pass. All 500 reference hashes and the dependency lock are unchanged. No UI change. Evidence: f133_validation.json and artifacts/f133-*.log.
