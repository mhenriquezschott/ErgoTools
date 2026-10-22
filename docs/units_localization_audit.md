# F2: model units and risk localization

Completed 2026-09-27 using the approved environment, with no dependency changes. This is a bounded foundation slice, not completion of all unit handling or localization.

## Reference findings

| Source | Observed behavior | Migration decision |
|---|---|---|
| `src/pyLiFFT.py`, LiFFT.__init__; `src/pyTST.py`, TST.__init__ | Metric lever arm divided by 2.54; metric load divided by 4.45. Imperial numbers pass through. | Preserve exact arithmetic in `domain/model_units.py`; normalized values explicitly identify inches and pounds-force. |
| Both calculate methods | Metric displayed moment is `(moment / 0.73756) * 9.81`, then rounded to one decimal. | Preserve in a clearly named model-compatibility function. This expression requires scientific review before first assessment integration; it is not a general physical conversion API. |
| LiFFT.calculate | Imperial model moment rounded to one decimal before damage lookup and before metric display conversion. | Do not move this rounding into input normalization. Fixture records that intermediate value. |
| TST.calculate and moment_cal | Direction and arm contribution affect model moment; conversion/rounding follow damage calculation. | Fixture uses the real moment_cal result for all three directions; full model migration remains pending. |
| `main.py` calls around 5620 and 6025 | Calculators receive selectedMeasurementSystem. | Carry an explicit unit identifier with each input snapshot. |
| `main.py` setUnitText around 1364 | Headers use per-tool lifft_unit/tst_unit, while calculation calls use selectedMeasurementSystem. | Track this potential state mismatch for workflow migration; this slice does not resolve UI state ownership. |
| `main.py` updateUnits around 5403 | Changes selection and labels; does not convert entered values. | Do not claim safe live unit switching. Future switching must preserve a canonical input snapshot rather than repeatedly converting rounded display text. |
| `main.py` input parsing around 6000 | float parsing; empty/bad entries represented by empty strings, rep=0 used when other fields exist but repetitions do not. | Parsing/missing-input semantics await assessment validation; this conversion API accepts typed finite numbers only. |
| `worker_window.py` around 936 | Body height/weight labels switch cm/kg versus in/lb. | Do not reuse force conversion for body mass. Anthropometry needs its own audit and contracts. |
| `main.py` changeLanguage, retranslateUI; `src/eng-esp.ts` and .qm | Mixed direct English/Spanish strings, Qt translation and untranslated newer text. changeLanguage rebuilds some dropdowns. | No wholesale translation-file adoption. Catalog keys are stable and no widget/model mutation occurs in Translator. Selection preservation must be verified during UI migration. |

These findings describe existing code, not validation of model equations or clinical/ergonomic accuracy. No scientific constant was corrected. Reference files remain unchanged.

## Implemented contracts

`MeasurementSystem` uses stable `imperial`/`metric` values. `normalize_model_load` returns immutable `ModelLoad(lever_arm_in, load_lbf)` without rounding. Signed finite numbers remain signed; assessment-specific physical bounds are not invented here. NaN/infinity and display overflow raise ValueError, an explicit new API guard. Unknown systems never silently default to imperial. The API is not a persisted legacy-string parser.

`model_moment_for_display` preserves the existing expression and Python one-decimal ties-to-even rounding. It consumes the moment at each original model's display boundary. It does not calculate damage or risk. The model-unit function must not be used for generic SI conversion, body mass or reverse unit switching. Scientific review of the metric expression is a prerequisite before integrating the first assessment workflow; retain fixtures when an approved correction is proposed.

`presentation/localization.py` supplies immutable English/Spanish risk catalogs and a per-view `Translator`. All four existing risk keys have both translations. English strings match existing appearance labels exactly; Spanish strings are newly authored and need user-facing review with the first localized UI. Unsupported languages raise ValueError and missing keys raise KeyError, making catalog gaps visible. There is no implicit English fallback, global locale mutation, pluralization, regional numeric parser or whole-application translation claim. Values, unit identifiers, risk enums and colors do not change with language.

## Evidence and reproduction

`tests/fixtures/model_units_reference.json` contains 48 observations from the unchanged Python 3.10.18 interpreter, with SHA-256 of both models, main.py and eng-esp.ts. The standalone model files were loaded with runpy.run_path under `python -B`, without Qt, database access or bytecode writes.

Reproduce deliberately after reference review: instantiate LiFFT and TST for imperial and metric, using input pairs `(0,0), (1,1), (12,10), (25.4,44.5), (68.58,100), (15.75,22.25)` and rep=1. For TST use directions `0`, `1`, `2`; for LiFFT direction is an unused fixture marker `1`. Record constructor lever_arm/load, LiFFT `round(lever_arm / 12 * load, 1)` or TST `moment_cal(...)`, and calculate()[0]. These are characterization vectors, not exhaustive valid-input tests or formula verification.

The suite additionally checks unrounded small/signed inputs, force-versus-mass semantics, invalid systems, nonfinite values, output overflow, rounding ties, catalog completeness, exact English labels, independent language contexts, missing keys, unsupported languages and all four language/unit combinations. All 31 tests passed. Overall combined statement/branch coverage is 97.35%; both new production modules are 100%. Ruff, format, strict mypy (17 source/tool files), architecture and builds passed.

## Remaining work

Session/dirty/save/history contracts are next. Complete quantity validation, reversible unit switching, locale-aware parsing/formatting, persistence identifiers, translation expansion and visual acceptance through actual assessment workflows. Retain the metric-moment discrepancy as a visible integration gate. No GUI or dependency proposal is needed for this completed slice.
