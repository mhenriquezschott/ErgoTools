# F104 — original PLOT risk/demographic filter grid

The original filter grid now composes with the map in the temporary component
harness. Apply calls an injected result operation with an immutable scope, tool,
risk-view and demographic selection. Production PLOT is still disabled; this
slice does not claim historical assessment queries, marker rendering or summaries.

## Source mapping and behavior

The layout follows plant_layout.py configureResponsiveLayout, lines 1835–1999:
three exclusive risk buttons; optional demographic fields; 164-pixel action column;
original margins, spacings and processed assets. Disclosure follows
updateWorkerFilterDisclosure at line 3379: the risk/demographic peers change from
68 to 96 pixels and the filter group from 201 to 229. The map below resizes with
them. Source code supplied the geometry; captures check the result.

Sex retains Both/Female/Male order, with stable values independent of translated
captions. Paired age, weight and height bounds are inclusive. As in the original
retrieval routines around lines 5284 and 5538, an incomplete or reversed range is
ignored; missing worker data fails only an active constraint. Disabled demographic
filters accept every worker. Age is current year minus birth year, preserving the
reference rule rather than silently adopting exact birthday-based age.

Weight/height bounds remain kilograms/centimeters internally. Actual edits update
the canonical cache once; changing display units projects that cache without
feeding rounded display values back into it. Repeated unit switches preserve
exact bounds. Large converted values expand the spin maximum instead of clamping
a 1000 kg bound to 1000 lb. Decimal convention is explicit and independent of UI
language; native fields reject grouping. Unit names appear in the existing range
headings: putting suffixes in the original narrow fields clipped values during
native inspection. This unit annotation is a documented metric/imperial correction,
not a grid redesign.

Edited filters remain separate from the last successfully applied selection.
Callback False or exceptions retain the applied snapshot and edited inputs.
Exceptions produce a localized visible message and diagnostic logging. The
eventual result callback must compute before publishing its results; the panel
cannot undo arbitrary side effects in an injected callback.

Clear follows resetFilters at line 3967: first saved plant, all descendants,
shift 1 when available (otherwise first saved shift), LiFFT, individual risk,
Both, empty bounds and disabled demographics. Map scope acceptance/consent occurs
before resetting fields. Refusal or failed map loading preserves the edits.
Clear does not automatically Apply. Risk/tool selection currently edits intent;
the final result integration must preserve the reference risk-view redraw behavior
once actual markers exist.

## Validation and remaining work

Nine focused cases cover predicates and invalid bounds, English/Spanish Apply and
Clear, failures, exact unit projection, explicit decimal input and three-tool
pending assessment preservation. 820 native tests pass; combined statement/branch
coverage is 96.53%. Ruff/format, strict mypy over 169 source files, architecture,
wheel and sdist pass using the approved baseline.

Native source-region captures and English/Spanish collapsed, expanded empty,
populated metric, imperial/comma, enlarged and cleared compositions were inspected.
Full map containment is asserted at enlarged size. An actual Spanish error message
was inspected from the isolated wheel. Source captures include an incidental graph
settings control from the reference extraction; that control and the complete
window regions are not parity claims for this slice. The prior map title contrast
limitation remains for full-window review.

Extracted-wheel checks pass for actual Apply/predicate results, edited/applied
separation, units/decimal, failure message and Clear. All 500 reference hashes and
the approved dependency lock are unchanged. No solver, scientific formula, VTK,
project format or dependency changed. Evidence: f104_validation.json,
artifacts/f104-check.log, artifacts/f104-wheel.log and artifacts/plot-demographics.
Reproducible capture/verification scripts are archived under reference/f104-*.txt.

Next: connect scoped historical worker/job assessment results to the filters,
then original markers and summaries in the complete PLOT composition. Parent
close consent, remaining map actions, legacy sidecars and final copied comprehensive
project/platform validation remain. JROT keeps CBC single-tool, HiGHS multi-tool,
no GLPK. Overall completion percentage and finish date remain unvalidated.
