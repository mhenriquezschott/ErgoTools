"""Repository namespace for the removable project migration utility.

This tools-layer package is excluded from the application wheel. It contains the
independently launched converter, not normal project editing capabilities.

Developer tooling layer; no normal application module imports this file. External
conversion code remains separately removable. This file owns only the operations
described above; it never changes original project files.
"""
