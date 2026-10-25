# Linux installation and packaging

For installation from Git, use the [installation guide](installation.md#linux).
ErgoTools requires Python 3.13.14, an OpenGL-capable graphical session and Qt/XCB
system libraries. The launcher is `bash tools/run.sh`.

## Wheel installation

Build distribution files from a development checkout:

```bash
.venv/bin/python -m hatchling build
```

Create a separate environment with the same Python version. Install the wheel's
`desktop` extra to include the pinned Linux runtime dependencies:

```bash
uv venv --python 3.13.14 /path/to/ergotools-env
uv pip install --python /path/to/ergotools-env/bin/python '/path/to/ergotools.whl[desktop]'
/path/to/ergotools-env/bin/ergotools
```

Replace the wheel filename with the actual build output. Resources and bilingual
Help are packaged with the application. Legacy project conversion is an optional
external utility; see its [guide](../tools/project_migration/README.md).

Recreate a virtual environment if its installation directory changes. For project
backups and recovery, see [recovery](recovery.md).
