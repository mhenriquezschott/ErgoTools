# First historical assessment from the window — F56

New assessment in the temporary LiFFT window asks for a worker and an explicit
existing job assignment, then creates an empty current version 1 with a UUID.
It inherits the open LiFFT source's recorded units; it does not copy tasks.
The shared AssignmentDialogHost composes selection and creation through the
existing AssignmentSelector and transactional historical creation APIs.

Pending text requires Apply/Discard first. The existing Save/Discard/Cancel
decision protects dirty source edits. The hierarchy snapshot is checked both
after dialog acceptance and after the dirty decision; the presenter independently
checks job/source freshness. This additional hierarchy check also protects the
existing selection path against changes during a modal dirty decision.

Creation preflight rejects conflicting version/current ownership before saving
the old source. Successful creation opens the clean, persisted draft and clears
calculated results. Other assignments and their current assessments remain intact.
Duplicate creation raises the existing displayed error; it does not overwrite,
choose another version, or silently redirect to an existing assessment.
As in F47, old-source Save and new creation are separate transactions: a late
creation failure may leave the old source saved. Cancellation creates nothing;
applying pending text remains an independent edit.

The action requires an open version-six project and an existing worker/job
assignment. It is not an empty-project bootstrap or worker/job editor, and it
does not upgrade older projects. The default New project still creates the
older standalone format. Units selection during creation and integrated
LiFFT/DUET/ST screens remain future work.

Two added desktop scenarios cover real modal creation, current version 1,
empty clean source, unchanged previous assignment, duplicate rejection, pending
text, dirty cancellation and hierarchy changes during the dirty callback.
All 476 tests pass; combined coverage is 98.94%, the shared host 100%.
Ruff/format, strict mypy (101 source files), architecture and builds pass.
The isolated wheel independently creates through the actual window action
and reopens the saved project to verify both assignment owners.

Native XCB inspection covers empty, populated/pending, Spanish minimum 960 x 680,
worker picker, expanded selected assignment and resulting empty current editor.
Task region, result card, labels and bottom controls fit without visible clipping.
The action reuses existing text-button styling and the chooser's processed icons;
no new icon assets are needed. No VTK view exists in this temporary harness.
See f56_validation.json, reference/f56-capture.py.txt and
reference/f56-verify.py.txt for reproducible evidence. All 500 original files and
the dependency lock remain unchanged. No schema or scientific formula changed.

Next: historical project setup and complete worker/job record workflows, then
integrated model UI. Overall completion remains approximately 66%; this is a
qualitative scope estimate, not a measured code fraction or schedule. PLOT/JROT,
legacy import, scientific review, comprehensive copied-project validation,
final UI parity and release acceptance remain. No reliable finish date yet.
