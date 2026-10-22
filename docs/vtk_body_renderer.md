# Original avatar integration — F78

The integrated preview now loads the eight packaged original STL models through
`VtkBodyRenderer`, confined to the desktop rendering adapter. The portable
`BodyRenderer` port receives immutable region/color display state and exposes the
three reviewed view controls and cleanup. It has no Qt/VTK types, project storage
or scientific calculations. This keeps the established future renderer/platform
boundary without adding a second renderer or new infrastructure.

## Original behavior and deliberate implementation changes

All actor positions, shared X=-90/Z=-45 transform, background, projection,
reference region/full-body framing and control factors come from the current
reference source. Characterization extracts its renderer methods and camera
class read-only, redirects only asset filenames to temporary packaged copies,
and compares all eight actor positions/bounds and all four shots exactly in the
approved new environment. The original checkout/environment is never executed
as a compatibility test or modified.

The old loader uses paths relative to the launch directory. The adapter obtains
bytes from the package, stages them briefly for vtkSTLReader, checks decoded
meshes, and retains mesh data after temporary files are removed. Missing assets
propagate an error after native cleanup. No live render pipeline rereads a removed
file. Empty/invalid/pending/review-blocked results hide the current risk overlay.
Duplicate display states do not render again; value changes preserve camera
position. Region transitions use reference shots. Native resources finalize once
on accepted close, and remain usable after a modal close cancellation.

## Run and verification

```bash
.venv/bin/python -m ergotools.bootstrap --integrated-preview
QT_QPA_PLATFORM=xcb bash tools/check.sh
```

`--disable-vtk` intentionally retains the renderer-free composition for isolated
UI review. Programmatic `create_window` defaults to that composition; native tests
and the integrated CLI explicitly enable VTK. Offscreen tests skip the six native
OpenGL checks; they must be run with a working native display for acceptance.
Exact approved packages and owner authorization are in
[vtk-dependency_proposal.md](vtk-dependency_proposal.md).

638 native tests pass; combined coverage is 96.91%. Standards, strict types,
architecture, source/wheel build, extracted-wheel native rendering and synthetic
calculation/save/reopen checks pass. All 500 reference hashes are unchanged and
all 22 previous locked package versions retained. Evidence: `f78_validation.json`.
Native captures are in `artifacts/vtk-body/`, with reproduction scripts archived
under `docs/reference/`. Qt widget grabs do not reliably contain native OpenGL;
QScreen grabs are black under this compositor. Verification artifacts therefore
place the actual VTK back-buffer image at its exact widget coordinates in the Qt
capture. They are labeled as composed captures, not direct system screenshots.
The two standalone avatar framebuffers compare original and adapter rendering.

## Remaining scope

This is LiFFT integration, not final application parity. DUET/ST views are next;
then their region labels, stored per-tool overlay coexistence and the existing
optional camera-animation setting must be connected. Reset currently implements
the reference animation-disabled full-body behavior. Full menu/settings,
PLOT/JROT, legacy import and final copied-project validation remain separate
planned work. No Windows/macOS packaging or performance acceptance is claimed.
All scientific unit/model review gates remain intact; no formulas changed here.
