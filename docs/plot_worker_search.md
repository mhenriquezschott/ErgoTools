# F111 — original PLOT worker search and overview selection

Source: `src/plant_layout.py`, `PlotWorkerPickerDialog` (lines 550–693) and
`searchInfoWorkerClicked`. The reviewed constructor/layout is the starting point;
the capture harness executes only that source class, without importing the legacy
application, querying its database or modifying its files.

`PlotWorkerPicker` retains the 820×500 window, 680×420 minimum, original margins,
hierarchy/result splitter, four result columns, live search, processed icons,
Select Worker/Cancel buttons and Cancel keyboard mnemonic. The result snapshot
comes from the existing saved PLOT dataset. Search trims/casefolds a substring
across ID, name, full workplace path and literal shift. Workplace selection applies
an exact ancestry prefix; repeated station labels in different sections remain
separate. First matching result is selected, and double-click accepts it.

The owned Qt dialog returns a stable assignment ID rather than a dataset index.
Worker Overview Search now opens it modally. Accept selects the existing marker
when present, or the overview row for an unplaced/hidden worker. It reveals All
when the selected assignment is outside the current alphabet filter. This corrects
the source handler's dataset-index/combo-index mismatch under alphabet filtering.
Cancel keeps the selected worker and partial visual-setting edits. Search performs
no SQL queries, editor handoff, marker creation or persistence.

Deliberate corrections: Select is disabled when no matching result exists; Search
is disabled when the overview has no result rows. Literal full-column tooltips are
escaped, and English/Spanish captions use the established language contract.
The subtitle can wrap at narrow sizes. These changes preserve the original layout
and workflow while making empty results and localization usable. No dependency,
scientific model, unit conversion, storage format or VTK adapter changed.

## Validation and limits

Three focused cases (English/Spanish picker and real modal overview integration)
cover duplicate worker assignments, repeated station labels, exact hierarchy,
literal All/Day shifts, live case-insensitive search, empty acceptance, Cancel,
double-click, escaped literal names, alphabet disclosure, partial drafts and no
writes/fabricated marker. Full baseline checks pass: 860 tests, 96.40% coverage,
Ruff/format, strict mypy on 180 source files, architecture, wheel and sdist.
An isolated extracted-wheel check repeats the actual modal handoff and verifies
saved positions remain unchanged after reopening the synthetic project.

Twenty-five native captures cover source and new populated/expanded/selected/
query/empty/minimum/enlarged states, localized no-data states, and the adjacent
worker overview/map. All were visually inspected. English populated,
scope-selected and enlarged captures match pixel-for-pixel. Other captures include
cursor blink timing and the deliberate disabled empty Select difference; whole
application parity is not claimed. Native minimum/enlarged states preserve headers,
buttons and splitter containment. The runtime uses packaged copied assets only;
source comparison assets are read solely by the evidence harness.

Evidence: `f111_validation.json`, `artifacts/f111-check.log`,
`artifacts/f111-wheel.log`, `artifacts/f111-native.log`, and
`artifacts/plot-worker-picker`. Reproducible harnesses are archived in
`reference/f111-capture.py.txt`, `reference/f111-overview-capture.py.txt` and
`reference/f111-verify.py.txt`. All 500 reference hashes and approved lock match.

Next: original marker context actions and Load Into Tool handoff, then summaries
and full PLOT composition. Production PLOT remains disabled. Parent close consent,
remaining map actions/deletion composition and final application acceptance remain.
JROT follows PLOT with CBC single-tool, HiGHS multi-tool and no GLPK. Overall
completion percentage and finish date remain unvalidated.
