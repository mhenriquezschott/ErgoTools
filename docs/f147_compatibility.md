# F147 — recorded summary CSV compatibility

Saved summary exports now preserve exact-source archived results with explicit
recorded status. The read-only application contract checks source equality before
using evidence; edited sources take the characterized fresh calculator path.
No calculation is run for an unchanged archived source. Per-assessment recorded
units are retained, including DUET's labels independent of project defaults.
This closes CSV compatibility within B1's existing G3 credit; no extra scope
points are claimed simply for completing another checkpoint.

CSV keeps the original first eleven columns and existing migrated identity/status
columns. Original Metric/Imperial spelling is restored. Recorded percent precision
is retained directly rather than divided, multiplied and rounded again; missing
and zero are distinct, and no gauge clipping occurs. Fresh percentages retain the
established one-decimal output. Numeric SQLite values are compared numerically;
this is not byte-identical integer/float text formatting or timestamp reproduction.
UTF-8 BOM, CRLF, quoting and exclusive atomic publication remain unchanged.

Focused regressions exercise recorded missing/zero/high-precision values, prohibit
accidental recalculation, check edited-source invalidation, and preserve DUET's
per-assessment units. Packaged independent-oracle validation compares all 194
comprehensive original summary identities, damage, percent and unit values against
the original table on a disposable copy, then round-trips the CSV writer.
All values match. No UI layout changed; native export interaction is exercised in
F148. Reference tree and approved dependency lock remain unchanged.

Export is deliberately based on saved source and archived evidence, not the
active editor or an ephemeral Calculate result. An unchanged imported source
therefore still exports recorded evidence after an in-memory recalculation.
That distinction is explicit and remains part of final workflow acceptance.
Next: full fresh workflows on the comprehensive copy across all three tools,
PLOT, CBC single-tool and HiGHS multi-tool JROT, backup and archive retention.

Validation: 1102 tests; 96.45% coverage; required gates and wheel checks pass; 500 reference hashes/lock unchanged. See f147_validation.json.
