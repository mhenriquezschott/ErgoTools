# M1R acceptance — one authoritative calculated result

**M1R complete: 2/6 cleanup milestones, 33.33%.** M2 is not started. This is the
owner-approved correction to M1's former dual-result policy; the fixed remaining
milestones and dependency baseline are unchanged. User acceptance stays on hold
until M4 documentation and M5 final acceptance are complete.

## Delivered behavior

Native format 14 stores one source-bound calculated result per assessment version,
using result envelope 3. Conversion recalculates preserved inputs with the existing
LiFFT/DUET/ST formulas, units and Shoulder Tool selector convention. Original cached
outputs are discarded, including prior converted format 12/13 duplicate stores.
There is no imported-result archive, duplicate result table, or application fallback
to original observations. The external converter remains outside the application.
Historical-result API names refer to assessment versions, not parallel outputs.

Summary totals and probabilities retain calculator precision: Save adds no rounding
or gauge clamping. Intrinsic calculator rounding and UI formatting remain unchanged.
Unchanged input Save retains the result; changed input Save atomically invalidates
it. Calculate/Save replaces the same result row. Transfer, reopen, export, Save As
and Backup preserve matching values and embedded images/rotation data. Export can
evaluate persisted inputs read-only when no saved result exists; it does not store
a second result. Manually entered job risk estimates remain separate authored data.
Missing task inputs remain missing; successful partial calculations are explicitly
partial, and failed evaluation does not fabricate a complete zero assessment.

## Native fixtures and original comparison

The two supported comprehensive originals have regenerated self-contained copies
in [test_projects/native](../test_projects/native), each with 194 versions/results,
four plant images and respectively seven/five schemes. Each has 103 complete and
91 partial results because its original grids contain unfinished rows.

All 388 versions and 7,154 task rows match an independent execution of the original
calculator code. In each original project, 29 ST cached totals differed from fresh
calculation by more than four-decimal rounding. Migrated totals now match original
formulas applied to saved inputs. No formula or original file was changed.

Two additional original samples cannot currently convert: JROT_EpiSalmonTestStudy01
uses an unsupported earlier schema; test3 has a blank required title. These existing
limitations are recorded in [review-register](review_register.md); no new repair or
schema support was added. Do not claim all four originals are converted.

## Acceptance evidence

The required full gate passed **1,256 tests**, with **96.37% execution coverage**;
Ruff, formatting, strict mypy (246 modules), architecture and wheel/sdist builds pass.
Coverage is not a test pass percentage. Focused tests cover exact precision, source
invalidation, one-row replacement, conversion, codec rejection and rollback.

An independently extracted wheel excludes converter/duplicate-store code and runs
native Save As/Backup, main LiFFT/DUET/ST, PLOT and JROT with converter imports blocked.
All ten EN/ES captures were visually inspected, including full VTK, cards and bottom
controls. No layout was redesigned. PLOT capture gauges were still animating and are
not numeric oracle evidence; numeric comparisons use the source/result assertions.
The earlier converted 197-version fixture also upgrades and round-trips correctly.

Reference 500-file hashes and approved lock are unchanged. Documentation-only final
edits preserve executable AST against the functional/native-tested wheel; final
package bytes are checked against current source. No repeated functional gate is
needed for these comments and records. See [validation](cleanup_m1r_validation.json),
[package report](../artifacts/cleanup-m1r-package.json),
[original oracle](../artifacts/cleanup-m1r-original-oracle.json),
[fixture details](../test_projects/README.md) and the refreshed
[documentation inventory](cleanup_documentation_inventory.json). Remaining M4
reviews are explicitly pending; docstring presence does not certify full documentation.
