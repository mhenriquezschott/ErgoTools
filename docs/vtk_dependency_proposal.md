# VTK adapter dependency proposal — F78 preparation

**Owner approved the exact project-local dependency set on 2026-10-04:
"yes you can install those for the new code base env". Installation and renderer
validation are complete as F78; all 22 previous locked versions are retained.**

## Concrete baseline

Use the reference application's installed VTK 9.5.0, Matplotlib 3.10.5, NumPy 2.2.6
and their exact runtime dependency versions below, preserving the new project's
already approved packaging 26.3. These reference versions have been read from
installed distribution metadata, without importing or modifying that environment.
VTK requires Matplotlib, which requires NumPy and the remaining packages; these
are packaging requirements, not a proposal to replace the Qt gauge or renderer.

| Package | Exact version | Proposed action |
|---|---|---|
| vtk | 9.5.0 | New-project addition |
| matplotlib | 3.10.5 | New-project addition |
| numpy | 2.2.6 | New-project addition |
| contourpy | 1.3.2 | New-project addition |
| cycler | 0.12.1 | New-project addition |
| fonttools | 4.59.0 | New-project addition |
| kiwisolver | 1.4.8 | New-project addition |
| pillow | 11.3.0 | New-project addition |
| pyparsing | 3.2.3 | New-project addition |
| python-dateutil | 2.9.0.post0 | New-project addition |
| six | 1.17.0 | New-project addition |
| packaging | 26.3 | Already approved; retain |

Python 3.13.14, PyQt5 5.15.11, PyQt5-Qt5 5.15.17, PyQt5-sip 12.17.0 and every other
existing approved package retain their exact versions. The eleven additions are
project-local and Linux-scoped, consistent with the current desktop extra. No
system or reference environment changes are proposed. No optional VTK web/Qt
extra is needed: the existing approved PyQt5 is used by its Qt interactor.

The exact list resolved with approved uv 0.11.25 and the existing new-project
Python, using binary distributions only. This was metadata resolution into /tmp,
not installation, a new environment, or a compatibility test. The proposed
hash-bearing requirements are [archived here](reference/f78-proposed-vtk-requirements.txt).
They are review evidence, not the active project lock. After approval, add exact
pins to the desktop extra and update uv.lock without upgrading existing packages;
check every old package/version before project-local sync.

Primary release information:
[VTK 9.5.0](https://pypi.org/project/vtk/9.5.0/),
[Matplotlib 3.10.5](https://pypi.org/project/matplotlib/3.10.5/),
[NumPy 2.2.6](https://pypi.org/project/numpy/2.2.6/).
VTK publishes a CPython 3.13 Linux x86-64 wheel for this exact version. Metadata
resolution does not prove native Qt/OpenGL rendering, camera or platform parity.

## Reviewed integration slice after approval

Reuse the eight packaged STL files. Preserve each reference actor position and
the shared X=-90/Z=-45 transform, renderer background (0.035,0.176,0.271), initial
LiFFT camera framing and overlay visibility/color policy. The original model loader
uses working-directory-relative paths; the adapter will load packaged assets so
launching from another directory does not lose the avatar.

Keep VTK imports and objects inside presentation.desktop.rendering.vtk_*.
The desktop owner supplies the widget and renderer lifecycle; application/domain
receive only immutable body state and RGB colors. Rendering does not calculate
risk, query SQL or interpret worker labels. Preserve reference full-body and
region framing from the reviewed camera director. Rotate uses Azimuth(20), Zoom
uses 1.15, and Reset View preserves the original camera-mode behavior. Stop active
camera animation before resetting/closing; finalize Qt/VTK resources on owned
window closure. Wire the existing light-icon controls to the actual adapter.

First validate actual LiFFT avatar, valid/absent/partial overlay updates and
Rotate/Zoom/Reset at the integrated 1550×1015 size, including the complete model,
legend, result cards and bottom controls. Then connect body regions as DUET/ST
views migrate. Camera-animation settings remain part of the planned settings
integration, not a new feature. The reference code review is
[archived here](reference/f78-reviewed-renderer.json).

## Verification before acceptance

After installation, run native same-version Qt/VTK rendering checks and the full
existing standards/regression suite. Check packaged model loading from another
working directory, actor positions/transforms, reference camera framing, overlay
clearing, view controls, close/reopen, dimensions/clipping and wheel composition.
Do not use reference-environment execution as evidence of new-project compatibility.
No Windows/macOS/native packaging acceptance is claimed by Linux wheel availability.

## Approved installation and acceptance

The owner approved this exact project-local list on 2026-10-04. Exact pins were
added to the Linux desktop extra, uv.lock updated and all 22 prior lock entries
checked unchanged before project-local sync. Eleven new packages were installed;
Python and existing packages were retained. Native integration, all 638 tests,
standards/build gates and an extracted-wheel native smoke pass. See
[vtk_body_renderer.md](vtk_body_renderer.md) and `f78_validation.json` for evidence
and remaining UI/platform parity limits. This approval does not authorize future
dependency changes, VTK replacement or modifications to the reference environment.
