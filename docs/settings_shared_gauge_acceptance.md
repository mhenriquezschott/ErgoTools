# Shared gauges, section Settings and owned-dialog theme

Owner-requested follow-up, 2026-10-17. The main-only marker implementation was
incomplete for PLOT. This correction shares the control and preferences, reorganizes
Settings, separates range numbers from tick lines and themes ErgoTools-owned input
forms/prompts. The owner's latest instruction explicitly leaves system file, color
and font selectors on their platform default appearance. There is no custom file
browser. Migration and cleanup remain 100%; no new milestone or points.

## Implementation and contracts

- `RiskGauge` owns one painter, marker menu, interval prompt and probability API.
  `PlotRiskGauge` is a compatibility adapter selecting the compact profile; it has
  no duplicate painter. Main and PLOT preserve their existing animation timing,
  absence policy, arc colors and value mapping. Main label clearance adds four
  pixels at the center; labels move five pixels farther outward. Compact arcs
  reserve the top margin needed by labels, including comparison cards.
- Every PLOT gauge receives the same immutable personal marker options. Bootstrap
  injects the settings port; save succeeds before all three appearances update.
  Failure reports an error and retains their previous options. Main reloads the
  shared preference after PLOT closes. Project bytes/results are not preference
  storage. Personal settings stay at format 5; native schema stays at 16.
- Settings uses a left tree and five retained pages: General, Appearance / Risk
  gauges, Appearance / Avatar, Project and Assessment. The footer always contains
  Apply/Cancel. Switching pages retains drafts; the existing host owns persistence,
  input resolution and reset confirmation. Project/task controls disable when
  unavailable. EN/ES and metric/imperial contracts are preserved.
- Scoped application styling covers base owned forms, input and message prompts;
  established custom-dialog styles retain their local priority. Project Details,
  task count, Settings and custom interval input explicitly use the shared base.
  Menu proxy installation is idempotent under Qt's stylesheet wrapper.
- File/color/font selectors are excluded. There is no application native-dialog
  override, forced `DontUseNativeDialog`, event filter or custom browser. Main Open
  and Save retain the standard QFileDialog wrapper, project filters, suffix,
  cancellation and existing exclusive-save policy. PLOT image/export selectors
  keep default native options. Window-manager title bars remain system owned.

## Validation and practical limits

Final required gate: **1,379 passed, zero failures/skips, 95.41% coverage**.
Strict types (262), standards, architecture/naming, documentation (423 files),
review hashes and wheel/source builds pass. Twenty changed code/test files are
reviewed; all fifteen production modules and both HTML guides match the wheel.

See [machine-readable final results](../artifacts/settings_shared_gauge_validation.json)
and [required gate](../artifacts/settings_shared_gauge_final_check.log). Changed
maintained files were substantively reviewed, with individual hashes in
[review evidence](../artifacts/settings_shared_gauge_documentation_review.json).
The final documentation-only argument correction has unchanged executable AST;
post-build packaging checks verify final source/guide bytes.

Fifty-eight final native XCB captures were inspected in contact sheets with
full-size checks of main labels, PLOT single/comparison gauges, Settings Spanish
project page and prompts. The manifest contains Settings pages with/without a
project (20), interval inputs (2), Project Details/task count EN/ES (4), integrated
LiFFT/DUET/ST with VTK EN/ES (6), PLOT Individual/Job/Comparison and marker/menu
states (18), and ordinary message/confirmation/warning/error prompts EN/ES (8).
No clipping was observed in these captured states. Existing custom forms with
unchanged local themes retain their prior evidence; this is not a claim of new
visual inspection of every unchanged form. Capture scripts are frozen as
`artifacts/settings_shared_gauge_*_capture.py.txt`.

Early attempts to force a common style onto system selectors caused native
capture stalls; the owner also reported a black Open window with the desktop's
not-responding warning. Those attempts were removed. Earlier system file/color/font
captures and broad-theme family logs are superseded, not final acceptance evidence.
The screenshot alone does not prove the sole cause of the host warning. Final
checks mock the system chooser execution boundary and assert native/default
configuration; they do not establish live system-picker responsiveness.

After restarting ErgoTools, manually verify Project > Open > Cancel, Open of an
existing `.ergprj`, Save destination selection/cancellation, PLOT image Open and
image/figure Export selection/cancellation, and color/font selection if used.
They should use the platform's default picker. No native system-picker visual or
responsiveness acceptance is claimed here. Windows/macOS acceptance stays deferred.

The pre-existing main `_AnimatedScale` integer-limit interpolation issue at 100%
is unchanged and remains recorded in the review register. It is not repaired or
visually accepted by this follow-up. This implementation does not write native fixtures or the original reference and
does not change formulas, dependency versions or assessment workflows. The
integrated fixture and approved lock match their recorded hashes. The owner's
actively used comparative test project currently differs from the earlier recorded
checkpoint; it is preserved as-is, not restored or reported as a migration defect.
PLOT QA checks its own before/after fixture bytes and uses a disposable project copy.
See artifacts/settings_shared_gauge_preservation.json for exact hashes.

Next: owner Linux testing feedback. No additional implementation is active.
