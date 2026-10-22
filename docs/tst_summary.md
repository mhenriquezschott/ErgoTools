# TST assessment summaries and selector discrepancy — F21

## Important correction to the F20 call-site description

TstDirection values 0/1/2 identify the model formulas (handling loads, downward, horizontal). They are NOT the unchanged reference UI selector indices. The actual main.py:tstCalculateResults swaps index 1 to model direction 2, and index 2 to model direction 1. Its visible selector labels remain Handling Loads, Push or Pull Downward, Horizontal Push or Pull. Thus the downward/horizontal labels and model execution disagree. F20's direct-model fixtures remain valid, but its claim that IDs directly match UI choices was incorrect and has been corrected.

`tst_direction_for_selection` is an isolated presentation compatibility adapter preserving 0->0, 1->2, 2->1. It rejects unsupported/raw noninteger indices. It is not a scientifically approved mapping. No live GUI or mixed evaluator is wired to it. Before TST workflow integration, explicitly review both the direction-label mismatch and existing metric moment conversion; do not silently fix either. Direct TstDirection enum values retain their model meaning and do not pass through this adapter.

## Summary and presentation contracts

summarize_tst_tasks returns a frozen TstSummary with system, ordered task results, contributions, total damage and optional probability on the 0-1 scale. It checks units and uses the shared ID/damage validation and explicit row-order += arithmetic. Already-rounded task damage is summed without rounding the total; shares round to one decimal and need not sum to 100. TST retains its own probability formula. Empty/zero results have zero shares and absent probability, not a zero-risk assertion. Invalid IDs, damage, units and overflow produce structured errors without partial output.

The stateless display mapping retains one-decimal moments, five-decimal row damage, four-decimal positive totals, and round-before-bound probability labels. A positive total may display 0.0000 while probability uses its full value. Rounded-zero contributions suppress row colors. Zero total provides 0.0 placeholders, explicit None colors and zero share strings to clear stale view state. The original zero branch does not clear all prior styles/labels/actors; this intended correction is documented rather than claimed as unchanged UI behavior. No windows or shoulder actors were modified or visually accepted.

## Reference evidence

The fixture tests/fixtures/tst_summary_reference.json contains 70 captures from the actual unchanged tstCalculateResults method, compiled from its AST with the original TST class and inert widget/renderer stand-ins. All three selector choices, both systems, empty/zero inputs, thirds, large relative contributions and deterministic multi-task groups are included. Exact total/share values, task moment/damage strings, summary strings and all colors match. No Qt launch, operational database or reference bytecode writes occurred.

Reference main.py SHA-256: `6e8a65a2ba7370b1dbda199110e3cfbe0b9f62d91ed9677ceea9f8483b3e2fc5`. Method AST SHA-256: `973e031d614f57e8eb8218709a07ce13ecdc27b612f782d1b67c4b1f69a9d3a6`. Original runtime: `3.10.18 (main, Jun  5 2025, 13:14:17) [GCC 11.2.0]`. Full capture harness: reference/f21-capture.py.txt. This is behavioral characterization, not scientific validation or UI testing.

Five new tests cover all captured groups, explicit selector mapping and invalid indices, zero/small-positive distinctions, wrong units/invalid damage/overflow, summation/rounding and immutability. All 227 tests pass; combined coverage is 99.53%, new modules 100%. Ruff/format, strict mypy (65 files), architecture and builds pass. Independent package/reference/lock evidence is in f21_validation.json.

## Next work

Implement TST source draft, reversible editing and versioned persistence with explicit model-direction identities, then add it to mixed-project source routing while retaining review-required evaluation gates. Scientific resolution of the reference selector swap and metric conversion, GUI/VTK integration, remaining workflows, legacy migration and native packaging remain pending. No runnable replacement desktop app exists yet.
