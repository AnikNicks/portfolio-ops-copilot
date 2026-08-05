"""SQLite-backed run-history observability for the /diagnose pipeline.

Every successful /diagnose run gets one row recorded here: which company, when, whether the
grounding eval passed and at what score, how many subagent retries the guardrail layer needed,
and the total dollar-impact range of the resulting memo. This turns "measure and communicate
impact - establish baselines, document results" (see CLAUDE.md) into something queryable across
runs instead of a one-off number in a chat transcript.

The database file (run_history.db, gitignored - local run state, not portfolio content) lives
next to this module. Not a general-purpose ORM layer on purpose: query_runs() below runs real
SQL, not method chains hiding it.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(__file__).resolve().parent / "run_history.db"

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    guardrail_pass INTEGER NOT NULL,
    guardrail_retry_count INTEGER NOT NULL DEFAULT 0,
    grounding_score REAL,
    dollar_impact_low REAL,
    dollar_impact_high REAL
)
"""


def _connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(_SCHEMA)
    return conn


def record_run(
    company: str,
    *,
    guardrail_pass: bool,
    guardrail_retry_count: int = 0,
    grounding_score: float | None = None,
    dollar_impact_low: float | None = None,
    dollar_impact_high: float | None = None,
    db_path: Path = DB_PATH,
) -> int:
    """Insert one run record. Returns the new row's id."""
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "INSERT INTO runs (company, guardrail_pass, guardrail_retry_count, grounding_score, "
            "dollar_impact_low, dollar_impact_high) VALUES (?, ?, ?, ?, ?, ?)",
            (
                company,
                int(guardrail_pass),
                guardrail_retry_count,
                grounding_score,
                dollar_impact_low,
                dollar_impact_high,
            ),
        )
        conn.commit()
        logger.info("record_run: company=%r row id=%d", company, cur.lastrowid)
        return cur.lastrowid
    finally:
        conn.close()


def record_run_from_artifacts(company: str, *, guardrail_retry_count: int = 0, db_path: Path = DB_PATH) -> int:
    """Convenience wrapper for the CLI/orchestrator: compute grounding score and dollar-impact
    totals from the company's own committed output artifacts, then record_run()."""
    try:
        from evals.grounding_eval import evaluate  # local import - evals/ isn't a hard dep of pipeline/
    except ImportError:
        # Invoked as `python pipeline/guardrails.py` (script dir on sys.path, not repo root).
        sys.path.insert(0, str(REPO_ROOT))
        from evals.grounding_eval import evaluate

    grounding_report = evaluate(company)

    memo_path = REPO_ROOT / "output" / company / "action_memo.json"
    memo = json.loads(memo_path.read_text(encoding="utf-8"))
    dollar_low = sum(item["dollar_impact_low"] for item in memo["action_items"])
    dollar_high = sum(item["dollar_impact_high"] for item in memo["action_items"])

    return record_run(
        company,
        guardrail_pass=True,
        guardrail_retry_count=guardrail_retry_count,
        grounding_score=grounding_report["score_pct"],
        dollar_impact_low=dollar_low,
        dollar_impact_high=dollar_high,
        db_path=db_path,
    )


def all_runs(db_path: Path = DB_PATH) -> list[dict]:
    conn = _connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM runs ORDER BY timestamp DESC").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def summary_by_company(db_path: Path = DB_PATH) -> list[dict]:
    conn = _connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT company,
                   COUNT(*) AS run_count,
                   AVG(grounding_score) AS avg_grounding_score,
                   AVG(guardrail_retry_count) AS avg_retry_count,
                   MAX(dollar_impact_high) AS max_dollar_impact_high
            FROM runs
            GROUP BY company
            ORDER BY company
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def most_retries(limit: int = 5, db_path: Path = DB_PATH) -> list[dict]:
    conn = _connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT company, timestamp, guardrail_retry_count FROM runs "
            "ORDER BY guardrail_retry_count DESC, timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
