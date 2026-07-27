"""Pydantic contracts for every inter-agent JSON handoff in the diagnostic pipeline.

Every subagent's output must validate against one of these models before the
synthesis-writer is allowed to consume it. See CLAUDE.md for the handoff map, and
`pipeline/guardrails.py` for the CLI that actually runs this validation as a code-enforced
gate rather than trusting the LLM to self-conform.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Finding(BaseModel):
    title: str
    description: str
    dollar_impact_low: float = Field(description="Low end of estimated annual $ impact")
    dollar_impact_high: float = Field(description="High end of estimated annual $ impact")
    confidence: Literal["low", "medium", "high"]
    evidence: list[str] = Field(default_factory=list, description="Source refs, e.g. cell ranges, row ids, clause ids")

    @model_validator(mode="after")
    def _impact_range_is_ordered(self) -> "Finding":
        if self.dollar_impact_high < self.dollar_impact_low:
            raise ValueError("dollar_impact_high must be >= dollar_impact_low")
        return self


class FinancialFindings(BaseModel):
    company: str
    period_covered: str
    revenue: float
    gross_margin_pct: float
    findings: list[Finding]


class DataQualityFindings(BaseModel):
    company: str
    source_system: str
    record_count: int
    duplicate_count: int
    missing_field_rate_pct: float
    findings: list[Finding]


class ContractClauseRisk(BaseModel):
    contract_file: str
    clause_type: Literal["auto_renewal", "pricing_escalator", "termination", "other"]
    quoted_text: str = Field(
        min_length=1,
        description="Verbatim quote pulled via the retrieval tool, never paraphrased from memory",
    )
    risk_summary: str
    dollar_impact_low: float
    dollar_impact_high: float

    @model_validator(mode="after")
    def _impact_range_is_ordered(self) -> "ContractClauseRisk":
        if self.dollar_impact_high < self.dollar_impact_low:
            raise ValueError("dollar_impact_high must be >= dollar_impact_low")
        return self


class ContractRiskFindings(BaseModel):
    company: str
    contracts_reviewed: list[str]
    clause_risks: list[ContractClauseRisk]


class ActionItem(BaseModel):
    problem: str = Field(min_length=1)
    solution: str = Field(min_length=1)
    tradeoffs: str = Field(min_length=1)
    success_metrics: str = Field(min_length=1)
    dollar_impact_low: float
    dollar_impact_high: float
    priority_rank: int

    @model_validator(mode="after")
    def _impact_range_is_ordered(self) -> "ActionItem":
        if self.dollar_impact_high < self.dollar_impact_low:
            raise ValueError("dollar_impact_high must be >= dollar_impact_low")
        return self


class ActionMemo(BaseModel):
    company: str
    summary: str
    action_items: list[ActionItem]
