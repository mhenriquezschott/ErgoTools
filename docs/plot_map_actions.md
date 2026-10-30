# PLOT navigation and map actions

The current zoom, persistent cursor/pan modes, Locate, image capture and position-cancel
behavior are documented in [map controls](plot_map_controls.md). The image and markers
share the same transform; fitted zoom is bounded to 100–400%. Normal cursor and Escape
exit navigation modes. View state is undoable session state, not scientific data.

`PlotLayoutCanvas` owns view transforms and input modes. `PlotMapPanel` owns rail commands,
image import/capture consent and scope projection. Geometry and image adapters validate
and stage accepted changes; the main Save writes the project. No reference image paths or
original application modules are read at runtime.
