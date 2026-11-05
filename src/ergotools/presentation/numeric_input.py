"""Compatibility exports for the shared, widget-independent numeric token policy.

Presentation callers retain their established imports. The single implementation now
belongs to domain so application clipboard validation uses exactly the same grammar,
precision, missing-value and overflow rules without depending on presentation.
"""

from ergotools.domain.decimal_convention import DecimalConvention as DecimalConvention
from ergotools.domain.numeric_input import (
    format_input_number as format_input_number,
)
from ergotools.domain.numeric_input import (
    parse_input_number as parse_input_number,
)
