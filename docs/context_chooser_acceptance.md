# Standalone selection inside the context chooser — 2026-10-17

Owner requested moving Standalone assessment into Select assessment context to
remove its extra main-window control row. Implemented in the existing chooser as
an English/Spanish selectable row; Use assessment context confirms it. Cancel
preserves the view. Workers with no assignments can open this chooser too.
Selecting standalone retains existing pending-input and Save/Discard/Cancel policy,
opens the saved worker/tool source or a transient preview, and never detaches or
copies an assigned assessment. Assignment-only association dialogs do not offer
standalone. The conditional Associate assessment action is unchanged.

No schema, formula, unit, dependency, reference or maintained fixture changes.
Schema stays 16. Migration and cleanup remain 100%; no new milestone. The tested
comparative fixture already differed from historical acceptance because it is used
for owner testing; its handoff bytes were preserved by this change.

## Evidence

- Final native XCB gate: 1,348 passed, zero failures/errors/skips, 95.45% coverage.
  Ruff/format, strict types (259), architecture/naming, documentation (418 files),
  review inventory and wheel/sdist build pass. See
  [gate log](../artifacts/context_chooser_final_check.log) and
  [validation](../artifacts/context_chooser_validation.json).
- Focused context/optional-organization checks: 25 passed. The final gate also
  verifies existing workplace navigation after explicitly skipping the new
  standalone tree row; its previous first-row assumption caused the intermediate
  regression failure. Qt initially lacked sandbox display access; native runs used
  authorized display access. An enum typing issue and formatting were corrected.
- All three changed packaged modules match their rebuilt wheel bytes. Five changed
  code/test files have reviewed contracts and renewed hashes; inventory is current.
- Eighteen native EN/ES captures inspected, including assigned/standalone/preview,
  collapsed/expanded, empty and populated chooser, and association-only states.
  See ../artifacts/context_chooser_review/validation.json. Direct screen grabs were
  black and were replaced with the existing CPU/VTK composite capture method.

## Visual limitation and next step

At 1548×1040 the saved-standalone composite overlaps the top of the body-region
caption when Associate assessment is visible. The enlarged 1800×1120 EN/ES states
fit. Do not claim compact-state visual acceptance or infer whether this is a live
layout defect versus capture behavior. Recorded in review_register.md; no separate
repair was authorized or attempted. Owner testing should confirm that state live
if relevant. Otherwise restart the application and test Select assessment context
→ Standalone assessment → Use assessment context, including Cancel and dirty input.
