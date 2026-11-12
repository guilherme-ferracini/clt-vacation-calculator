"""Brazilian payroll tax tables used by the calculator.

Values for 2026:
- INSS (employee): Portaria Interministerial MPS/MF nº 13/2026, in force since 1 Jan 2026.
- IRRF monthly table: in force since May 2025 and kept for 2026.
- IRRF monthly reduction: Lei nº 15.270/2025 (zero tax up to R$ 5,000.00 of taxable income,
  decreasing reduction up to R$ 7,350.00).

Tables change every year. Add a new entry to TABLES instead of editing an old one,
so past calculations stay reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal as D
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class IrrfReduction:
    full_until: D        # taxable income up to this value: tax is reduced to zero
    full_cap: D          # maximum reduction in that range
    partial_until: D     # decreasing reduction up to this value
    intercept: D         # reduction = intercept - slope * taxable income
    slope: D


@dataclass(frozen=True)
class TaxTables:
    year: int
    # (upper limit of the bracket, rate); the last limit is the INSS ceiling
    inss_brackets: List[Tuple[D, D]]
    # (upper limit or None for "above", rate, amount to deduct)
    irrf_brackets: List[Tuple[Optional[D], D, D]]
    irrf_dependent_deduction: D
    irrf_simplified_discount: D
    irrf_reduction: Optional[IrrfReduction]


TABLES: Dict[int, TaxTables] = {
    2026: TaxTables(
        year=2026,
        inss_brackets=[
            (D("1621.00"), D("0.075")),
            (D("2902.84"), D("0.09")),
            (D("4354.27"), D("0.12")),
            (D("8475.55"), D("0.14")),
        ],
        irrf_brackets=[
            (D("2428.80"), D("0"), D("0")),
            (D("2826.65"), D("0.075"), D("182.16")),
            (D("3751.05"), D("0.15"), D("394.16")),
            (D("4664.68"), D("0.225"), D("675.49")),
            (None, D("0.275"), D("908.73")),
        ],
        irrf_dependent_deduction=D("189.59"),
        irrf_simplified_discount=D("607.20"),
        irrf_reduction=IrrfReduction(
            full_until=D("5000.00"),
            full_cap=D("312.89"),
            partial_until=D("7350.00"),
            intercept=D("978.62"),
            slope=D("0.133145"),
        ),
    ),
}


def get_tables(year: int) -> TaxTables:
    try:
        return TABLES[year]
    except KeyError as exc:
        raise ValueError(f"No tax tables for {year}. Available: {sorted(TABLES)}") from exc
