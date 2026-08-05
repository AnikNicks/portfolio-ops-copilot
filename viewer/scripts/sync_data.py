"""Copy the pipeline's committed output into viewer/public/data/ as static build assets.

Run before `vite build` (wired as the `predev`/`prebuild` npm scripts) so the React app has
something to fetch at runtime. Reads only already-committed files (output/*/action_memo.json) -
never regenerates or invokes the pipeline itself, this is a static site.

Usage:
    python scripts/sync_data.py
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

VIEWER_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = VIEWER_ROOT.parent
OUTPUT_DIR = REPO_ROOT / "output"
PUBLIC_DATA_DIR = VIEWER_ROOT / "public" / "data"


def main() -> None:
    if PUBLIC_DATA_DIR.exists():
        shutil.rmtree(PUBLIC_DATA_DIR)
    PUBLIC_DATA_DIR.mkdir(parents=True)

    companies = []
    for company_dir in sorted(OUTPUT_DIR.iterdir()) if OUTPUT_DIR.exists() else []:
        memo_path = company_dir / "action_memo.json"
        if not company_dir.is_dir() or not memo_path.is_file():
            continue
        dest_dir = PUBLIC_DATA_DIR / company_dir.name
        dest_dir.mkdir(parents=True)
        shutil.copy2(memo_path, dest_dir / "action_memo.json")
        companies.append(company_dir.name)
        print(f"synced {company_dir.name}")

    (PUBLIC_DATA_DIR / "manifest.json").write_text(json.dumps({"companies": companies}, indent=2))
    print(f"wrote manifest.json ({len(companies)} companies)")


if __name__ == "__main__":
    main()
