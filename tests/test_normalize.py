from __future__ import annotations

import pytest
from openpyxl import Workbook

import pipeline.normalize as normalize_module
from pipeline.normalize import normalize

HEADERS = ["Month", "Revenue", "COGS", "Gross Profit", "OpEx", "AR (days)", "Notes"]


def _write_financials_xlsx(path, data_rows: list[list]) -> None:
    """Build a workbook matching the real export's quirky layout: a title row, a blank row,
    then the real header on row 3 - mirrors data/synthetic/*/generate_financials.py."""
    wb = Workbook()
    ws = wb.active
    ws.append(["Acme-like Inc. - Monthly P&L (unaudited)"])
    ws.append([])
    ws.append(HEADERS)
    for row in data_rows:
        ws.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


@pytest.fixture
def fake_company(tmp_path, monkeypatch):
    """Returns a function that writes financials_raw.xlsx for a fake company and patches
    normalize.py's REPO_ROOT so normalize() reads it."""
    monkeypatch.setattr(normalize_module, "REPO_ROOT", tmp_path)

    def _make(company: str, data_rows: list[list]) -> None:
        xlsx_path = tmp_path / "data" / "synthetic" / company / "financials_raw.xlsx"
        _write_financials_xlsx(xlsx_path, data_rows)

    return _make


class TestNormalizeQuirksInIsolation:
    def test_blank_row_is_dropped(self, fake_company):
        fake_company(
            "fake-co",
            [
                ["Jan-25", 100000, 60000, 40000, 30000, 45, ""],
                [None, None, None, None, None, None, None],
                ["Feb-25", 110000, 65000, 45000, 31000, 47, ""],
            ],
        )
        result = normalize("fake-co")
        assert len(result["months"]) == 2
        assert [m["month"] for m in result["months"]] == ["Jan-25", "Feb-25"]

    def test_formula_as_text_cogs_is_evaluated(self, fake_company):
        fake_company(
            "fake-co",
            [
                ["Jan-25", 100000, "100000*0.6", 40000, 30000, 45, ""],
            ],
        )
        result = normalize("fake-co")
        record = result["months"][0]
        assert record["cogs_cad"] == 60000.0
        assert any("unevaluated formula" in issue for issue in result["normalization_issues"])

    def test_usd_flagged_month_converted_to_cad(self, fake_company):
        fake_company(
            "fake-co",
            [
                ["Jan-25", 100000, 60000, 40000, 30000, 45, "USD - not converted"],
            ],
        )
        result = normalize("fake-co")
        record = result["months"][0]
        assert record["revenue_cad"] == round(100000 * normalize_module.USD_TO_CAD, 2)
        assert record["cogs_cad"] == round(60000 * normalize_module.USD_TO_CAD, 2)
        assert any("converted to CAD" in issue for issue in result["normalization_issues"])

    def test_gbp_flagged_month_converted_to_cad(self, fake_company):
        fake_company(
            "fake-co",
            [
                ["Jan-25", 100000, 60000, 40000, 30000, 45, "GBP - not converted"],
            ],
        )
        result = normalize("fake-co")
        record = result["months"][0]
        rate = normalize_module.CURRENCY_RATES["GBP"]
        assert record["revenue_cad"] == round(100000 * rate, 2)
        assert record["cogs_cad"] == round(60000 * rate, 2)
        assert any("GBP" in issue and "converted to CAD" in issue for issue in result["normalization_issues"])

    def test_thousands_separated_string_is_parsed(self, fake_company):
        fake_company(
            "fake-co",
            [
                ["Jan-25", "1,234,000", 60000, 40000, 30000, 45, ""],
            ],
        )
        result = normalize("fake-co")
        record = result["months"][0]
        assert record["revenue_cad"] == 1234000.0
        assert any("thousands-separated" in issue for issue in result["normalization_issues"])

    def test_non_usd_month_not_converted(self, fake_company):
        fake_company(
            "fake-co",
            [
                ["Jan-25", 100000, 60000, 40000, 30000, 45, "some other note"],
            ],
        )
        result = normalize("fake-co")
        assert result["months"][0]["revenue_cad"] == 100000.0

    def test_stated_gross_profit_mismatch_flagged(self, fake_company):
        fake_company(
            "fake-co",
            [
                # Revenue - COGS = 40000, but stated Gross Profit column says 99000 - disagreement.
                ["Jan-25", 100000, 60000, 99000, 30000, 45, ""],
            ],
        )
        result = normalize("fake-co")
        assert result["months"][0]["gross_profit_cad"] == 40000.0  # uses computed, not stated
        assert any("disagrees" in issue for issue in result["normalization_issues"])

    def test_missing_company_raises_file_not_found(self, fake_company):
        with pytest.raises(FileNotFoundError):
            normalize("never-created")


class TestNormalizeAgainstRealAcmeFile:
    """Integration test against the real committed financials_raw.xlsx."""

    def test_record_count_after_dropping_blank_row(self):
        result = normalize("acme-distribution")
        assert len(result["months"]) == 12

    def test_nov_25_formula_cogs_evaluated(self):
        result = normalize("acme-distribution")
        nov = next(m for m in result["months"] if m["month"] == "Nov-25")
        assert nov["cogs_cad"] == 391251.0

    def test_dec_25_usd_conversion_and_disagreement_flagged(self):
        result = normalize("acme-distribution")
        dec = next(m for m in result["months"] if m["month"] == "Dec-25")
        assert dec["revenue_cad"] == 669930.0
        assert dec["cogs_cad"] == 447513.24
        assert dec["gross_profit_cad"] == 222416.76
        assert dec["ebitda_cad"] == -36513.24
        issues_text = " ".join(result["normalization_issues"])
        assert "Dec-25" in issues_text and "converted to CAD" in issues_text
        assert any("Dec-25" in i and "disagrees" in i for i in result["normalization_issues"])
