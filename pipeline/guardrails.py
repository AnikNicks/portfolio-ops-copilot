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
    python pipeline/guardrails.py validate --schema FinancialFindings \
        --file output/acme-distribution/financial_findings.json

Prints GUARDRAIL_OK or GUARDRAIL_FAIL (with reasons) and exits 0/1 accordingly, so the
calling agent can branch on the exit code rather than parsing prose.
"""

from __future__ import annotations

import argparse
import json
import logging
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

logger = logging.getLogger(__name__)

SCHEMA_MAP = {
    "FinancialFindings": FinancialFindings,
    "DataQualityFindings": DataQualityFindings,
    "ContractRiskFindings": ContractRiskFindings,
    "ActionMemo": ActionMemo,
}


def preflight(company: str) -> list[str]:
    """Return a list of error strings; empty list means the company is safe to diagnose."""
    logger.info("preflight: checking company=%r", company)
    if not COMPANY_SLUG_RE.match(company):
        logger.warning("preflight: rejected invalid company slug %r", company)
        return [
            f"company slug '{company}' is invalid — must be lowercase alphanumeric/hyphen "
            "only (^[a-z0-9][a-z0-9-]*$), rejected before it could be used in any file path "
            "or shell command"
        ]

    company_dir = DATA_ROOT / company
    if not company_dir.is_dir():
        logger.warning("preflight: no data room found for company=%r", company)
        return [f"no data room found at data/synthetic/{company}/"]

    errors = []
    for label in ("financials_raw.xlsx", "crm_export.csv"):
        if not (company_dir / label).is_file():
            errors.append(f"missing required input: {label}")

    contracts_dir = company_dir / "contracts"
    if not contracts_dir.is_dir() or not any(contracts_dir.glob("*.pdf")):
        errors.append("missing required input: at least one contract PDF in contracts/")

    if errors:
        logger.warning("preflight: company=%r failed with %d error(s)", company, len(errors))
    else:
        logger.info("preflight: company=%r OK", company)
    return errors


def validate_output(schema_name: str, file_path: str) -> list[str]:
    """Return a list of error strings; empty list means the file satisfies the schema."""
    logger.info("validate: schema=%s file=%s", schema_name, file_path)
    model = SCHEMA_MAP.get(schema_name)
    if model is None:
        logger.warning("validate: unknown schema %r", schema_name)
        return [f"unknown schema '{schema_name}' — must be one of {sorted(SCHEMA_MAP)}"]

    path = Path(file_path)
    if not path.is_file():
        logger.warning("validate: output file does not exist: %s", file_path)
        return [f"output file does not exist: {file_path}"]

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("validate: could not read %s: %s", file_path, exc)
        return [f"could not read {file_path}: {exc}"]

    try:
        model.model_validate_json(raw)
    except ValidationError as exc:
        logger.warning("validate: %s failed schema %s", file_path, schema_name)
        return [str(exc)]
    except json.JSONDecodeError as exc:
        logger.warning("validate: %s is not valid JSON: %s", file_path, exc)
        return [f"{file_path} is not valid JSON: {exc}"]

    logger.info("validate: %s OK against %s", file_path, schema_name)
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
    parser.add_argument("--verbose", action="store_true", help="Log INFO-level detail to stderr")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_pre = sub.add_parser("preflight", help="Validate inputs before dispatching subagents")
    p_pre.add_argument("--company", required=True)

    p_val = sub.add_parser("validate", help="Validate a subagent's JSON output against its schema")
    p_val.add_argument("--schema", required=True, choices=sorted(SCHEMA_MAP))
    p_val.add_argument("--file", required=True)

    p_rec = sub.add_parser(
        "record-run",
        help="Record a completed, fully-validated run to the SQL run-history log (observability, not a gate)",
    )
    p_rec.add_argument("--company", required=True)
    p_rec.add_argument("--retries", type=int, default=0, help="Total subagent retries the orchestrator needed this run")

    args = parser.parse_args()

    # All logging goes to stderr - stdout is the exact machine-readable channel
    # (GUARDRAIL_OK/FAIL) that diagnose.md parses, and must never carry log noise.
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if args.cmd == "preflight":
        _report(preflight(args.company))
    elif args.cmd == "validate":
        _report(validate_output(args.schema, args.file))
    else:
        # Observability only - never gates the run, so failures here don't use the
        # GUARDRAIL_OK/FAIL vocabulary (diagnose.md is instructed to note, not retry, this).
        try:
            from pipeline.run_history import record_run_from_artifacts
        except ImportError:
            from run_history import record_run_from_artifacts

        try:
            row_id = record_run_from_artifacts(args.company, guardrail_retry_count=args.retries)
        except (FileNotFoundError, KeyError, ValueError) as exc:
            print(f"RUN_RECORD_FAILED: {exc}")
            sys.exit(1)
        print(f"RUN_RECORDED: row {row_id}")
        sys.exit(0)


if __name__ == "__main__":
    main()
