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
