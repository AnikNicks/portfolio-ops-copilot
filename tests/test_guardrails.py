from __future__ import annotations

import subprocess
import sys

import pytest

from pipeline.guardrails import preflight, validate_output


class TestPreflight:
    def test_valid_company_passes(self):
        assert preflight("acme-distribution") == []

    @pytest.mark.parametrize("slug", ["Bad Slug!", "../etc", "UPPERCASE", "-leading-hyphen"])
    def test_invalid_slug_rejected(self, slug):
        errors = preflight(slug)
        assert errors
        assert "invalid" in errors[0]

    def test_unknown_company_reports_missing_data_room(self):
        errors = preflight("no-such-company-xyz")
        assert errors == ["no data room found at data/synthetic/no-such-company-xyz/"]

    def test_missing_input_file_reported_specifically(self, tmp_path, monkeypatch, repo_root):
        import pipeline.guardrails as guardrails_module

        fake_data_root = tmp_path / "synthetic"
        company_dir = fake_data_root / "acme-fake"
        company_dir.mkdir(parents=True)
        (company_dir / "crm_export.csv").write_text("a,b\n1,2\n")
        (company_dir / "contracts").mkdir()
        (company_dir / "contracts" / "x.pdf").write_bytes(b"%PDF-1.4\n")

        monkeypatch.setattr(guardrails_module, "DATA_ROOT", fake_data_root)
        errors = preflight("acme-fake")
        assert "missing required input: financials_raw.xlsx" in errors

    def test_missing_contracts_reported(self, tmp_path, monkeypatch):
        import pipeline.guardrails as guardrails_module

        fake_data_root = tmp_path / "synthetic"
        company_dir = fake_data_root / "acme-fake"
        company_dir.mkdir(parents=True)
        (company_dir / "financials_raw.xlsx").write_bytes(b"")
        (company_dir / "crm_export.csv").write_text("a,b\n1,2\n")

        monkeypatch.setattr(guardrails_module, "DATA_ROOT", fake_data_root)
        errors = preflight("acme-fake")
        assert any("contract PDF" in e for e in errors)


class TestValidateOutput:
    def test_real_files_pass(self, acme_output_dir):
        assert validate_output("FinancialFindings", str(acme_output_dir / "financial_findings.json")) == []
        assert validate_output("DataQualityFindings", str(acme_output_dir / "data_quality_findings.json")) == []
        assert validate_output("ContractRiskFindings", str(acme_output_dir / "contract_risk_findings.json")) == []
        assert validate_output("ActionMemo", str(acme_output_dir / "action_memo.json")) == []

    def test_missing_file(self):
        errors = validate_output("FinancialFindings", "does/not/exist.json")
        assert errors and "does not exist" in errors[0]

    def test_malformed_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json")
        errors = validate_output("FinancialFindings", str(bad))
        assert errors

    def test_schema_violating_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text('{"company": "x"}')  # missing required fields
        errors = validate_output("FinancialFindings", str(bad))
        assert errors

    def test_unknown_schema_name(self, acme_output_dir):
        errors = validate_output("NotARealSchema", str(acme_output_dir / "financial_findings.json"))
        assert errors and "unknown schema" in errors[0]


class TestStdoutContract:
    """diagnose.md parses stdout for exactly GUARDRAIL_OK / GUARDRAIL_FAIL - lock this down."""

    def test_preflight_ok_stdout_exact(self, repo_root):
        result = subprocess.run(
            [sys.executable, "pipeline/guardrails.py", "preflight", "--company", "acme-distribution"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "GUARDRAIL_OK"

    def test_preflight_fail_stdout_starts_correctly(self, repo_root):
        result = subprocess.run(
            [sys.executable, "pipeline/guardrails.py", "preflight", "--company", "Not-Valid!"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert result.stdout.splitlines()[0] == "GUARDRAIL_FAIL"
