# PLOT worker and Job selection

`PlotResultSelector` provides a compact summary/selection control with a searchable
hierarchy picker (`PlotResultPicker`). Worker Overview in Individual and Comparison and
Job Overview in Job view use the corresponding applied result population. The picker
supports text search, scope navigation and exact assignment identities; it is not a giant
unstructured combo list. The former `PlotWorkerPicker` implementation is retired.

Selecting a result synchronizes the map/overview without creating markers or changing
saved coordinates. Hidden or unplaced worker records remain distinct from visible points.
Locate reveals a placed result in the zoomed viewport and centers it when possible.
Cancel preserves the original selection and local pending controls. Names, repeated
station IDs and shifts remain literal data, independent of translated labels.

Selection/view changes use the existing shared project session. Source/results and
geometry persist only through their explicit accepted operations and main Save.
See [Worker Overview](plot_worker_overview.md) and [Job Overview](plot_job_overview.md).
