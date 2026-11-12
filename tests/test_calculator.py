from decimal import Decimal as D

import pytest

from clt_vacation import VacationInput, calculate, inss, irrf
from clt_vacation.tables import get_tables

T = get_tables(2026)


# --- INSS ------------------------------------------------------------------

def test_inss_first_bracket():
    assert inss(D("1621.00"), T) == D("121.58")          # 1621.00 * 7.5%


def test_inss_progressive():
    # 121.575 + (2902.84-1621)*9% + (4354.27-2902.84)*12% + (6000-4354.27)*14%
    assert inss(D("6000.00"), T) == D("641.51")


def test_inss_ceiling():
    assert inss(D("8475.55"), T) == D("988.09")
    assert inss(D("20000.00"), T) == D("988.09")


# --- IRRF ------------------------------------------------------------------

def test_irrf_zero_up_to_5000():
    assert irrf(D("5000.00"), inss(D("5000.00"), T), 0, T) == D("0.00")


def test_irrf_partial_reduction():
    gross = D("6000.00")
    paid = inss(gross, T)                                 # 641.51
    base = gross - paid                                   # 5358.49
    table_tax = base * D("0.275") - D("908.73")           # 564.85975
    reduction = D("978.62") - D("0.133145") * gross       # 179.75
    expected = (table_tax - reduction).quantize(D("0.01"))
    assert irrf(gross, paid, 0, T) == expected


def test_irrf_no_reduction_above_7350():
    gross = D("10000.00")
    paid = inss(gross, T)                                 # 988.09
    expected = ((gross - paid) * D("0.275") - D("908.73")).quantize(D("0.01"))
    assert irrf(gross, paid, 0, T) == expected


def test_irrf_uses_simplified_discount_when_better():
    # INSS 300 < simplified discount 607.20, so the simplified discount applies
    gross = D("9000.00")
    expected = ((gross - D("607.20")) * D("0.275") - D("908.73")).quantize(D("0.01"))
    assert irrf(gross, D("300.00"), 0, T) == expected


def test_dependents_lower_the_tax():
    gross = D("12000.00")
    paid = inss(gross, T)
    assert irrf(gross, paid, 2, T) < irrf(gross, paid, 0, T)


# --- Vacation --------------------------------------------------------------

def test_full_30_days():
    r = calculate(VacationInput(monthly_salary=D("3000.00")))
    assert r.vacation_pay == D("3000.00")
    assert r.one_third_bonus == D("1000.00")
    assert r.gross_total == D("4000.00")
    assert r.net_total == r.gross_total - r.inss - r.irrf


def test_sold_days_are_not_taxed():
    with_sale = calculate(VacationInput(D("6000.00"), vacation_days=20, sold_days=10))
    assert with_sale.abono_pecuniario == D("2000.00")
    assert with_sale.abono_one_third == D("666.67")
    taxable = with_sale.vacation_pay + with_sale.one_third_bonus
    assert with_sale.inss == inss(taxable, T)


def test_variable_pay_enters_the_daily_rate():
    r = calculate(VacationInput(D("3000.00"), average_variable_pay=D("600.00")))
    assert r.vacation_pay == D("3600.00")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"sold_days": 11},
        {"vacation_days": 25, "sold_days": 10},
        {"vacation_days": 4},
        {"dependents": -1},
    ],
)
def test_invalid_inputs(kwargs):
    with pytest.raises(ValueError):
        calculate(VacationInput(D("3000.00"), **kwargs))
