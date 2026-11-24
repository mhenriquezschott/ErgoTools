#!/usr/bin/env bash
# Launch the isolated Android tablet demo; auto-build changed sources and replace
# the same prototype APK without clearing its saved app-private project.
# Arguments: --rebuild forces compilation, --stop closes only this demo emulator.
# Effects: uses dedicated home cache/AVD, writes build/device logs and test data.
set -euo pipefail
project_root="$(cd "$(dirname "$0")/../.." && pwd)"
exec python3 "$project_root/prototypes/android_demo/manage.py" "$@"
