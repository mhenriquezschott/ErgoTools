# F149 — reliable main-window capture and resize verification

F149 verifies the reported main-window clipping without changing the application's
layout or behavior. Full-resolution F148 PNGs contain the labels and regions that
appeared absent in combined previews; R007 was not an established application
layout defect. The record is corrected rather than adding repaint callbacks.
The application wheel remains byte-for-byte identical to F148. Overall scope
progress remains 74/100 complete and 26/100 remaining; no final gate is awarded.

A small typed desktop verification helper now renders Qt into owned CPU image
memory and composites native frames only within their explicit logical viewport.
It preserves device pixel ratio, clips native drawing, rejects empty/out-of-bounds
images and returns a detached snapshot without committing editors or changing
layout. No VTK dependency crosses into the application/domain or this helper.
Four focused regressions prove adjacent-pixel preservation at 1x/1.5x/2x scaling,
invalid-image rejection and snapshot independence from later control changes.
This improves the verification code; it is not an application repaint fix.

Diagnostics compared native screen grabs, QWidget grabs and control rectangles.
Direct screen grabs returned black in the current XWayland session; ordinary Qt
capture does not contain the native OpenGL scene. These capture limitations are
not missing application controls. Full-resolution individual source PNGs were
inspected, and a contact tile was verified byte-for-byte against its scaled source.
No low-level GPU/compositor cause is asserted from these observations.

Native extracted-wheel EN/ES verification produces 20 captures across LiFFT,
DUET and ST: minimum 1550x1015, enlarged 1800x1200, invalid pending text, and an
empty project with Reset View fitting all eight full-avatar bounds corners.
Checks verify caption ink, control bounds, unchanged adjacent card/context/footer
pixels after native compositing, source preservation and unchanged original XML,
database and images. Populated, pending and empty controls/headers/cards/VTK and
bottom controls were visually inspected. Frame fitting does not assert that a
focused anatomical view must display the full body; original focus shots remain.

Original setupResultsSidebar constraints were checked directly in reference
main.py: width 230–260, margins 12/8/12/8 and 235px risk card match the migrated
code. No forms were reconstructed from screenshots. Final matched original-window
workflow/layout acceptance remains in C1/C2/C3/C4/G2, with original metric and ST
compatibility policies unchanged. Native fractional-DPI platform acceptance is
still pending; the fractional-ratio regression checks image composition only.

The owner's ONE-milestone pacing is persisted in AGENTS.md and the completion
plan. Stop after F149. Next is F150: unchanged-input fresh-result Calculate/Save/
export/reopen provenance (R008), preserving the original archive separately.

Validation: 1108 tests; 96.45% coverage; required gates and wheel checks pass; 500 reference hashes/lock unchanged. See f149_validation.json.
