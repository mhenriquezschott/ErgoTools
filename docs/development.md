# Development

ErgoTools uses Python 3.13.14 and a modular desktop architecture. See
[architecture](architecture.md), [coding standards](coding_standards.md),
[API contracts](api_contracts.md) and the [database reference](database_tables.md).

## Environment

Install Git and uv following the [installation guide](installation.md), then run:

```bash
uv python install 3.13.14
uv sync --locked --extra desktop --python 3.13.14
bash tools/run.sh
```

On Linux, `tools/run.sh` defaults to Qt XCB and removes `XDG_SESSION_TYPE` from
the launched process when using XCB. You do not need to prefix the command with
`env -u XDG_SESSION_TYPE QT_QPA_PLATFORM=xcb`. An explicitly configured
`QT_QPA_PLATFORM` is respected; other operating systems keep their native defaults.

The development environment includes Ruff, mypy, pytest, coverage and Hatchling.
`uv.lock` records exact dependencies so installations can be reproduced. Keep it
under version control; update dependencies deliberately and review compatibility.
Windows and macOS setup is described separately in the installation guide.

## Verification

```bash
bash tools/check.sh
```

The check script runs formatting/lint, strict types, architecture and naming checks,
documentation structure and substantive-review checks, tests with coverage, and
wheel/source builds. Documentation review metadata is maintained in
`cleanup_documentation_inventory.json` and `cleanup_documentation_reviews.json`;
these are verification inputs, not application data.

Review changed file and function contracts before updating review hashes. Refreshing
the inventory does not certify a substantive review. UI changes also require visual
inspection, including the VTK avatar and populated, empty and resized states.
Use private copies of example projects for checks that modify data.

## Packaging

```bash
.venv/bin/python -m hatchling build
```

Builds produce a wheel and source archive in `dist/`. The wheel includes the
application and its resources; the external legacy-project conversion utility
remains separate under `tools/project_migration/`.

Keep domain and application code independent of Qt, SQL, solvers and rendering.
Adapters implement those integrations. Preserve scientific calculations, units,
localization and project integrity when changing interfaces.

## Shared assessment presentation

Use [AssessmentTaskGrid and AssessmentEditorSection](shared_assessment_editor.md) for
new ergonomic task editors. Main, Jobs and compact copy previews share these controls.
Keep host source acceptance, unit conversion, validation, calculation, history and
saving outside the grid; do not add another per-window row/header implementation.
The experimental JROT workflow can adopt the component in its separately authorized
follow-up; this refactor does not change that prototype.


## Documentation map

[The documentation index](README.md) distinguishes current operating/API guides from
historical component records. Public guides must not link to personal checkpoint notes
or ignored local evidence. Retired widgets/modules must be identified as removed rather
than documented as active interfaces. Screenshot projects are private copies with fictional
records; do not modify maintained fixtures to prepare README images.
