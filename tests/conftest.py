from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def acme_output_dir() -> Path:
    return REPO_ROOT / "output" / "acme-distribution"


@pytest.fixture
def acme_financial_json(acme_output_dir: Path) -> str:
    return (acme_output_dir / "financial_findings.json").read_text(encoding="utf-8")


@pytest.fixture
def acme_data_quality_json(acme_output_dir: Path) -> str:
    return (acme_output_dir / "data_quality_findings.json").read_text(encoding="utf-8")


@pytest.fixture
def acme_contract_risk_json(acme_output_dir: Path) -> str:
    return (acme_output_dir / "contract_risk_findings.json").read_text(encoding="utf-8")


@pytest.fixture
def acme_action_memo_json(acme_output_dir: Path) -> str:
    return (acme_output_dir / "action_memo.json").read_text(encoding="utf-8")
