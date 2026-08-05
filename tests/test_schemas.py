from __future__ import annotations

import pytest
from pydantic import ValidationError

from pipeline.schemas import (
    MAX_DOLLAR_IMPACT,
    ActionItem,
    ActionMemo,
    ContractClauseRisk,
    ContractRiskFindings,
    DataQualityFindings,
    FinancialFindings,
    Finding,
)


def _finding(**overrides) -> dict:
    base = dict(
        title="Margin leakage in Q3",
        description="COGS grew faster than revenue.",
        dollar_impact_low=10_000,
        dollar_impact_high=50_000,
        confidence="medium",
        evidence=["row 12"],
    )
    base.update(overrides)
    return base


def _action_item(**overrides) -> dict:
    base = dict(
        problem="p",
        solution="s",
        tradeoffs="t",
        success_metrics="m",
        dollar_impact_low=1_000,
        dollar_impact_high=2_000,
        priority_rank=1,
    )
    base.update(overrides)
    return base


class TestRealCommittedData:
    """The tightened schemas must still accept the real, already-shipped acme-distribution run."""

    def test_financial_findings(self, acme_financial_json):
        FinancialFindings.model_validate_json(acme_financial_json)

    def test_data_quality_findings(self, acme_data_quality_json):
        DataQualityFindings.model_validate_json(acme_data_quality_json)

    def test_contract_risk_findings(self, acme_contract_risk_json):
        ContractRiskFindings.model_validate_json(acme_contract_risk_json)

    def test_action_memo(self, acme_action_memo_json):
        ActionMemo.model_validate_json(acme_action_memo_json)


class TestRealCommittedNorthwindData:
    """The second data room (northwind-fabrication) must validate against the same schemas."""

    def test_financial_findings(self, northwind_financial_json):
        FinancialFindings.model_validate_json(northwind_financial_json)

    def test_data_quality_findings(self, northwind_data_quality_json):
        DataQualityFindings.model_validate_json(northwind_data_quality_json)

    def test_contract_risk_findings(self, northwind_contract_risk_json):
        ContractRiskFindings.model_validate_json(northwind_contract_risk_json)

    def test_action_memo(self, northwind_action_memo_json):
        ActionMemo.model_validate_json(northwind_action_memo_json)


class TestFinding:
    def test_valid(self):
        Finding(**_finding())

    def test_impact_range_inverted(self):
        with pytest.raises(ValidationError):
            Finding(**_finding(dollar_impact_low=100, dollar_impact_high=50))

    def test_negative_impact(self):
        with pytest.raises(ValidationError):
            Finding(**_finding(dollar_impact_low=-1))

    def test_impact_above_ceiling(self):
        with pytest.raises(ValidationError):
            Finding(**_finding(dollar_impact_high=MAX_DOLLAR_IMPACT + 1))

    def test_bad_confidence_enum(self):
        with pytest.raises(ValidationError):
            Finding(**_finding(confidence="extremely-sure"))

    def test_empty_evidence(self):
        with pytest.raises(ValidationError):
            Finding(**_finding(evidence=[]))


class TestFinancialFindings:
    def test_gross_margin_above_100_rejected(self):
        with pytest.raises(ValidationError):
            FinancialFindings(
                company="acme",
                period_covered="FY25",
                revenue=1000,
                gross_margin_pct=150,
                findings=[_finding()],
            )

    def test_negative_gross_margin_allowed(self):
        # No artificial floor - a distressed company can legitimately have negative margin.
        FinancialFindings(
            company="acme",
            period_covered="FY25",
            revenue=1000,
            gross_margin_pct=-40,
            findings=[_finding()],
        )

    def test_negative_revenue_rejected(self):
        with pytest.raises(ValidationError):
            FinancialFindings(
                company="acme",
                period_covered="FY25",
                revenue=-1,
                gross_margin_pct=10,
                findings=[_finding()],
            )

    def test_empty_findings_rejected(self):
        with pytest.raises(ValidationError):
            FinancialFindings(
                company="acme",
                period_covered="FY25",
                revenue=1000,
                gross_margin_pct=10,
                findings=[],
            )


class TestDataQualityFindings:
    def _base(self, **overrides) -> dict:
        base = dict(
            company="acme",
            source_system="CRM",
            record_count=14,
            duplicate_count=10,
            missing_field_rate_pct=57.1,
            findings=[_finding()],
        )
        base.update(overrides)
        return base

    def test_valid(self):
        DataQualityFindings(**self._base())

    def test_negative_record_count_rejected(self):
        with pytest.raises(ValidationError):
            DataQualityFindings(**self._base(record_count=-1))

    def test_duplicate_count_exceeds_record_count_rejected(self):
        with pytest.raises(ValidationError):
            DataQualityFindings(**self._base(record_count=5, duplicate_count=10))

    def test_missing_field_rate_out_of_bounds_rejected(self):
        with pytest.raises(ValidationError):
            DataQualityFindings(**self._base(missing_field_rate_pct=150))


class TestContractClauseRisk:
    def _base(self, **overrides) -> dict:
        base = dict(
            contract_file="vendor_contract_freight.pdf",
            clause_type="auto_renewal",
            quoted_text="Some verbatim clause text.",
            risk_summary="This is risky.",
            dollar_impact_low=1_000,
            dollar_impact_high=2_000,
        )
        base.update(overrides)
        return base

    def test_valid_without_chunk_id(self):
        # chunk_id is optional for backward compatibility with pre-existing runs.
        ContractClauseRisk(**self._base())

    def test_valid_with_chunk_id(self):
        ContractClauseRisk(**self._base(chunk_id="vendor_contract_freight.pdf#4"))

    def test_malformed_chunk_id_rejected(self):
        with pytest.raises(ValidationError):
            ContractClauseRisk(**self._base(chunk_id="not-a-real-chunk-id"))

    def test_bad_clause_type_enum(self):
        with pytest.raises(ValidationError):
            ContractClauseRisk(**self._base(clause_type="unheard_of"))

    def test_empty_quoted_text_rejected(self):
        with pytest.raises(ValidationError):
            ContractClauseRisk(**self._base(quoted_text=""))


class TestContractRiskFindings:
    def test_empty_clause_risks_rejected(self):
        with pytest.raises(ValidationError):
            ContractRiskFindings(company="acme", contracts_reviewed=["a.pdf"], clause_risks=[])

    def test_empty_contracts_reviewed_rejected(self):
        with pytest.raises(ValidationError):
            ContractRiskFindings(
                company="acme",
                contracts_reviewed=[],
                clause_risks=[
                    ContractClauseRisk(
                        contract_file="a.pdf",
                        clause_type="other",
                        quoted_text="x",
                        risk_summary="y",
                        dollar_impact_low=1,
                        dollar_impact_high=2,
                    )
                ],
            )


class TestActionMemo:
    def test_valid(self):
        ActionMemo(
            company="acme",
            summary="s",
            action_items=[_action_item(priority_rank=1), _action_item(priority_rank=2)],
        )

    def test_duplicate_priority_rank_rejected(self):
        with pytest.raises(ValidationError):
            ActionMemo(
                company="acme",
                summary="s",
                action_items=[_action_item(priority_rank=1), _action_item(priority_rank=1)],
            )

    def test_empty_action_items_rejected(self):
        with pytest.raises(ValidationError):
            ActionMemo(company="acme", summary="s", action_items=[])

    def test_action_item_impact_range_inverted(self):
        with pytest.raises(ValidationError):
            ActionItem(**_action_item(dollar_impact_low=100, dollar_impact_high=50))
