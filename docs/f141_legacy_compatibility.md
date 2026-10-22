# F141 — original recorded assessment results

Converted projects now show original cached task outputs and totals in the
existing LiFFT/DUET/ST grids and result cards, explicitly marked Recorded /
Registrado. All 194 original/recovered sources are bound to their exact original
inputs. Editing hides historical evidence; undo can restore it, and saving an
edited source never makes the old result current. Fresh calculation gates remain.
Overall completion percentage and finish date remain unvalidated.

The application owns a typed read-only historical-result contract. Infrastructure
reuses reviewed source/recovery readers on an owned in-memory archive snapshot,
with a per-repository immutable result index. No reference paths, scientific
calculation or evaluation-cache injection is used. Blank cached values remain
absent rather than zero. New-format projects without original evidence keep
existing behavior. All 194 sources/row counts and native EN/ES recorded statuses
were verified from the extracted wheel, including unit projection and minimum /
enlarged original layouts with real VTK. Historical body coloring, row-color
parity for DUET/ST and complete final UI comparisons remain for F144 / later
parity work. Gauge captures can show an intermediate animation value; their
stored numeric targets remain recorded, not recalculated.

Validation: 1088 tests pass; 96.48% coverage. Ruff/format, strict mypy, architecture and builds pass. Extracted-wheel compatibility checks pass. All 500 reference hashes and the dependency lock are unchanged. Historical result display added. Evidence: f141_validation.json and artifacts/f141-*.log.
