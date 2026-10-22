# F96 — original View camera animation, 2026-10-06

View > Animated body-region focus now exposes the original checkable command,
with English/Spanish caption, tooltip and status guidance. It is enabled only
when the installed renderer implements the optional animation capability. The
default is enabled, matching the reference. Turning it off applies the original
full-body shot; turning it on applies current-region focus. View changes preserve
pending assessment input, sources, units, language, decimal convention and history.
A failed preference write restores the check and existing camera policy.

Explicit mouse clicks on a different tool animate only after the existing source
selection/dirty decision resolves. An unaccepted choice retains the original
camera. Programmatic tab changes snap to the appropriate view; ordinary refreshes
and repeated state/overlay updates do not animate or reset user zoom. A small
owned tab event observer captures intent before Qt selection, without consuming
Qt events; focus completion follows the existing currentChanged handler. This
ordering was established by native tests rather than assuming tabBarClicked order.

VTK geometry, camera objects and motion stay inside VtkBodyRenderer. The portable
optional AnimatedBodyRenderer port exposes policy and resolved selection only.
The widget-owned GUI-thread timer uses the reference 16 ms cadence and elapsed
clock, with three stages: 190 ms outward/full body, 420 ms smooth curved approach,
120 ms outward/final region. Approach offsets, arc and easing follow the reviewed
vtk_camera_director.py. Existing aspect correction preserves framing on resize.
All three stage midpoints were compared numerically against the read-only original
interpolation/easing helper. No solver, risk calculation or project data participates.

New selection replaces an in-flight path. Rotate, Zoom, Reset and close stop the
timer before camera/native-resource changes. Queued/late empty ticks do not render.
There is one Render per tick, including the final exact-target tick; the reference
performed a second final render. Manual camera interruption therefore survives
instead of being overwritten by the next frame. Qt deletes its owned timer when
its widget is released. No threads, new libraries or dependency changes were added.

Reset View now follows the actual original enabled/disabled policy: active region
when enabled, full body when disabled. F78's temporary always-full-body behavior
is superseded. Existing full-avatar resize tests explicitly disable animation
before checking all model bounds; both policies retain their native regressions.

User settings format three adds a strictly boolean animated_body_region_focus.
Versions one/two load read-only and default to enabled; version-two decimal choice
is retained. Explicit settings saves publish version three. Invalid boolean-like
values, incomplete/corrupt/future formats are rejected, not coerced/reset. Older
migrated builds that only support formats one/two cannot read saved format three.
The reference QSettings and environment remain untouched; project schemas are unchanged.

Nine focused new cases cover actual accepted/rejected mouse selection, exact stage
boundaries/target and render count, Rotate/Zoom/Reset/close cancellation, failed
View save, pending preservation, restart, disabled region changes, old settings
compatibility and strict boolean types. Required gates pass 743 tests, 96.34%
combined coverage, lint/format, strict mypy on 153 source files, architecture,
wheel and source builds. The extracted wheel passes actual timer completion for
all tools, View on/off, invalid pending preservation, independent saved preferences,
disabled restart and close during motion. All 500 reference hashes and the approved
lock are unchanged. Only synthetic new-format project/settings files were used.

Native artifacts/camera-animation covers enabled/disabled and no-renderer View,
English/Spanish commands, intermediate/settled frames for LiFFT/DUET/ST, full-body
off, active-region on and 1920 by 1200 enlargement. At 1550 by 1015 and enlargement,
avatar viewport, captions, result cards and bottom controls remain visible. Active
region framing intentionally crops unrelated body parts, following original shots.
This is reviewed workflow evidence, not full original-application/platform parity.

Evidence: f96_validation.json, artifacts/f96-check.log, archived
reference/f96-capture.py.txt and reference/f96-verify.py.txt.
Next usable workflow: original project Properties/details. Remaining localization,
F95 native message parity, renderer extras, scientific gates, PLOT/JROT, legacy
import and final copied-project/platform acceptance remain. Overall percentage
and finish date remain unvalidated after withdrawal of the former 67% estimate.
