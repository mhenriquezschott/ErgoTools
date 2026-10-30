# PLOT Job overview

In Job risk view, squares represent current Job risks at worker/workplace assignment
positions. The count and map locations match Comparison; individual worker assessments
are omitted from the map. Repeated Jobs remain separate assignment occurrences.

The hierarchy-aware Job selector lists only relevant placed data from the applied scope.
Job identity, workplace/shift and map assignment are explicit. The overview shows the
selected tool's Job inputs/results as available, plus the assignment's map position.
Locate reveals and centers its square in a zoomed view, without changing saved coordinates.
Cancel movement restores the saved assignment point and reports the outcome.

Job charts distinguish risk values from repeated occurrence counts. Population Job summaries
and worker assessment summaries remain separate quantities; Comparison displays both.
An unavailable Job risk is not treated as zero. Job definitions themselves do not acquire
position/scale records through this view; geometry belongs to assignments/station anchors.

`PlotJobOverview` and `PlotResultSelector` project typed owner IDs. The shared searchable
hierarchy picker handles long result lists; displayed labels are never parsed into keys.
See [marker rendering](plot_marker_rendering.md), [map controls](plot_map_controls.md)
and [database tables](database_tables.md).
