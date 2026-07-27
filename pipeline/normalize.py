"""Normalize a portfolio company's messy financials export into clean structured JSON.

Invoked as a tool by the financial-analyst subagent - never pasted raw into a prompt.

Usage:
    python pipeline/normalize.py --company acme-distribution

Prints one JSON object to stdout: monthly records (all in CAD, formulas evaluated,
blank rows dropped) plus a list of data-quality issues encountered during normalization
(useful as evidence for the financial-analyst's findings).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

USD_TO_CAD = 1.37  # fixed rate for a reproducible demo; not a live FX feed
REPO_ROOT = Path(__file__).resolve().parent.parent


def coerce_number(value, issues: list[str], month: str, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and re.match(r"^=?[\d.]+\*[\d.]+$", value.strip()):
        # Export artifact: an unevaluated arithmetic expression like "601000*0.651" left as
        # literal text instead of a computed value
        match = re.match(r"^=?([\d.]+)\*([\d.]+)$", value.strip())
        if match:
            issues.append(f"{month}: {field} was an unevaluated formula string ('{value}'); evaluated it directly")
            return float(match.group(1)) * float(match.group(2))
        issues.append(f"{month}: {field} was an unparseable formula string ('{value}'); dropped")
        return None
    issues.append(f"{month}: {field} had unexpected type {type(value).__name__} ('{value}'); dropped")
    return None


def normalize(company: str) -> dict:
    src = REPO_ROOT / "data" / "synthetic" / company / "financials_raw.xlsx"
    if not src.exists():
        raise FileNotFoundError(f"no financials_raw.xlsx for company '{company}' at {src}")

    raw = pd.read_excel(src, sheet_name=0, header=2)  # row 3 (0-indexed 2) is the real header
    raw = raw.dropna(how="all")  # drop the blank export row

    issues: list[str] = []
    records = []
    for _, row in raw.iterrows():
        month = str(row["Month"]).strip()
        notes_val = row.get("Notes")
        notes = str(notes_val).strip() if pd.notna(notes_val) else ""

        revenue = coerce_number(row["Revenue"], issues, month, "Revenue")
        cogs = coerce_number(row["COGS"], issues, month, "COGS")
        opex = coerce_number(row["OpEx"], issues, month, "OpEx")
        ar_days = coerce_number(row["AR (days)"], issues, month, "AR (days)")

        if "USD" in notes.upper():
            issues.append(f"{month}: figures reported in USD per Notes column; converted to CAD at {USD_TO_CAD}")
            if revenue is not None:
                revenue = round(revenue * USD_TO_CAD, 2)
            if cogs is not None:
                cogs = round(cogs * USD_TO_CAD, 2)
            if opex is not None:
                opex = round(opex * USD_TO_CAD, 2)

        gross_profit = round(revenue - cogs, 2) if revenue is not None and cogs is not None else None
        gross_margin_pct = round(100 * gross_profit / revenue, 2) if gross_profit is not None and revenue else None
        ebitda = round(gross_profit - opex, 2) if gross_profit is not None and opex is not None else None

        stated_gp = row.get("Gross Profit")
        if isinstance(stated_gp, (int, float)) and gross_profit is not None and abs(stated_gp - gross_profit) > 1:
            issues.append(
                f"{month}: stated Gross Profit ({stated_gp}) disagrees with Revenue-COGS ({gross_profit}); "
                f"using computed value"
            )

        records.append({
            "month": month,
            "revenue_cad": revenue,
            "cogs_cad": cogs,
            "gross_profit_cad": gross_profit,
            "gross_margin_pct": gross_margin_pct,
            "opex_cad": opex,
            "ebitda_cad": ebitda,
            "ar_days": ar_days,
            "source_notes": notes or None,
        })

    return {"company": company, "months": records, "normalization_issues": issues}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", required=True)
    args = parser.parse_args()
    try:
        result = normalize(args.company)
    except FileNotFoundError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
