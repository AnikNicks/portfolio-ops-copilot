"""Portfolio Ops Copilot demo front end.

Pick a synthetic company, see its messy raw exports, click "Run Diagnostic" to invoke the
Claude Code multi-agent pipeline (/diagnose), and see the generated value-creation memo
rendered next to the raw input. This is the before/after moment for the demo - the pipeline
itself lives entirely in .claude/agents/ and .claude/commands/, not in this file.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "synthetic"
MEMOS_DIR = REPO_ROOT / "memos"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def describe_stream_event(raw_line: str) -> str | None:
    """Turn one `claude --output-format stream-json` line into a short human-readable
    progress message, or None if it's not worth showing (thinking-token counters, rate-limit
    pings, etc). Unknown-but-parseable events fall back to their type so nothing goes silent;
    unparseable lines are shown truncated rather than dropped, so real errors stay visible."""
    import json as _json

    try:
        event = _json.loads(raw_line)
    except _json.JSONDecodeError:
        return raw_line[:200] if raw_line.strip() else None

    etype = event.get("type")

    if etype == "system":
        if event.get("subtype") == "init":
            return "session started"
        return None  # thinking_tokens / background_tasks_changed counters - too noisy to show

    if etype == "rate_limit_event":
        return None

    if etype == "assistant":
        parts = []
        for block in event.get("message", {}).get("content", []):
            btype = block.get("type")
            if btype == "text" and block.get("text", "").strip():
                parts.append(block["text"].strip().splitlines()[0][:160])
            elif btype == "tool_use":
                name = block.get("name", "tool")
                inp = block.get("input", {}) or {}
                if name in ("Agent", "Task"):
                    parts.append(
                        f"-> dispatching subagent: {inp.get('subagent_type', '?')} "
                        f"({inp.get('description', '')})"
                    )
                elif name == "Bash":
                    parts.append(f"-> bash: {str(inp.get('command', ''))[:100]}")
                elif name == "Write":
                    parts.append(f"-> write: {inp.get('file_path', '?')}")
                elif name.startswith("mcp__"):
                    parts.append(f"-> mcp tool: {name}")
                else:
                    parts.append(f"-> {name}")
        return " | ".join(parts) if parts else None

    if etype == "user":
        for block in event.get("message", {}).get("content", []) or []:
            if not isinstance(block, dict) or block.get("type") != "tool_result":
                continue
            tool_result = event.get("tool_use_result")
            if isinstance(tool_result, dict) and tool_result.get("isAsync"):
                return f"   (subagent running in background: {tool_result.get('description', '')})"
            if block.get("is_error"):
                return f"   ERROR: {str(block.get('content', ''))[:200]}"
        return None

    if etype == "result":
        if event.get("is_error"):
            return f"FAILED: {event.get('result', 'unknown error')[:300]}"
        return f"done ({event.get('subtype', 'success')}, {event.get('num_turns', '?')} turns)"

    return None


st.set_page_config(page_title="Portfolio Ops Copilot", layout="wide")
st.title("Portfolio Ops Copilot")
st.caption(
    "Messy portfolio-company export in -> prioritized, dollar-quantified value-creation memo out. "
    "Powered by a Claude Code multi-agent pipeline (financial-analyst, data-quality-auditor, "
    "contract-reviewer, synthesis-writer) reading through a Docker MCP-scoped data room."
)

companies = sorted(p.name for p in DATA_DIR.iterdir() if p.is_dir()) if DATA_DIR.exists() else []

with st.sidebar:
    st.header("Manage portfolio companies")
    st.caption(
        "Files are saved under data/synthetic/<company>/ — the same data room the pipeline and "
        "the Docker MCP filesystem server (already scoped to that directory) both read from, so "
        "anything you add here works with the existing agents unchanged."
    )

    st.subheader("Upload files")
    target_mode = st.radio(
        "Company", ["Add to existing", "Create new"], horizontal=True, disabled=not companies
    )
    if target_mode == "Add to existing" and companies:
        target_slug = st.selectbox("Existing company", companies, key="upload_target")
    else:
        target_name = st.text_input("New company name", placeholder="e.g. Northwind Fabrication")
        target_slug = slugify(target_name)

    up_financials = st.file_uploader(
        "Financials export (.xlsx) — replaces the existing one", type=["xlsx"], key="up_fin"
    )
    up_crm = st.file_uploader(
        "CRM / ERP export (.csv) — replaces the existing one", type=["csv"], key="up_crm"
    )
    up_contracts = st.file_uploader(
        "Contracts (.pdf) — added alongside existing ones",
        type=["pdf"],
        accept_multiple_files=True,
        key="up_contracts",
    )

    if st.button("Save files"):
        if not target_slug:
            st.error("Enter or select a company first.")
        elif not (up_financials or up_crm or up_contracts):
            st.error("Upload at least one file.")
        else:
            company_dir = DATA_DIR / target_slug
            company_dir.mkdir(parents=True, exist_ok=True)
            saved = []
            if up_financials is not None:
                (company_dir / "financials_raw.xlsx").write_bytes(up_financials.getvalue())
                saved.append("financials_raw.xlsx")
            if up_crm is not None:
                (company_dir / "crm_export.csv").write_bytes(up_crm.getvalue())
                saved.append("crm_export.csv")
            if up_contracts:
                contracts_dir = company_dir / "contracts"
                contracts_dir.mkdir(exist_ok=True)
                for uploaded in up_contracts:
                    (contracts_dir / uploaded.name).write_bytes(uploaded.getvalue())
                    saved.append(f"contracts/{uploaded.name}")
            st.success(f"Saved to '{target_slug}': {', '.join(saved)}")
            st.rerun()

    st.divider()
    st.subheader("Files in a company's data room")
    if companies:
        manage_slug = st.selectbox("Company", companies, key="manage_slug")
        manage_dir = DATA_DIR / manage_slug

        manage_fin = manage_dir / "financials_raw.xlsx"
        manage_crm = manage_dir / "crm_export.csv"
        manage_contracts_dir = manage_dir / "contracts"

        any_files = False
        for label, path in [
            ("financials_raw.xlsx", manage_fin),
            ("crm_export.csv", manage_crm),
        ]:
            if path.exists():
                any_files = True
                c1, c2 = st.columns([4, 1])
                c1.text(label)
                if c2.button("Remove", key=f"rm_{label}"):
                    path.unlink()
                    st.rerun()

        if manage_contracts_dir.exists():
            for pdf in sorted(manage_contracts_dir.glob("*.pdf")):
                any_files = True
                c1, c2 = st.columns([4, 1])
                c1.text(f"contracts/{pdf.name}")
                if c2.button("Remove", key=f"rm_contract_{pdf.name}"):
                    pdf.unlink()
                    st.rerun()

        if not any_files:
            st.caption(f"No files yet for '{manage_slug}'.")
    else:
        st.caption("No companies yet — upload files above to create the first one.")

if not companies:
    st.error(f"No portfolio companies yet — use the sidebar to add one.")
    st.stop()

company = st.selectbox("Portfolio company", companies)
company_dir = DATA_DIR / company
memo_path = MEMOS_DIR / f"{company}_value_creation_memo.md"

col_before, col_after = st.columns(2)

with col_before:
    st.subheader("Before — raw data room")

    financials_path = company_dir / "financials_raw.xlsx"
    if financials_path.exists():
        st.markdown("**financials_raw.xlsx**")
        try:
            df = pd.read_excel(financials_path, sheet_name=0, header=2).dropna(how="all")
            st.dataframe(df, use_container_width=True, height=250)
        except Exception as exc:  # noqa: BLE001 - demo-grade preview, not a pipeline path
            st.warning(f"Couldn't preview spreadsheet: {exc}")

    crm_path = company_dir / "crm_export.csv"
    if crm_path.exists():
        st.markdown("**crm_export.csv**")
        st.dataframe(pd.read_csv(crm_path), use_container_width=True, height=250)

    contracts_dir = company_dir / "contracts"
    if contracts_dir.exists():
        st.markdown("**contracts/**")
        for f in sorted(contracts_dir.glob("*.pdf")):
            st.text(f"- {f.name}")

with col_after:
    st.subheader("After — value-creation memo")

    run_clicked = st.button("Run Diagnostic", type="primary")

    if run_clicked:
        st.caption(f"Running `/diagnose {company}` — this dispatches 3 subagents in parallel "
                   "then a synthesis pass, typically ~8-10 minutes total.")
        log_placeholder = st.empty()
        log_lines: list[str] = []

        proc = subprocess.Popen(
            [
                "claude", "-p", f"/diagnose {company}",
                "--permission-mode", "acceptEdits",
                "--allowedTools",
                "Task,Bash,Read,Write,mcp__MCP_DOCKER__read_file,mcp__MCP_DOCKER__list_directory",
                "--output-format", "stream-json",
                "--verbose",
            ],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        final_event_is_error = False
        for raw_line in proc.stdout:  # type: ignore[union-attr]
            raw_line = raw_line.rstrip("\n")
            if not raw_line.strip():
                continue
            message = describe_stream_event(raw_line)
            if message is None:
                continue
            # A "   ERROR" line is a single tool call failing mid-run (e.g. a subagent
            # retrying a write after Claude Code's read-before-write guard) - the agent
            # routinely recovers from these. Only the terminal `result` event's is_error
            # flag (surfaced here as "FAILED") means the run actually didn't complete.
            if message.startswith("FAILED"):
                final_event_is_error = True
            log_lines.append(message)
            log_placeholder.code("\n".join(log_lines[-30:]), language=None)
        returncode = proc.wait()

        if returncode != 0 or final_event_is_error:
            st.error("Pipeline run failed — see the log above for the last events before failure.")
        else:
            st.success("Diagnostic complete.")

    if memo_path.exists():
        # Streamlit's markdown treats $...$ as LaTeX, which mangles a memo full of dollar
        # amounts - escape literal $ so "$1.12M" renders as text, not a broken math span.
        memo_text = memo_path.read_text(encoding="utf-8").replace("$", "\\$")
        st.markdown(memo_text)
    else:
        st.info(
            f"No memo yet for {company}. Click **Run Diagnostic** to generate "
            f"{memo_path.relative_to(REPO_ROOT)}."
        )

st.divider()
st.caption(
    "Data room is a synthetic, fictional company — nothing here is a real client. "
    "MCP filesystem access is read-only and scoped to data/synthetic/ via a dedicated Docker MCP profile."
)
