# PLOT map controls

PLOT displays the selected Plant's embedded image with markers positioned in original-image
pixel coordinates. The rail provides normal cursor, image selection, zoom, pan, 1:1 reset,
opacity, image capture and export actions. Use the cursor button to return to ordinary
selection/movement; Escape also cancels an armed navigation mode.

Zoom-in/out and pan retain their cursor modes until cancelled. Zoom applies to the image
and all worker/Job figures together, preserving relative positions and apparent scale.
The allowed range is 100–400% of the fitted 1:1 view. Zoom-out and pan are unavailable at
100%; zoom tooltips include the current percentage. Resize/reset fits the complete map.
Zoom/pan state participates in shared session history without changing scientific inputs.

Locate in Worker or Job Overview reveals the selected assignment in a zoomed view and
centers it where possible, clamping at image edges. It does not change the saved position.
Moving a marker changes its assignment map position; Cancel movement restores its saved
point and reports the outcome. The same position is used in Individual, Job and Comparison.

PNG capture exports the actual current viewport with image and markers. It does not replace
the project's embedded image. Accepted map/geometry edits remain private until main Save.
See [markers](plot_marker_rendering.md), [Job view](plot_job_overview.md) and
[shared saving](single_project_save.md).


## Desktop-height adaptation

PLOT uses the current screen's available logical geometry, reserving native title/border
space and the taskbar rather than sizing against raw monitor resolution. Below a
1200-pixel client-height budget it uses compact presentation: 48-pixel map controls,
36-pixel map artwork, tighter spacing/history buttons and result-panel padding,
and a wider details panel to
reduce wrapped text. The chart retains a 220-pixel floor; normal desktops retain
63-pixel map controls and a 250-pixel chart floor. Gauges and text sizes are unchanged.
Demographics disclosure and all three risk modes retain the complete bottom results.
The plant-image view never gains scrollbars; fitting the layout preserves marker anchors.

The Matplotlib chart's resize-dependent preferred height is not treated as an immutable
minimum. This prevents successive layout passes from ratcheting PLOT taller. First-show
sizing does not run again for spontaneous minimize/restore events. This layout policy
changes no saved filter values, assessments, marker positions or optimization data.

At the zoom floor/ceiling, additional clamped gestures leave both the viewport and
undo history unchanged; integer viewport rounding must not create a phantom pan.

The verified compact target is a 1920×1200 desktop with 1152 logical pixels of
available height. Smaller logical work areas remain subject to the controls' functional
minimum sizes; the application does not make text microscopic to bypass those limits.
