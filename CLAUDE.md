# Portfolio Ops Copilot

A multi-agent Claude Code pipeline that turns a messy portfolio-company data export into a
prioritized, dollar-quantified value-creation memo — the kind of diagnostic a private-equity
operating/consulting team hands a portfolio company after close.

## Pipeline shape

`/diagnose <company>` (orchestrator) dispatches three specialist subagents in parallel, each of
which reads its inputs from the synthetic "data room" and writes one JSON findings file to
`output/<company>/`. A `synthesis-writer` subagent then reads all three JSON files and produces
the final memo.

| Subagent | Input | Output |
|---|---|---|
| `financial-analyst` | `data/synthetic/<company>/financials_raw.xlsx` (via `pipeline/normalize.py`) | `output/<company>/financial_findings.json` |
| `data-quality-auditor` | `data/synthetic/<company>/crm_export.csv` | `output/<company>/data_quality_findings.json` |
| `contract-reviewer` | `data/synthetic/<company>/contracts/*` | `output/<company>/contract_risk_findings.json` |
| `synthesis-writer` | all three JSON files above | `memos/<company>_value_creation_memo.md` |

## Conventions

- **Schemas are the contract.** Every JSON handoff between agents must validate against a model
  in `pipeline/schemas.py`. If a subagent's output doesn't match its schema, that's a bug in the
  subagent's prompt, not a reason to loosen the schema.
- **Data access goes through tools, not raw prompting.** Financial normalization happens in
  `pipeline/normalize.py` (pandas) and is invoked as a tool call — never paste raw spreadsheet
  contents into a prompt. Contract text is discovered via the Docker MCP filesystem server's
  `list_directory`/`search_files` tools, but actual content comes from
  `pipeline/extract_contract_text.py` (pypdf), which chunks each contract by numbered section
  and returns a `chunk_id` per clause. **Do not use the MCP filesystem server's `read_file` on a
  PDF** — it returns raw compressed PDF bytes, not text (confirmed by hand: piping a contract PDF
  through it just returns PDF stream syntax, unreadable). The contract-reviewer cites a specific
  `chunk_id`/quoted text for every finding instead of paraphrasing from memory — that's what
  retrieval-only actually buys you, and it's the real failure story: pointing an agent at an MCP
  filesystem tool without checking what it actually returns for a given file type is exactly how
  you get hallucinated clause numbers.
- **Subagents get the minimum tools they need.** Each `.claude/agents/*.md` file declares an
  explicit `tools:` allowlist. `contract-reviewer` in particular has no `Bash` and no unscoped
  filesystem access — retrieval-only by construction, not by instruction.
- **No secrets in the repo.** Any credential a tool needs is set via `docker mcp secret set` and
  injected into the container at runtime. `.mcp.json` only ever points at
  `docker mcp gateway run` — it never contains a raw token.
- **The memo format is fixed and non-negotiable:** every generated memo follows
  **Problem → Solution → Trade-offs → Success Metrics**, per section, per action item, with a
  dollar-impact estimate attached to each recommendation. This mirrors the
  Problem/Solution/Trade-offs/Success-Metrics rubric standard to PE operating-partner and
  consulting deliverables — don't deviate from it.
- **Synthetic data lives under `data/synthetic/<company>/`.** Treat each subfolder as a
  self-contained fake data room; nothing outside `data/synthetic/` should ever be read by a
  subagent.
