"""Command line: python -m clt_vacation --salary 6500 --days 20 --sell 10 --dependents 1"""

from __future__ import annotations

import argparse
import json
from decimal import Decimal as D

from .calculator import VacationInput, calculate

LABELS = {
    "vacation_pay": "Vacation pay (férias)",
    "one_third_bonus": "1/3 constitutional bonus",
    "abono_pecuniario": "Sold days (abono pecuniário)",
    "abono_one_third": "1/3 on sold days",
    "gross_total": "Gross total",
    "inss": "(-) INSS",
    "irrf": "(-) IRRF",
    "net_total": "Net to pay",
}


def main() -> None:
    p = argparse.ArgumentParser(description="Brazilian CLT vacation pay calculator")
    p.add_argument("--salary", required=True, type=D, help="monthly base salary (BRL)")
    p.add_argument("--variable", default=D("0"), type=D, help="average variable pay (BRL)")
    p.add_argument("--days", default=30, type=int, help="vacation days taken")
    p.add_argument("--sell", default=0, type=int, help="days sold (abono pecuniário, max 10)")
    p.add_argument("--dependents", default=0, type=int)
    p.add_argument("--year", default=2026, type=int)
    p.add_argument("--json", action="store_true", help="print JSON instead of a table")
    a = p.parse_args()

    result = calculate(VacationInput(a.salary, a.variable, a.days, a.sell, a.dependents, a.year))
    values = result.as_dict()
    if a.json:
        print(json.dumps(values, indent=2))
        return
    width = max(len(v) for v in LABELS.values())
    for key, label in LABELS.items():
        sep = "-" * (width + 16) if key in ("gross_total", "net_total") else None
        if sep:
            print(sep)
        print(f"{label:<{width}}  R$ {values[key]:>10}")


if __name__ == "__main__":
    main()
