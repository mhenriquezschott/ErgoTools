# LiFFT window context action — F51

The temporary LiFFT window now invokes AssignmentDialogHost through an Assessment
context action. This is a visible integration step in worker/job workflow migration,
not the final integrated LiFFT/DUET/ST/PLOT/JROT main-window layout.

A no-I/O capability flag enables the action only for an open historical project
(version six). Older/default preview projects keep the action disabled and are not
upgraded. Bootstrap loads the existing packaged jobmanagement, plant, section, line
and station icons; no new assets or dependencies were introduced.

Pending text disables the action. A direct invocation also refuses navigation and
shows the existing Apply/Discard reminder, retaining text. Once resolved, the action
reads worker identities, uses the existing styled picker, invokes the assignment
dialog for LiFFT, and uses the existing dirty-choice prompt. Worker IDs are displayed
directly to avoid ambiguity from names or parsing labels. Successful selection clears
old calculated results and rebinds the editor to the newly active source.

The separate action row preserves toolbar spacing at the 960 x 680 minimum. Native
XCB inspection covered empty and populated windows, 1200 x 780 and 960 x 680,
Spanish at minimum size, pending text, worker picker and popup, expanded assignment
choice and the selected result. The task table, complete result panel, labels and
bottom controls fit without visible clipping. This temporary window has no VTK.
Existing style, processed assets, translated action labels and tooltips are reused.
The assignment dialog itself retains its existing English text; full translation
is not claimed here.

Two new desktop tests exercise capability enabling, pending protection, real action
invocation and source rebinding, cancellation and older-format behavior. All 463
tests pass; total coverage 98.94%. Ruff/format, strict mypy (101 files), architecture
and builds pass. The isolated wheel independently creates the window and executes
its context action through the modal host. Native capture and hashes are recorded
in f51_validation.json and docs/reference/f51-capture.py.txt. All 500 original files
and the dependency lock remain unchanged.

Usability limits: the action selects existing LiFFT assessments; it does not create
workers/jobs or automatically create a missing assessment. New/default preview
files remain version two, and historical test data is currently prepared through
the repository API. Legacy import, current-version transitions, creation controls
and the final integrated window remain pending.
