"""Automated grounding/citation check for contract-reviewer output.

The contract-reviewer subagent is retrieval-only by construction (see CLAUDE.md): every clause
it cites is supposed to carry a chunk_id and a verbatim quote pulled from
pipeline/extract_contract_text.py's output, never paraphrased from memory. Until now that
"zero hallucinated citations" claim was only ever checked by hand, once, in a chat session, and
never captured as a repeatable script. This module makes it a real, CI-enforceable check: it
re-extracts the source PDFs fresh (not a cached copy) and verifies every cited chunk_id actually
exists and every quoted_text actually appears in that chunk's text.

Usage:
    python evals/grounding_eval.py --company acme-distribution
    python evals/grounding_eval.py --company acme-distribution --threshold 90

Prints GROUNDING_OK or GROUNDING_FAIL (with a per-entry breakdown and a grounded/total score) and
exits 0/1 accordingly - same stdout convention as pipeline/guardrails.py, so it can be dropped
into the same kind of gate.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from pipeline.extract_contract_text import extract_chunks
    from pipeline.schemas import ContractRiskFindings
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from pipeline.extract_contract_text import extract_chunks
    from pipeline.schemas import ContractRiskFindings

REPO_ROOT = Path(__file__).resolve().parent.parent

# Scoped to a specific contract_file at call time, so a reference to another contract's chunk_id
# in the same risk_summary can't be mistaken for this entry's citation.
_CHUNK_REF_RE = re.compile(r"([\w.\-]+\.pdf)#(\d+)")


def _normalize_whitespace(text: str) -> str:
    # pypdf wraps lines mid-sentence (e.g. "one hundred\ntwenty (120) days"), so verbatim-quote
    # matching against chunk text needs whitespace collapsed first, or every real quote fails.
    return re.sub(r"\s+", " ", text).strip()


def _find_cited_chunk_id(contract_file: str, chunk_id: str | None, risk_summary: str) -> str | None:
    """Prefer the structured chunk_id field; fall back to a `<file>#<n>` reference embedded in
    risk_summary prose, scoped to this entry's own contract_file (covers pre-chunk_id-field runs)."""
    if chunk_id:
        return chunk_id
    for match in _CHUNK_REF_RE.finditer(risk_summary):
        if match.group(1) == contract_file:
            return f"{match.group(1)}#{match.group(2)}"
    return None


def evaluate(company: str) -> dict:
    findings_path = REPO_ROOT / "output" / company / "contract_risk_findings.json"
    findings = ContractRiskFindings.model_validate_json(findings_path.read_text(encoding="utf-8"))

    # Re-extract every referenced contract fresh - this is the whole point, not a cached copy.
    chunk_maps: dict[str, dict[str, str]] = {}
    for contract_file in findings.contracts_reviewed:
        chunks = extract_chunks(company, contract_file)
        chunk_maps[contract_file] = {c["chunk_id"]: c["text"] for c in chunks}

    results = []
    for entry in findings.clause_risks:
        cited_chunk_id = _find_cited_chunk_id(entry.contract_file, entry.chunk_id, entry.risk_summary)
        chunk_map = chunk_maps.get(entry.contract_file, {})

        if cited_chunk_id is None:
            results.append(
                {
                    "contract_file": entry.contract_file,
                    "clause_type": entry.clause_type,
                    "status": "FAIL",
                    "reason": "uncited - no chunk_id found",
                }
            )
            continue
        if cited_chunk_id not in chunk_map:
            results.append(
                {
                    "contract_file": entry.contract_file,
                    "clause_type": entry.clause_type,
                    "status": "FAIL",
                    "reason": f"fabricated chunk_id: {cited_chunk_id}",
                }
            )
            continue

        chunk_text = _normalize_whitespace(chunk_map[cited_chunk_id])
        quoted = _normalize_whitespace(entry.quoted_text)
        if quoted not in chunk_text:
            results.append(
                {
                    "contract_file": entry.contract_file,
                    "clause_type": entry.clause_type,
                    "status": "FAIL",
                    "reason": f"quoted_text not found verbatim in {cited_chunk_id}",
                }
            )
            continue

        results.append(
            {
                "contract_file": entry.contract_file,
                "clause_type": entry.clause_type,
                "status": "PASS",
                "chunk_id": cited_chunk_id,
            }
        )

    total = len(results)
    grounded = sum(1 for r in results if r["status"] == "PASS")
    score_pct = round(100 * grounded / total, 2) if total else 0.0
    return {"company": company, "total": total, "grounded": grounded, "score_pct": score_pct, "results": results}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", required=True)
    parser.add_argument(
        "--threshold",
        type=float,
        default=100.0,
        help="Minimum grounded-citation score (percent) required to pass. Default 100.",
    )
    args = parser.parse_args()

    report = evaluate(args.company)

    for r in report["results"]:
        marker = "OK " if r["status"] == "PASS" else "FAIL"
        detail = r.get("chunk_id") or r.get("reason")
        print(f"  [{marker}] {r['contract_file']} ({r['clause_type']}): {detail}")

    print(f"score: {report['grounded']}/{report['total']} ({report['score_pct']}%)")

    if report["score_pct"] >= args.threshold:
        print("GROUNDING_OK")
        sys.exit(0)
    print("GROUNDING_FAIL")
    sys.exit(1)


if __name__ == "__main__":
    main()
