# Integrated main-window resizing — F81

The reference launcher fixed the window at 1550×1015. The migrated integrated
preview keeps that initial size and logical-pixel minimum, but allows enlargement
and normal window-manager maximize. The existing layouts allocate extra space;
there are no percentage-positioned controls or new screen designs.

The central assessment frame has layout stretch, the worker combo expands, and
both task scroll areas gain useful space. Body and result sidebars keep their
existing bounded widths. Their captions, cards, viewport and bottom actions remain
inside the window. Result gauges retain their intended size rather than stretching.
Task headers retain actual control widths and horizontal-scroll synchronization.
DUET observes first-row resize events to synchronize after a row rebuild receives
its final geometry, including translated captions; one deferred update coalesces
those events. Resizing does not parse, commit or discard pending assessment text.

The VTK adapter scales its parallel camera by max(1, 0.68 / viewport aspect).
The 0.68 framing aspect comes from the reviewed original camera calculation.
Resize applies the ratio of new and old factors, preserving pose and user zoom;
new region shots and Reset View apply the current factor. Qt/VTK performs the
ordinary repaint: the observer adds no explicit Render loop. A full-body reset
projects all eight world-space model-bound corners inside the tall viewport.
Region closeups still intentionally frame their selected body area.

Native Linux/XCB checks cover 1550×1015, 1920×1200, 1550×1300 and 2100×1300.
The window manager caps actual height at the available desktop, so a 1600px-tall
request is not presented as tested geometry. Captures in
`artifacts/main-window-resize/` combine window.grab with the actual VTK framebuffer
at the viewport's mapped coordinates because direct capture of embedded OpenGL is
unreliable under this compositor. Synthetic projects exercise both connected tabs.
Two focused regressions cover retained pending input/source, sticky-header widths,
adjacent control containment and reversible camera framing/relative zoom.

The minimum is conservative; smaller-display layouts and Windows/macOS/HiDPI
acceptance are not established by this slice. ST/PLOT/JROT are not yet complete,
so they will receive their own integrated resize and visual checks when connected.
Approved dependencies, scientific gates and the reference application are unchanged.
