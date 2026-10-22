# Final disposition

M04 is complete. The comparison and pending-policy notes below are historical;
owner CR003 and the bounded correction resolve all three items. Current evidence
and progress are in [M04 acceptance](m04_acceptance.md) and m04_validation.json.

---

# M04 — comparison complete, correction pending

**M04 remains incomplete. Overall stays 82.75%; 3/12 milestones complete.**
No M04 points awarded, no new milestone/weight/scope added. M05 not started.
This document defines the remaining bounded M04 correction batch; it does not
approve arbitrary additional work or defer these lifecycle gaps as completed.

## Verified current behavior and reusable evidence

136 focused cases passed from the existing extracted wheel: project/session
ownership, dirty Save/Discard/Cancel, snapshots, Properties, New details, prefilled
Save As, recent/missing files, transfer Copy/Move, localization boundaries, CSV,
legacy Open/conversion and strict legacy catalog readers. These tests verify the
currently implemented behavior; passing them does not erase the original workflow
differences below. Atomic Save/Save As/result failure guarantees reuse F150/F153.

A disposable comprehensive-project conversion preserves all 28 raw worker number
pairs; ten rows contain height or weight. It also retains original XML/database/
images, catalogs and history through backup and independent reopen. All 194 saved
summary identities, cumulative damage, full percent precision and per-assessment
units match the original saved-summary table; CSV BOM/CRLF/quoting round trips pass.
Recorded/fresh/saved result distinctions and the extra migrated CSV identity/status
columns are retained existing policies. F138 supplies full typed source/map/rotation
identity evidence; M04 does not rerun PLOT or optimization acceptance.

The first audit harness referenced metadata.system instead of default_units.
That was a harness error after 136 passed tests, not an application failure; the
copy audit alone was corrected and rerun. Both log outcomes are retained.

Individual reused original/new Details and Transfer captures, prefilled Save As,
Spanish Transfer and current copied-project EN/ES Properties were inspected.
Properties retain original 500×400 rows/Close button. Current single-file project
and database paths describe the converted file; original sidecar paths/descriptor
remain in its archive, not falsely presented as active folders. Literal long values
remain available in tooltips. Whole-app localization remains M09; some existing
Transfer explanatory paragraphs are still English in Spanish captures and must
remain visible in that existing review, not be silently certified as translated.

No source/test/UI/dependency changes in this comparison. Reuse unchanged M02 full
quality gate (1,157 tests; 96.49% coverage); identical current wheel SHA. All 500
reference hashes and approved lock verified unchanged.

## Finite remaining correction batch — existing M04 only

1. **Restore original New/first-Save timing.** New should establish an unsaved
   editing state without asking for a final destination/details. First Save must
   collect the original destination/details and publish exclusively; cancellation
   or failure retains the unsaved work. Temporary backing, if necessary, must be
   owned/cleaned and excluded from recent projects. Keep existing approved dirty
   consent and atomic source/result policy. This is the F98/F99 documented gap,
   not a new feature or permission to redesign the project lifecycle.
2. **Open an empty project.** Adopt validated metadata/catalogs with no invented
   assessment, preserving dirty consent and failure isolation. Keep management,
   Properties, Save As/backup and Close usable; assessment editing becomes available
   after an actual assessment is created. This is F89's documented unfinished path.
3. **Close untagged worker-unit policy.** The original labels height/weight according
   to the current project setting but writes/reads their raw numbers unchanged.
   Its rows have no unit history. Current importer assertion of universal cm/kg is
   unsupported by original code. The comprehensive descriptor is Metric, with ten
   nonempty rows (SSN007–SSN016), but its current setting cannot prove historical
   entry units. Do not infer units from plausible numeric ranges or silently change
   source data. Required owner question offers explicit source-unit selection for
   imports with nonempty measurements, or retaining the existing cm/kg assumption.
   If explicit selection is chosen, normalize only destination canonical values,
   retain raw source evidence, and cancel before publication without losing work.

New/empty Open already belong to authorized M04 original-workflow acceptance;
there is no separate request to approve them again. The outstanding question is
about genuinely missing unit provenance and a possible new import decision step.
Collect that answer before the one bounded correction batch, rather than silently
choosing a policy or adding successive repair checkpoints. Any additional finding
requiring repair still needs the owner's scope approval. Completion needs focused
regressions, one required full gate for changed code, packaged/native checks and
all M04 criteria closed. Only then award the fixed 2.5 points (85.25% overall).

Evidence: m04_validation.json; artifacts/m04-wheel.log,
artifacts/m04-copy-wheel.log, artifacts/m04-copy/, prior F150/F153 and F138/F147
records. Reproduction scripts retained as docs/reference/m04-*.py.txt.
