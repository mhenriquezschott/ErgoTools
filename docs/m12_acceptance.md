# M12 accepted — Linux migration complete

**100/100 of the owner-approved Linux migration; 12/12 milestones closed;
26/26 fixed remaining points earned.** M12 earns its existing 2.25 points.
No new milestone, dependency, UI redesign or formula change.

On 2026-10-11 the owner explicitly states that the migration finishes with Linux;
Windows/macOS native testing will be added later. This resolves M12.3's required
scope/deferral decision. Neither Windows nor macOS has passed native acceptance.

- M12.1 verified: independent approved Python/environment/wheel installation,
  installed integrated launcher, 71 packaged assets, VTK, CBC/HiGHS, disconnected
  operation and comprehensive copied-project backup/reopen equality.
- M12.2 platform source review complete; native Windows/macOS acceptance is
  explicitly deferred by the owner, rather than reported as a passed test.
- M12.3 installation/run/recovery instructions and evidence delivered; explicit
  deferral recorded. Reference application and operational projects untouched.

Linux original-codebase equivalence is supported by the accepted M01–M11
control/layout/workflow, units/languages, calculation and comprehensive-copy
integration evidence. In particular, [M10 acceptance](m10_acceptance.md) records
the integrated original-project conversion, all three calculators, PLOT, both
JROT solver routes, transfer/export and backup/reopen. That evidence is reused;
closure is not a claim that automated tests prove every possible interaction.
The owner's own Linux acceptance/use comes before later native platform work.
Any concrete mismatch found in that review should be recorded with reproduction
steps and handled under the existing scope-control rule, not rolling milestones.

Final full gate: **1,226 tests, 96.42% coverage**, lint/format/strict typing/
architecture and builds pass. Final wheel: **21 focused tests, 77 subtests**,
237 Python files and guide bytes equal to source; installed-only/native evidence
and all 500 reference hashes/approved lock verified. No dependency/formula change.

Run the new project with `bash tools/run.sh`; installed command: `ergotools`.
To retain earlier project-local preferences explicitly, pass
`--settings "$PWD/.cache/desktop_settings.json"`.

[Linux delivery instructions](linux_delivery.md), [platform review](platform_review.md),
[validation](m12_validation.json), [review](m12_review.md),
[delivery checksums](../dist/linux/SHA256SUMS).


## Subsequent bounded original-workflow correction

Owner-requested positional command-line project opening is restored and the
existing Recent Projects workflow verified. See [correction acceptance](cli_project_acceptance.md)
and [current validation](cli_project_validation.json) for the corrected wheel
and current 1,232-test gate. Earlier M12 figures/hashes remain historical evidence.
No milestone/point/dependency change.

Current owner-approved history extension and delivery hashes: [analysis history acceptance](analysis_history_acceptance.md), [validation](analysis_history_validation.json). Earlier evidence remains historical.
