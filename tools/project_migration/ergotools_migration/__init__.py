"""Read original schemas and publish recalculated standalone native projects.

The application invokes this separately removable external tool as a process; it never
imports these readers. Native operation needs no original folders or converter code.
Original files stay untouched; the output retains current inputs and one recalculated
result per valid assessment version.

Developer tooling layer; no normal application module imports this file. External
conversion code remains separately removable. This file owns only the operations
described above; it never changes original project files.
"""
