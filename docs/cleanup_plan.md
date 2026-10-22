# Owner-approved cleanup complete — Linux

Six fixed milestones: M1, M1R, M2, M3, M4, M5. **All six accepted: 6/6 (100%).**
The owner explicitly authorized finishing M5; its final checks and Linux delivery
are complete. No added milestone/scope. Owner testing can begin with the current
self-contained native fixtures. Native Windows/macOS acceptance stays deferred.
See [M5 acceptance](cleanup_m5_acceptance.md), [validation](cleanup_m5_validation.json)
and [fixed ledger](cleanup_progress.json). Historical headers below are preserved
for provenance and do not supersede this final disposition.

---

# Owner-approved correction — M1R before M2

Six fixed milestones: M1, M1R, M2, M3, M4, M5. Owner authorizes M1R only.
M2 accepted: progress is now 3/6 (50%); M3 awaits owner instruction.
See [M2 acceptance](cleanup_m2_acceptance.md).
See [M1R acceptance](cleanup_m1r_acceptance.md).
M1 converter separation remains accepted; its dual-result preservation policy is
superseded. M2 and later milestone scopes are unchanged; testing stays held.

**M1R acceptance:** one source-bound result set per assessment version; no imported
result store/fallback. Save calculator precision without additional summary rounding
or gauge clamping. External conversion recalculates all versions from preserved
inputs using established formulas, units and ST convention; upgrades prior native
format12/13 into one-result projects. Regenerate migrated test projects. Verify
invalidations, exact reopening/export/transfer/backup and native EN/ES presentation,
with focused/full standards/build checks and updated in-code/documentation records.
No second original result is retained inside new projects or application sidecars.
Original source files remain read-only reference evidence. Missing inputs stay
missing; partial/failed outcomes are explicit, not invented complete assessments.

---

## Historical five-milestone baseline (M1 result policy superseded above)

# Approved cleanup follow-up — M1–M5

Owner approves five fixed milestones and authorizes M1 only. The historical
M01–M12 Linux migration ledger is retained; it does not establish completeness
of the documentation now required. User acceptance testing stays on hold until
all five follow-up milestones pass. No added milestone/scope without approval.
Progress is completed milestones / five (20% each), not effort or time elapsed.

1. **M1 — Independent converter.** Removable code outside src/ergotools; command
   line entry; application invokes an external process, never imports converter
   modules. Old saved results are materialized in native storage with exact
   units/source/status/precision. Original input files remain untouched. Native
   operation, Save As and Backup require no converter/old sidecars/schema decoding.
   Include external upgrade of earlier converted format-12 archive projects.
   Enforce separation and focused failure/data-preservation regressions; required
   standards/full regression/build and independent package proof. Existing Open
   interaction remains for M1; changed interaction is M2, not hidden in M1.
2. **M2 — Guided migration/fixtures.** EN/ES migration explanation, CLI instructions,
   Migrate/Cancel, optional external execution, failure handling, temporary native
   project and explicit first Save. Originals/native fixture directories; every
   plant image and original data relationship checked without original sidecars.
3. **M3 — Names.** Descriptive English snake_case resource/owned file names,
   synchronized references/manifests/package checks. Asset bytes unchanged;
   exceptions explicit, limited to appropriate external/generated conventions.
4. **M4 — Documentation.** Inventory every maintained Python file and symbol,
   including functions/methods/private/nested helpers, tests, developer tooling
   and external migration utility. File purpose/scope/responsibilities/layer;
   function purpose/arguments/returns/yields/errors/units/side effects; documented
   constants. Track source hashes and individual review status. Automated structure
   and signature checks supplement substantive human-readable review; no filler
   templates accepted. Approved sub-batches may partition the fixed inventory;
   no extra milestone or silent expansion. All gaps must close before M5 acceptance.
5. **M5 — Acceptance.** Full regression/standards/build/resource/relocation/backup
   checks, uncovered-path review and updated Linux artifacts/guides. Report exact
   documentation inventory and unresolved gaps; Windows/macOS native tests remain
   deferred. No UI redesign, formula changes or dependency upgrades.

New/modified M1 interfaces receive complete documentation as they are written.
Moving an existing file does not imply its existing docstrings are complete:
the frozen inventory tracks those remaining semantic documentation reviews for M4.
The reference application and original test data remain read-only.
