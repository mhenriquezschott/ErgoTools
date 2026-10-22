# M07 accepted — JROT schedule and scope

M07 earns its fixed **1.50 points**: **90.50/100**, 7/12 milestones complete.
M08 was authorized in the same batch and is reported separately.

M07.1 closes the existing original worker/job scope chooser and grid with the
required application-owned history. Partial cell edits, Delete batches, applied
and cleared scope are reversible without SQL or catalog rereads. Save is atomic,
not an edit; failures retain drafts/history. Cancel, navigation, search, New and
confirmed deletion retain original workflows and reset the scheme-local history.
Frozen worker assignment/profile/placement identities survive restoration and
independent reopen. F121/F123 persistence/pool tests continue to verify closed
assignments, retired profiles, per-column target uniqueness and duplicate captions.

M07.2 closes R006 at **1480x740**, retaining original sizes/positions. Complete
4/6/8/16 count summaries fit in English and Spanish; tooltips list full names.
The expanded scope chooser retains all **16 exact selected workplace contexts**.
Pending selection performs no write, Apply is one command, and Undo/Redo/Cancel
restore the correct pool and links. No formula or unit conversion changed.

Full batch gate: **1,178 tests, 96.40% coverage**; Ruff/format, strict
mypy, architecture and both builds pass. Ten focused new history regressions
cover partial edits, one-batch Delete, no-op/branching, save failure/clean markers,
scope restoration, native typing ownership, provenance and owned-solve boundaries.
Extracted-wheel focused JROT and native comprehensive-copy EN/ES acceptance pass.
All **22 batch captures** were inspected; main minimum/enlarged panels, scoped
summary, original chooser and fixed bottom controls remain usable. F122/F124
original-source geometry evidence is reused for unchanged controls. The localized
Edit menu is the approved Undo/Redo addition, not a visual redesign.

See [history contracts](jrot_history.md), [bounded review](m07_m08_review.md),
[validation](m07_validation.json), and `artifacts/m07-m08-native/verification.json`.
Noncritical decisions are R012. Reference hashes and approved lock are unchanged.
