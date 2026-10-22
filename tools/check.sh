#!/usr/bin/env bash
# Developer tooling: run the required standards, regression, coverage and build gates.
# Arguments: none; the repository is resolved from this script, not the caller cwd.
# Exit: zero only when every command passes; otherwise propagate the first failure.
# Effects: use the approved local interpreter; write caches, coverage/test artifacts
# and wheel/source packages. No dependency installation or reference-project writes.
set -euo pipefail
cd "$(dirname "$0")/.."
python_path="$PWD/.venv/bin/python"
mkdir -p artifacts
"$python_path" -m ruff check .
"$python_path" -m ruff format --check .
"$python_path" -m mypy
"$python_path" -m tools.check_architecture
"$python_path" -m tools.check_naming
"$python_path" -m tools.check_documentation
"$python_path" -m tools.check_documentation_review
"$python_path" -m pytest --cov --cov-report=term-missing --cov-report=json:artifacts/coverage.json --junitxml=artifacts/tests.xml
"$python_path" -m hatchling build
