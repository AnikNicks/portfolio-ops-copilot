"""Pydantic contracts for every inter-agent JSON handoff in the diagnostic pipeline.

Every subagent's output must validate against one of these models before the
synthesis-writer is allowed to consume it. See CLAUDE.md for the handoff map, and
`pipeline/guardrails.py` for the CLI that actually runs this validation as a code-enforced
gate rather than trusting the LLM to self-conform.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, model_validator

# Sanity ceiling on any single dollar-impact estimate. Real observed values top out around
# $1.09M; this only exists to catch a typo/unit-scale error (e.g. an agent writing 150000000
# instead of 150000), not to constrain realistic estimates.
MAX_DOLLAR_IMPACT = 25_000_000

_CHUNK_ID_PATTERN = re.compile(r"^[\w.\-]+\.pdf#\d+$")


class Finding(BaseModel):
    title: str
    description: str
    dollar_impact_low: float = Field(ge=0, le=MAX_DOLLAR_IMPACT, description="Low end of estimated annual $ impact")
    dollar_impact_high: float = Field(ge=0, le=MAX_DOLLAR_IMPACT, description="High end of estimated annual $ impact")
    confidence: Literal["low", "medium", "high"]
    evidence: list[str] = Field(min_length=1, description="Source refs, e.g. cell ranges, row ids, clause ids")

    @model_validator(mode="after")
    def _impact_range_is_ordered(self) -> Finding:
        if self.dollar_impact_high < self.dollar_impact_low:
            raise ValueError("dollar_impact_high must be >= dollar_impact_low")
        return self


class FinancialFindings(BaseModel):
    company: str
    period_covered: str
    revenue: float = Field(ge=0)
    gross_margin_pct: float = Field(
        le=100, description="No floor - a distressed company can have deeply negative margin"
    )
    findings: list[Finding] = Field(min_length=1)


class DataQualityFindings(BaseModel):
    company: str
    source_system: str
    record_count: int = Field(ge=0)
    duplicate_count: int = Field(ge=0)
    missing_field_rate_pct: float = Field(ge=0, le=100)
    findings: list[Finding] = Field(min_length=1)

    @model_validator(mode="after")
    def _duplicates_within_record_count(self) -> DataQualityFindings:
        if self.duplicate_count > self.record_count:
            raise ValueError("duplicate_count cannot exceed record_count")
        return self


class ContractClauseRisk(BaseModel):
    contract_file: str
    clause_type: Literal["auto_renewal", "pricing_escalator", "termination", "other"]
    quoted_text: str = Field(
        min_length=1,
        description="Verbatim quote pulled via the retrieval tool, never paraphrased from memory",
    )
    risk_summary: str
    chunk_id: str | None = Field(
        default=None,
        description="chunk_id (e.g. 'vendor_contract_freight.pdf#4') the quoted_text was pulled from. "
        "Optional for backward compatibility with runs predating this field, but the contract-reviewer "
        "agent should always populate it going forward instead of only embedding the reference in prose.",
    )
    dollar_impact_low: float = Field(ge=0, le=MAX_DOLLAR_IMPACT)
    dollar_impact_high: float = Field(ge=0, le=MAX_DOLLAR_IMPACT)

    @model_validator(mode="after")
    def _impact_range_is_ordered(self) -> ContractClauseRisk:
        if self.dollar_impact_high < self.dollar_impact_low:
            raise ValueError("dollar_impact_high must be >= dollar_impact_low")
        return self

    @model_validator(mode="after")
    def _chunk_id_well_formed(self) -> ContractClauseRisk:
        if self.chunk_id is not None and not _CHUNK_ID_PATTERN.match(self.chunk_id):
            raise ValueError(f"chunk_id {self.chunk_id!r} must look like '<filename>.pdf#<index>'")
        return self


class ContractRiskFindings(BaseModel):
    company: str
    contracts_reviewed: list[str] = Field(min_length=1)
    clause_risks: list[ContractClauseRisk] = Field(min_length=1)


class ActionItem(BaseModel):
    problem: str = Field(min_length=1)
    solution: str = Field(min_length=1)
    tradeoffs: str = Field(min_length=1)
    success_metrics: str = Field(min_length=1)
    dollar_impact_low: float = Field(ge=0, le=MAX_DOLLAR_IMPACT)
    dollar_impact_high: float = Field(ge=0, le=MAX_DOLLAR_IMPACT)
    priority_rank: int

    @model_validator(mode="after")
    def _impact_range_is_ordered(self) -> ActionItem:
        if self.dollar_impact_high < self.dollar_impact_low:
            raise ValueError("dollar_impact_high must be >= dollar_impact_low")
        return self


class ActionMemo(BaseModel):
    company: str
    summary: str
    action_items: list[ActionItem] = Field(min_length=1)

    @model_validator(mode="after")
    def _priority_ranks_are_unique(self) -> ActionMemo:
        ranks = [item.priority_rank for item in self.action_items]
        if len(ranks) != len(set(ranks)):
            raise ValueError("priority_rank values must be unique across action_items")
        return self
