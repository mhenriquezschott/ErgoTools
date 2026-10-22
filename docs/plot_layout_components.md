# F100 — original PLOT scope picker and read-only map component

This is the first reviewed PLOT component slice, not the complete PLOT window.
The production toolbar remains disabled. No project schema, bootstrap navigation,
assessment model, renderer or dependency version changed.

## Source and behavior

The behavioral source is the untouched reference `src/plant_layout.py`:
`PlotWorkplaceFilterDialog` (line 687), responsive map setup (around line 2031),
`applyPlotStyle` (line 2666), and `loadImageNew` (line 4916). Controls, margins,
570 by 540 minimum picker size, headers, hierarchy icons, shift selector,
summary and Cancel/Use workplaces treatment come from that code. The reviewed
stylesheet retains its original rules with formatting-only line wrapping.
Packaged processed icons are used; no runtime asset comes from the reference.

Checking a descendant removes checked ancestors; checking a parent removes
checked descendants; choosing another plant clears the previous plant's checks.
Multiple branches under one plant remain possible. Double-click retains the
original checkbox behavior. Acceptance publishes one immutable PlotScope;
Cancel publishes no selection. Shift identity uses item data, so an actual shift
named All or Todos remains distinct from the translated all-shifts option.
English/Spanish captions do not translate stored hierarchy names.

## Separation and improvements

PlotScope validates literal one-plant ancestry and shift membership. The application
load_plant_layout validates before invoking a PlantLayoutReader. FilePlantLayouts
reads an explicitly injected plant/path mapping: absent/missing files return None,
while actual permission/directory errors propagate. It neither infers legacy
filenames nor writes image files or metadata.

PlotLayoutCanvas owns its Qt scene and image decoding. Invalid encoded pixels
raise ValueError before replacing the existing scope/map. Selecting a plant with
no saved image clears the previous map. Original image-pixel scene coordinates
remain intact for later worker/job positions. Aspect-preserving fitting after Qt
layout keeps the complete image visible at minimum/default/enlarged sizes. One
owned single-shot timer coalesces resize fitting and stops on close. No VTK or
assessment calculation is involved.

One deliberate reference correction: the old SQL picker builds parents only
from Station rows. This slice uses the existing complete WorkHierarchy, preserving
empty plants/sections/lines so a map can be selected before stations are added.
It also avoids global tooltip-palette mutation and SQL/global parent lookups.

## Evidence and limitations

Fourteen focused cases cover malformed scope identities, hierarchy normalization,
one-plant/parent-child checks, empty/literal/Spanish records, PNG/JPEG decoding,
missing and invalid images, resize fitting, read-only files and storage errors.
Three actual modal fixture paths leave invalid pending LiFFT/DUET/ST inputs,
workspace state and settings unchanged. These are component integration tests,
not an enabled production PLOT workflow.

All 783 native tests pass; combined statement/branch coverage is 96.40%.
Ruff/format, strict mypy over 162 source files, architecture and wheel/sdist pass.
Native xcb screenshots in artifacts/plot-layout were inspected: source-extracted
original picker/canvas; English/Spanish collapsed, expanded, other-plant, empty
and enlarged picker states; map minimum/default/enlarged/missing states. The
extracted-wheel check also exercises actual Spanish modal acceptance, literal
shift identity, resize, invalid-image retention (its plain-white PNG fixture),
and missing-image clear. All 500 reference hashes and the approved lock match.
See f100_validation.json, artifacts/f100-check.log and archived capture/verification
scripts in reference/f100-capture.py.txt and reference/f100-verify.py.txt.

No full-window PLOT filter/worker/job/risk/chart panels, image import/save,
automatic project image catalog, marker editing/dragging/zoom or JROT exists in
this slice. Caller-supplied image mapping is currently fixture/component input.
Final full-window control positions, adjacent panels, metric/imperial presentation
and comprehensive copied-project validation remain required. Screenshots here
are component/source-derived checks, not final full-application acceptance.

Next: connect image import/save and saved-image associations to the new project's
owned persistence, then compose the original PLOT window around these components.
Preserve literal plant identity and original pixel coordinates; characterize
reference sidecar/copy behavior before choosing storage. If introducing a newer
project format, Save As metadata updates must preserve that version rather than
resetting it to eight. Enable the PLOT entry only with a complete usable workflow.
Overall completion percentage and finish date remain unvalidated.
