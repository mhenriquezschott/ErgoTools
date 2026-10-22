"""Shared LiFFT/DUET assessment probability-label policy; not a job-view formatter.

Presentation layer. Preserve original display geometry, decimal policies and palette
independently of scientific source calculation and persistence. Display rounding,
animation and bounded gauges never alter stored inputs/results. Qt operations, where
present, require the GUI owner thread; immutable formatting helpers perform no I/O or
widget mutation.
"""

import math


def format_assessment_probability(probability: float | None, places: int = 1) -> str:
    """Format a 0-1 probability with reference rounding before strict 5/90 cutoffs.

    None displays the legacy zero-total placeholder; it is not model probability zero.
    Reject nonfinite or out-of-scale values instead of showing false bounds.

    Args:
        places: Validated project display decimals; cutoff decisions retain original
            rounding.
        probability: Finite probability on 0-1 scale, or None for the original
            zero-total compatibility placeholder.

    Returns:
        One-decimal percent after original rounding, with strict < 5 and > 90 display
        bounds; None yields 0.0.

    Raises:
        ValueError: Probability is nonfinite or outside 0-1.
    """
    if probability is None:
        return "0.0"
    if not math.isfinite(probability) or not 0 <= probability <= 1:
        raise ValueError("Probability must be finite and on the 0-1 scale.")
    percent = round(probability * 100, 1)
    if percent < 5:
        return "< 5"
    if percent > 90:
        return "> 90"
    return f"{probability * 100:.{places}f}"
