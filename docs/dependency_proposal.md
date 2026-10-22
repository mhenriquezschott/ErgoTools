# Foundation environment proposal

Status: explicitly approved by the owner on 2026-09-27.

Approval: “Approve these project-local versions and locked transitive dependencies”. The earlier automatic-review block is resolved.

Scope: install only inside this new project. Never alter the reference Conda environment or system Python. No GUI, VTK, scientific or solver libraries are added in this milestone.

| Component | Exact proposed version | Purpose |
|---|---|---|
| CPython | 3.13.14 | Project-local interpreter, ordinary GIL build |
| Ruff | 0.16.9 | Formatting, naming, docstrings, imports and static checks |
| mypy | 2.3.1 | Strict type checking |
| pytest | 9.1.1 | Functionality and architecture tests |
| pytest-cov | 7.1.0 | Coverage measurement |
| Hatchling | 1.32.4 | Build an independently installable wheel |

Use the already installed uv 0.11.25 to create `.python/`, `.venv/` and `uv.lock`. Its available CPython 3.13 build is 3.13.14; the earlier researched 3.13.15 source release is not offered by this installed manager. No manager/system upgrade is proposed. Pin resolved transitive dependencies in the lock and document the resulting environment. Approval includes the required transitive packages resolved for these exact tools, within this project only.

Risks: downloaded executable tooling, Python/package compatibility and project-local disk use. No old application code or data will be installed into or modified by this environment. The source package has no runtime third-party dependency at the foundation milestone. Python 3.13 tests demonstrate candidate compatibility; they are not represented as tests of the 3.10 application baseline.

Release metadata inspected on 2026-09-27: https://pypi.org/pypi/{package}/json for the five named tools. Installation completed in the new project only; exact resolved versions are in `uv.lock`.
