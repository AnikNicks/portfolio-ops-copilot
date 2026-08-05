"""Query the /diagnose run-history SQLite log (pipeline/run_history.db).

Usage:
    python pipeline/query_runs.py --summary        # per-company aggregates
    python pipeline/query_runs.py --most-retries    # runs that needed the most subagent retries
    python pipeline/query_runs.py --all             # every run, most recent first
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from pipeline.run_history import DB_PATH, all_runs, most_retries, summary_by_company
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from pipeline.run_history import DB_PATH, all_runs, most_retries, summary_by_company


def _print_table(rows: list[dict]) -> None:
    if not rows:
        print("(no runs recorded yet)")
        return
    headers = list(rows[0].keys())
    widths = [max(len(h), max(len(str(r[h])) for r in rows)) for h in headers]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths, strict=True)))
    for row in rows:
        print("  ".join(str(row[h]).ljust(w) for h, w in zip(headers, widths, strict=True)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true", help="Per-company aggregates")
    parser.add_argument("--most-retries", action="store_true", help="Runs with the most subagent retries")
    parser.add_argument("--all", action="store_true", help="Every recorded run, most recent first")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"no run history yet at {DB_PATH} - run /diagnose at least once first")
        return

    if args.most_retries:
        _print_table(most_retries())
    elif args.all:
        _print_table(all_runs())
    else:
        _print_table(summary_by_company())


if __name__ == "__main__":
    main()
