"""Unchanged active DUET 1.3.0 lookup from reference pyDUET.py.

See docs/duet_calculation.md and the frozen fixture for provenance.

Domain layer. These rules and immutable values are independent of Qt, renderers and
storage. Callers supply project snapshots and explicit units; persistence and localized
presentation belong to the application and adapters.
"""

# Unchanged active DUET 1.3.0 dimensionless per-cycle damage by integer OMNI index
# 0-10.
DAMAGE_PER_CYCLE: tuple[float, ...] = (
    2.6e-07,
    4.5e-07,
    1.37e-06,
    4.13e-06,
    1.262e-05,
    3.801e-05,
    0.00011625,
    0.00035014,
    0.00105374,
    0.00322581,
    0.00970874,
)
