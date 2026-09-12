"""Canonical derived colors for ergonomic tool risk measurements."""

from __future__ import annotations

from pyDUET import DUET
from pyLiFFT import LiFFT
from pyTST import TST


def job_risk_color(tool_id: str, cumulative_damage, measurement_system: str = "Metric") -> str:
    """Derive the continuous tool-specific risk color used for Job measurements."""
    if cumulative_damage is None:
        return "#D9E1E6"
    damage = float(cumulative_damage)
    if tool_id == "LiFFT":
        tool = LiFFT(measurement_system or "Metric", 0, 0, 0)
    elif tool_id == "DUET":
        tool = DUET(0, 0)
    elif tool_id == "ST":
        tool = TST(measurement_system or "Metric", "", 0, 0, 0)
    else:
        raise ValueError(f"Unsupported ergonomic tool: {tool_id}")
    return tool.colorFromDamageRisk(damage)

