# F142 — active original PLOT loader compatibility

The original PLOT call path and active loadImageNew implementation were audited.
Stored Plant rotation/crop/mirror/other transform fields are not applied by that
loader. The migrated canvas matches its original pixel coordinates, scene bounds,
aspect-preserving fit, Top/Left alignment and hidden scrollbars, including resize.
Introducing dormant transforms would change the original behavior. They remain
archived for review rather than being activated. Next: readable assessment choices
and numeric inputs. Overall percentage/finish date remain unvalidated.

A frozen copy of only the active original method characterizes landscape,
portrait and square maps at two view sizes. It runs as an isolated function with
approved Qt components; the reference module is never imported or modified.
Exact scene rectangles and transforms match the migrated component. The existing
comprehensive original-map capture remains F140 evidence. No production/UI change
was required after this audit. This resolves the suspected missing active Plant
transform behavior, not every PLOT feature or final visual acceptance requirement.

Validation: 1091 tests pass; 96.48% coverage. Ruff/format, strict mypy, architecture and builds pass. Extracted-wheel compatibility checks pass. All 500 reference hashes and the dependency lock are unchanged. No UI change. Evidence: f142_validation.json and artifacts/f142-*.log.
