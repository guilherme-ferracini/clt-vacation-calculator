# CLT Vacation Pay Calculator

[![tests](https://github.com/guilherme-ferracini/clt-vacation-calculator/actions/workflows/tests.yml/badge.svg)](https://github.com/guilherme-ferracini/clt-vacation-calculator/actions)

A small, fully tested Python engine that calculates Brazilian CLT vacation pay: **férias + 1/3**, **abono pecuniário** (sold days), **INSS** and **IRRF**, including the 2026 income tax reduction from **Lei nº 15.270/2025**.

## Why this exists

At the accounting firm where I lead automation, vacation calculations used to be done by hand: look up the year's tables, apply progressive INSS bracket by bracket, decide between legal deductions and the simplified discount, then apply the new 2026 reduction. That is slow, and a single wrong bracket means a wrong payslip.

This repo shows the approach I use when automating that kind of routine:

- **Rules as data.** Tax tables live in `tables.py`, one entry per year, so a new year means a new entry and past calculations stay reproducible.
- **Exact money math.** `Decimal` everywhere and rounding only at defined points. No floats.
- **Tests as the spec.** Every rule (brackets, ceiling, simplified discount, 2026 reduction, abono exemption, input validation) has a test.

> The original production version lives in a private platform. This is a clean, standalone rewrite with no client data.

## What it calculates

| Item | Rule |
|---|---|
| Daily rate | (monthly salary + average variable pay) / 30 |
| Vacation pay | daily rate × vacation days |
| 1/3 bonus | vacation pay / 3 |
| Abono pecuniário | daily rate × sold days (max 10) and its 1/3, **exempt** from INSS and IRRF |
| INSS | progressive, bracket by bracket, capped at the 2026 ceiling (R$ 8,475.55) |
| IRRF | taxable = vacation + 1/3; deductions = max(INSS + dependents, simplified discount); progressive table; then the 2026 reduction (zero up to R$ 5,000, decreasing up to R$ 7,350) |

## Quickstart

```bash
pip install -r requirements.txt

# 20 days of vacation, 10 days sold, one dependent
python -m clt_vacation --salary 6500 --days 20 --sell 10 --dependents 1
```

```
Vacation pay (férias)         R$    4333.33
1/3 constitutional bonus      R$    1444.44
Sold days (abono pecuniário)  R$    2166.67
1/3 on sold days              R$     722.22
--------------------------------------------
Gross total                   R$    8666.66
(-) INSS                      R$     610.40
(-) IRRF                      R$     250.82
--------------------------------------------
Net to pay                    R$    7805.44
```

Use `--json` for machine-readable output, or call it from Python:

```python
from decimal import Decimal
from clt_vacation import VacationInput, calculate

result = calculate(VacationInput(monthly_salary=Decimal("6500"), vacation_days=20, sold_days=10))
print(result.as_dict())
```

## Tests

```bash
python -m pytest -q
```

## Assumptions and limits

- Vacation is taxed separately from the month's salary, and the 2026 reduction is applied to the vacation's taxable income. Payroll systems may differ on edge cases, so validate against your own payroll provider before using it in production.
- Not covered yet: 13th-salary advance, union contributions, alimony, proportional vacation on termination.

## Sources

- INSS 2026: Portaria Interministerial MPS/MF nº 13/2026
- IRRF 2026: monthly table in force since May 2025, plus the reduction in Lei nº 15.270/2025

## License

MIT
