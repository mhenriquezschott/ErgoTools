#!/bin/bash
# Desktop entry point for an initialized source checkout on macOS.
# Arguments: forward the optional project path and launcher options unchanged.
# Effects: launch the existing application; never install, update or save data.
# Exit: propagate Python's status; report a missing environment before launching.
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -x "$project_root/.venv/bin/python" ]]; then
    echo "ErgoTools environment not found. Follow docs/installation.md first." >&2
    exit 1
fi
exec "$project_root/.venv/bin/python" -m ergotools.launcher "$@"
