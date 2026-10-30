#!/usr/bin/env bash
# Desktop composition entry: launch the installed checkout with approved versions.
# Arguments: forward every argument unchanged to ergotools.launcher, including an
# optional project path and --settings; shell quoting preserves paths with spaces.
# Exit: replace this shell and propagate the application process exit status.
# Effects: normal application windows/preferences/project operations; no installs.
# Linux defaults to the approved XCB backend; explicit platform overrides are retained.
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$OSTYPE" == linux* ]]; then
    export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
    if [[ "$QT_QPA_PLATFORM" == xcb ]]; then
        unset XDG_SESSION_TYPE
    fi
fi
exec "$project_root/.venv/bin/python" -m ergotools.launcher "$@"
