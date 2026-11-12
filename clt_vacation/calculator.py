"""CLT vacation pay calculator (férias + 1/3, abono pecuniário, INSS and IRRF)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import ROUND_HALF_UP, Decimal as D
from typing import Dict

from .tables import TaxTables, get_tables

CENT = D("0.01")


def money(value: D) -> D:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def inss(contribution_base: D, tables: TaxTables) -> D:
    """Employee INSS, progressive bracket by bracket, capped at the ceiling."""
    total = D("0")
    lower = D("0")
    for upper, rate in tables.inss_brackets:
        if contribution_base <= lower:
            break
        taxable_slice = min(contribution_base, upper) - lower
        total += taxable_slice * rate
        lower = upper
    return money(total)


def irrf(gross_taxable: D, inss_paid: D, dependents: int, tables: TaxTables) -> D:
    """Monthly withholding tax.

    1. Deductions: the larger of (INSS + dependents) and the simplified discount.
    2. Progressive table: base * rate - amount to deduct.
    3. 2026 reduction (Lei 15.270/2025), driven by gross taxable income.
    """
    legal = inss_paid + tables.irrf_dependent_deduction * dependents
    deductions = max(legal, tables.irrf_simplified_discount)
    base = max(gross_taxable - deductions, D("0"))

    tax = D("0")
    for upper, rate, deduct in tables.irrf_brackets:
        if upper is None or base <= upper:
            tax = base * rate - deduct
            break
    tax = max(tax, D("0"))

    red = tables.irrf_reduction
    if red is not None:
        if gross_taxable <= red.full_until:
            tax -= min(tax, red.full_cap)
        elif gross_taxable <= red.partial_until:
            tax -= max(red.intercept - red.slope * gross_taxable, D("0"))
    return money(max(tax, D("0")))


@dataclass
class VacationInput:
    monthly_salary: D
    average_variable_pay: D = D("0")   # average overtime, commissions etc.
    vacation_days: int = 30
    sold_days: int = 0                 # abono pecuniário (max 1/3 of the entitlement)
    dependents: int = 0
    year: int = 2026

    def validate(self) -> None:
        if self.monthly_salary <= 0:
            raise ValueError("monthly_salary must be positive")
        if self.sold_days < 0 or self.sold_days > 10:
            raise ValueError("sold_days must be between 0 and 10 (1/3 of 30 days)")
        if self.vacation_days < 5:
            raise ValueError("a vacation period cannot be shorter than 5 days")
        if self.vacation_days + self.sold_days > 30:
            raise ValueError("vacation_days + sold_days cannot exceed 30")
        if self.dependents < 0:
            raise ValueError("dependents cannot be negative")


@dataclass
class VacationResult:
    vacation_pay: D
    one_third_bonus: D
    abono_pecuniario: D
    abono_one_third: D
    gross_total: D
    inss: D
    irrf: D
    net_total: D

    def as_dict(self) -> Dict[str, str]:
        return {k: f"{v:.2f}" for k, v in asdict(self).items()}


def calculate(data: VacationInput) -> VacationResult:
    data.validate()
    tables = get_tables(data.year)
    daily = (data.monthly_salary + data.average_variable_pay) / D(30)

    vacation_pay = money(daily * data.vacation_days)
    one_third = money(vacation_pay / D(3))
    abono = money(daily * data.sold_days)
    abono_third = money(abono / D(3))

    # Abono pecuniário and its 1/3 are not subject to INSS or IRRF.
    taxable = vacation_pay + one_third
    inss_due = inss(taxable, tables)
    irrf_due = irrf(taxable, inss_due, data.dependents, tables)

    gross = vacation_pay + one_third + abono + abono_third
    return VacationResult(
        vacation_pay=vacation_pay,
        one_third_bonus=one_third,
        abono_pecuniario=abono,
        abono_one_third=abono_third,
        gross_total=gross,
        inss=inss_due,
        irrf=irrf_due,
        net_total=gross - inss_due - irrf_due,
    )
