"""Extract and chunk a contract PDF's text for the contract-reviewer subagent.

Invoked as a tool - never pasted raw. The MCP filesystem server's read_file returns raw
PDF bytes (compressed streams), not extracted text, so this is the sanctioned path for
actually reading contract content. Chunking by numbered section, with each chunk tagged,
is what makes retrieval-only review possible: the reviewer cites a chunk_id/quoted_text
instead of inventing a clause number from memory.

Usage:
    python pipeline/extract_contract_text.py --company acme-distribution --file vendor_contract_freight.pdf
    python pipeline/extract_contract_text.py --company acme-distribution --list
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

REPO_ROOT = Path(__file__).resolve().parent.parent
SECTION_HEADING_RE = re.compile(r"^\d+\.\s+\S")


def contracts_dir(company: str) -> Path:
    return REPO_ROOT / "data" / "synthetic" / company / "contracts"


def list_contracts(company: str) -> list[str]:
    d = contracts_dir(company)
    if not d.exists():
        raise FileNotFoundError(f"no contracts directory for company '{company}' at {d}")
    return sorted(p.name for p in d.glob("*.pdf"))


def extract_chunks(company: str, filename: str) -> list[dict]:
    path = contracts_dir(company) / filename
    if not path.exists():
        raise FileNotFoundError(f"no such contract file: {path}")

    reader = PdfReader(str(path))
    full_text = "\n".join(page.extract_text() or "" for page in reader.pages)

    # Split on numbered section headings (e.g. "4. Renewal") so each chunk is one clause -
    # this is what lets the reviewer quote a specific, citable section instead of a vague
    # paraphrase of the whole document.
    lines = full_text.splitlines()
    chunks: list[dict] = []
    current_heading = "Preamble"
    current_lines: list[str] = []

    def flush():
        text = "\n".join(current_lines).strip()
        if text:
            chunks.append({
                "chunk_id": f"{filename}#{len(chunks)}",
                "heading": current_heading,
                "text": text,
            })

    for line in lines:
        if SECTION_HEADING_RE.match(line.strip()):
            flush()
            current_heading = line.strip()
            current_lines = []
        else:
            current_lines.append(line)
    flush()

    return chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", required=True)
    parser.add_argument("--file", help="Contract PDF filename within the company's contracts/ dir")
    parser.add_argument("--list", action="store_true", help="List available contract files instead of extracting")
    args = parser.parse_args()

    try:
        if args.list:
            print(json.dumps({"company": args.company, "contracts": list_contracts(args.company)}, indent=2))
        else:
            if not args.file:
                parser.error("--file is required unless --list is given")
            chunks = extract_chunks(args.company, args.file)
            print(json.dumps({"company": args.company, "file": args.file, "chunks": chunks}, indent=2))
    except FileNotFoundError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
