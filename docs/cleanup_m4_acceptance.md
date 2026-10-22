# M4 accepted — complete in-code documentation and enforcement

**5/6 cleanup milestones complete: 83.33%.** M1, M1R, M2, M3 and M4 are
accepted. M5 final acceptance/delivery is unstarted and awaits owner instruction.
No milestone was added or expanded; owner testing remains held through M5.

## Exact documented and reviewed boundary

- **401 maintained Python/stub files**, all individually reviewed and hash recorded.
- **2,672 functions/methods**, including private and nested callbacks: purpose,
  exact Args and Returns/Yields; errors, units, ownership/effects where relevant.
- **391 classes**, with state contracts and relevant attribute responsibilities.
- **301 uppercase constants**, with adjacent meaning/units/source comments.
- **Two shell entry points**, documenting purpose, arguments, exit and effects.
- **Zero pending reviews; zero structural gaps.**

The two files added after the 399-file checkpoint are the maintained review-inventory
tool and its regression tests. They implement existing M4 enforcement scope. Counts
are an exact inventory, not effort estimates or extra milestones. Frozen reference
text, generated environments/caches and captured original fixtures are excluded from
maintained-code review; their read-only status is checked separately.

Review covered actual bodies and contracts, not just headings. Important details
include sole full-precision source-bound results, display-only rounding, original
scientific row/selector behavior, recorded/display units, modal ownership, history,
PLOT pixel coordinates, JROT frozen references/solver routing, Qt signal blocking,
GUI-thread rendering and cleanup. Tests document fixture ownership, injected failures,
selection/rollback scenarios and assertions. Stale archive/future-UI descriptions and
ambiguous return/coordinate contracts were corrected to current implementation.

## Enforced review workflow

Both source-only gates now run in `tools/check.sh`:

1. `tools.check_documentation`: module/class/function documentation, exact argument
   names including variadics/receivers, function-owned Returns/Yields, explicitly
   escaping raised errors and adjacent constant explanations.
2. `tools.check_documentation_review`: exact source and symbol/signature metadata,
   independently recorded reviewed hashes, pending/new/deleted files and shell edits.

The inventory is reproducible. `--refresh-inventory` updates metadata but never
writes reviewed hashes or approves changed files. Fifteen focused regression cases
cover missing/private/nested contracts, argument drift/duplicates, generator/error
scope, metadata tampering, added/deleted/changed files and malformed review maps.
These checks cannot judge scientific prose or infer every injected adapter error;
substantive review remains mandatory. See coding_standards.md and development.md.

## Final validation

Approved Python **3.13.14**; exact existing dependency baseline unchanged.
`QT_QPA_PLATFORM=xcb xvfb-run -a -s '-screen 0 1920x1200x24' bash tools/check.sh`:

- **1,282 tests passed, zero failures/skips** in 66.62 seconds.
- **96.25% combined statement/branch coverage**, above the
  existing 90% threshold. Coverage measures executed code, not test pass rate;
  every collected test passed. This does not claim 100% path execution.
- Ruff/format; strict mypy **250 modules**; architecture/naming and both documentation
  gates pass. Independent wheel/source builds pass.

AST comparison after removing docstrings proves all **397 pre-existing Python/stub
files** retain identical executable code, including all **229 application modules**.
Only the two documentation tools, their two test files and the required shell gate
contain new executable checks. All **74 packaged resource files** remain byte
identical to M3. No calculator/schema/UI, localization or unit behavior changed.
Therefore M3's ten inspected native English/Spanish main/VTK/PLOT/JROT captures and
Save As/Backup evidence remain applicable; no redundant screenshot cycle was run
for documentation-only changes. New full M4 regressions establish current behavior.

All **500 reference file hashes**, **27 original fixture files** and the approved
lock remain unchanged. Converter separation remains intact. Package verification
checks exact maintained sources and reviewer records in the source archive and
exact application sources/resources in the wheel; conversion tooling is excluded
from the application wheel. The accepted records are included in the refreshed
source archive. No dependency installation, reference write or publishing occurred.

No critical decision or newly discovered repair remains within M4. M5 remains the
separate final acceptance/delivery milestone; native Windows/macOS work stays deferred.

[Validation](cleanup_m4_validation.json), [review inventory](cleanup_documentation_inventory.json),
[explicit reviewed hashes](cleanup_documentation_reviews.json), [fixed ledger](cleanup_progress.json),
[full gate](../artifacts/cleanup-m4-check.log), [package proof](../artifacts/cleanup-m4-packages.json).
