# F102 — original PLOT map/action rail with working Open and Save

PlotMapPanel ports the reviewed map region from the original plant_layout.py
configureResponsiveLayout, around lines 1999–2070. It is a reusable original-window
region, exercised in a temporary native harness; the complete production PLOT
window remains unfinished and its main entry remains disabled.

## Original controls and owned behavior

The blue 81-pixel action rail retains all eight original icons in original order,
63 by 63 buttons, 48-pixel icons, 42-pixel title, margins and spacing. The expanding
canvas retains the 900 by 580 minimum and original image-pixel scene coordinates.
Open and Save now invoke the F101 image adapters through injected reader/writer/
importer contracts. Existing packaged zoom/opacity/capture assets are exposed by
bootstrap; no new asset, stylesheet, dependency or project format was introduced.

Open uses the original PNG/JPG chooser, previews without saving, and cancellation
leaves the map alone. Import/decode errors retain the previous map and pending
image. Save commits only the preview for its exact selected plant. Failure retains
that preview and enables retry; success clears pending intent and shows the
original success message. Selected scope, preview and view state belong to this
Qt component; files/SQL remain in injected adapters. Assessment data/history/
settings are not read or accepted by these actions.

The same scope does not reload or discard its preview. A different workplace asks
before discarding an unsaved image; No is the default. Load failure keeps the old
scope/map. This corrects the reference's retained temp-image path, which could
otherwise be saved under a subsequently selected plant. Open is disabled without
a scope; Save is disabled without a pending preview. These are deliberate
interlocks rather than repeated generic warnings. Existing future rail actions
(zoom/actual-size/opacity/capture/export) remain visibly disabled until migrated.

All owned tooltips, chooser caption, messages and confirmation buttons support
English/Spanish. Stored names are literal. Error text is PlainText. A native check
exposed Pillow's memory-address error text: user-facing failures now explain the
failed operation and retained state in the active language; technical traceback
remains in the standard diagnostic log. No blanket error suppression is used.

## Validation and limits

Six new cases exercise actual Open/Save button paths, cancel/invalid import,
failed-save retry, scope consent and failed scope loading. Actual native localized
Yes/No/OK messages verify default No and literal text. Three main-assessment fixture
paths preserve pending invalid LiFFT/DUET/ST input, active state and settings.
The main PLOT entry remains disabled in those checks.

803 native tests pass, 96.43% combined statement/branch coverage; Ruff/format,
strict mypy (166 source files), architecture and wheel/sdist pass. The extracted
wheel uses actual Open/Save controls and Spanish chooser/messages, discard-No,
failed-save retry, cancellation, resize and saved reopen. All 500 reference hashes
and the approved lock remain unchanged. Evidence: f102_validation.json and
artifacts/f102-check.log. Native captures in artifacts/plot-map-controls compare
the extracted original source region with English/Spanish no-scope, empty,
preview, saved, error, consent and enlarged states. Full map corners and every rail
button were checked for clipping. The source's inherited dark rail-title treatment
is retained; full-window visual acceptance and any original contrast issues are
still subject to final review. Native message treatment follows the reference;
remaining shared message-icon/order parity work is already recorded at F95.
Capture/verification scripts are archived in reference/f102-capture.py.txt and
reference/f102-verify.py.txt.

This is not the final full-window acceptance: workplace/tool/worker filters, worker/
job marker interactions, summary charts, risk panels and remaining rail actions
still need composition. Full modal closing/unsaved-image consent must be wired
when the parent PLOT window is added. The parent owns project lifetime; current
integration fixtures do not authorize global project switching while editing.
No main-window layout or VTK component changed in this slice.

Next: the original workplace/tool filter region and window composition around
this map panel, followed by marker/filter/summary workflows. Preserve source
layout and reviewed callbacks; do not recreate forms from screenshots. Final
metric/imperial/legacy/copied-project/platform checks remain. JROT remains after
PLOT with CBC single-tool/HiGHS multi-tool and GLPK excluded; no solver installed.
Overall application completion percentage and finish date remain unvalidated.
