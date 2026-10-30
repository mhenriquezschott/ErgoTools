# PLOT assignment markers

Individual view shows worker assessment shapes with borders: circles for recorded Female,
triangles for Male and hexagons when sex is not provided. Risk colors follow the selected
tool's saved result and established palette. Unavailable data remains distinct from zero.

Job view shows one Job-risk square per visible workplace assignment, at the same positions
and with the same count as Comparison. It represents Jobs in their worker/workplace
occurrences, rather than deduplicating one icon per Job definition. Job IDs identify the
squares. Comparison overlays the individual worker shape on the corresponding Job square.
Tooltip identity uses the actual Job ID/name once; map assignment means worker assignment.

Map points, size, scale and visibility belong to worker assignments. Job definitions do not
supply a separate per-Job positioning/scale table. Station anchors remain distinct shared
geometry. Displaying or locating a marker never fabricates or saves coordinates.

Zoom scales the image and figures together. Cursor modes, clipping and centering are owned
by `PlotLayoutCanvas`; marker painting and identity projection remain in `PlotMarkerItem`
and `PlotMarkerLayer`. Accepted movement and visual changes use shared project history and
main Save. See [map controls](plot_map_controls.md) and [Job view](plot_job_overview.md).
