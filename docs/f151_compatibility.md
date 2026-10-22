# F151 — original LiFFT/DUET form controls and native comparison

LiFFT and DUET controls were compared by executing the original form-building methods in an isolated harness under the approved Qt baseline, without importing the original application's startup or touching its database. Headers, column/control types, DUET rating labels, button icons and matched parent-container captures now have direct source-based evidence. The measured DUET Calculate icon mismatch was corrected from 26 to the original 28 pixels. Overall scope progress remains 74/100; this checkpoint closes comparison subcriteria, not complete C1/C2 final acceptance.

The harness executes original setupLiFFTTab/setupDUETTab, SyncedHeaderLayout, stylesheet, sticky-header and control styling methods. Callback stubs connect construction signals only; they do not stand in for original calculations or workflow tests. Both forms share the same QTabWidget parent to avoid artificial top-level-versus-child layout margins. Original files are read only. Native original/new empty-form captures are in artifacts/f151-original-forms; each pair was visually reviewed. Header text and column types match; DUET rating strings match after stripping trailing whitespace. New missing-value selectors intentionally retain None rather than silently making an unanswered row scale zero, as already documented.

Final acceptance still requires matched populated integrated original-window captures, mixed source/display-unit saved-result presentation, and the shared navigation/reset/delete criteria. LiFFT's migrated bottom summary remains visible while this original constructor initially hides summary labels; the original integrated results path and the owner's reference screen must be reconciled before treating that as final parity. No visual redesign is authorized. Source-constructor evidence is not claimed as a full original application run. Existing full F150 EN/ES populated/pending/resize evidence remains applicable apart from the corrected two-pixel DUET Calculate icon size.

Quality gate: artifacts/f151-check.log. Independent-wheel original construction comparison: artifacts/f151-wheel.log. No dependency or formula changes. Reference and archive remain untouched.

Validation: 1123 tests; 96.43% coverage; required gates and wheel checks pass; 500 reference hashes/lock unchanged. See f151_validation.json.

Follow-up source review: original alignToolSummary explicitly calls widget.show()
on summary labels (main.py 4237–4244). The constructor-only hidden state must not
be reported as a confirmed integrated-layout defect. Final populated comparison
must execute that original result path.
