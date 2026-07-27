"""Code-enforced guardrails for the /diagnose orchestrator.

Two checkpoints, both run by the orchestrator (never by the specialist subagents
themselves, so none of them need extra tool permissions):

  preflight   - runs BEFORE any subagent is dispatched. Rejects an unsafe/unknown
                company slug and confirms the required input files actually exist,
                so a typo'd or malicious company argument never reaches a Task
                dispatch or a shell command.
  validate    - runs AFTER a subagent writes its output JSON. Loads the pydantic
                model from pipeline/schemas.py and validates the file against it for
                real, instead of trusting the subagent's own claim that it matched
                the schema "exactly."

Usage:
    python pipeline/guardrails.py preflight --company acme-distribution
    python pipeline/guardrails.py validate --schema FinancialFindings --file output/acme-distribution/financial_findings.json

Prints GUARDRAIL_OK or GUARDRAIL_FAIL (with reasons) and exits 0/1 accordingly, so the
calling agent can branch on the exit code rather than parsing prose.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from pipeline.schemas import (
        ActionMemo,
        ContractRiskFindings,
        DataQualityFindings,
        FinancialFindings,
    )
except ImportError:
    from schemas import (
        ActionMemo,
        ContractRiskFindings,
        DataQualityFindings,
        FinancialFindings,
    )

from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "data" / "synthetic"

COMPANY_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

SCHEMA_MAP = {
    "FinancialFindings": FinancialFindings,
    "DataQualityFindings": DataQualityFindings,
    "ContractRiskFindings": ContractRiskFindings,
    "ActionMemo": ActionMemo,
}


def preflight(company: str) -> list[str]:
    """Return a list of error strings; empty list means the company is safe to diagnose."""
    if not COMPANY_SLUG_RE.match(company):
        return [
            f"company slug '{company}' is invalid — must be lowercase alphanumeric/hyphen "
            "only (^[a-z0-9][a-z0-9-]*$), rejected before it could be used in any file path "
            "or shell command"
        ]

    company_dir = DATA_ROOT / company
    if not company_dir.is_dir():
        return [f"no data room found at data/synthetic/{company}/"]

    errors = []
    for label in ("financials_raw.xlsx", "crm_export.csv"):
        if not (company_dir / label).is_file():
            errors.append(f"missing required input: {label}")

    contracts_dir = company_dir / "contracts"
    if not contracts_dir.is_dir() or not any(contracts_dir.glob("*.pdf")):
        errors.append("missing required input: at least one contract PDF in contracts/")

    return errors


def validate_output(schema_name: str, file_path: str) -> list[str]:
    """Return a list of error strings; empty list means the file satisfies the schema."""
    model = SCHEMA_MAP.get(schema_name)
    if model is None:
        return [f"unknown schema '{schema_name}' — must be one of {sorted(SCHEMA_MAP)}"]

    path = Path(file_path)
    if not path.is_file():
        return [f"output file does not exist: {file_path}"]

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"could not read {file_path}: {exc}"]

    try:
        model.model_validate_json(raw)
    except ValidationError as exc:
        return [str(exc)]
    except json.JSONDecodeError as exc:
        return [f"{file_path} is not valid JSON: {exc}"]

    return []


def _report(errors: list[str]) -> None:
    if errors:
        print("GUARDRAIL_FAIL")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)
    print("GUARDRAIL_OK")
    sys.exit(0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_pre = sub.add_parser("preflight", help="Validate inputs before dispatching subagents")
    p_pre.add_argument("--company", required=True)

    p_val = sub.add_parser("validate", help="Validate a subagent's JSON output against its schema")
    p_val.add_argument("--schema", required=True, choices=sorted(SCHEMA_MAP))
    p_val.add_argument("--file", required=True)

    args = parser.parse_args()

    if args.cmd == "preflight":
        _report(preflight(args.company))
    else:
        _report(validate_output(args.schema, args.file))


if __name__ == "__main__":
    main()
