# Avatar click/rotation correction — accepted

Owner-reported regression fixed; this bounded repair is **100% complete**. No added
milestones, dependencies, calculation changes or reference edits.

## Reproduction and cause

The original click tests used immediate press/release with no held interval. The
previous event observer passed a left press straight through to VTK and picked only
after release. VTK's default camera interaction rotates while a press is held, even
with tiny pointer movement. Its timer can move the intended colored mesh before the
picker resolves the click. This explains the reported unexpected orientation and
unchanged/wrong tool. The old tests were insufficient; previous click acceptance is
superseded by this correction and realistic input-duration evidence.

Two new regressions (animation enabled/disabled) failed against the previous code,
with substantial camera-position changes during the held click. Evidence remains in
artifacts/avatar_click_reproduction.log. No version or interaction-style replacement
was needed.

## Corrected interaction

The owned Qt viewport filter retains a left press while movement stays within five
widget pixels. Those clicks and their release never enter VTK's camera handler.
Release queues the existing actor picker and ordinary tool-tab selection. A held click
or slight hand movement therefore leaves the camera still until intentional selection
animation begins. Neutral/background clicks also leave it still and select nothing.

When movement exceeds the threshold, the filter forwards the original retained press
once under a reentrancy guard, followed by native move/release handling. Real dragging
still rotates and stops on release; returning to the starting point remains a drag.
Right/middle buttons, wheel and native camera commands retain their existing handling.
No extra history stack, custom detection algorithm or new source/data policy is added.

## Verification

- Full approved Linux gate: **1,313 tests passed, zero failures/skips; 95.80% combined
  statement/branch coverage**; all formatting/lint/types/architecture/naming/docs/build
  checks pass. The two changed maintained files were substantively reviewed and their
  review hashes renewed; documentation inventory has no pending reviews.
- Focused avatar/camera/VTK tests passed. Actual held clicks include 160 ms before and
  after a one-pixel move, followed by release, animation settling and a further check
  for unwanted rotation. Both focus preferences select DUET and finish at the expected
  camera position/view-up. Neutral held clicks cannot rotate. Actual drags rotate,
  select no tool, and leave a stable camera after release.
- Twelve native EN/ES captures inspected: held and released selections for DUET arms,
  ST shoulders and LiFFT back. Native holds last 350 ms with one-pixel movement;
  all three tools select correctly and finish at their existing region camera shots.
  Each begins from a whole-body framing so the tested mesh is visible; ordinary final
  region framing and panel/tab selection are verified. No sideways/spinning result.
- All 194 saved assessment sources/results in the disposable comprehensive-project
  copy and the permanent fixture bytes remain unchanged. Existing toolbar/layout
  evidence is reused because this repair changes no control placement or styling.

Evidence: artifacts/avatar_click_check.log, avatar_click_reproduction.log,
avatar_click_review/validation.json and avatar_click_reviewed_files.json.
Restart the running application to load the corrected adapter; already-open processes
continue using the previous Python code. Local Linux delivery is refreshed.
