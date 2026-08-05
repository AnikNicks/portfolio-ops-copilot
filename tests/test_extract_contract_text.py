from __future__ import annotations

import re

import pytest

from pipeline.extract_contract_text import extract_chunks, list_contracts


def _normalize_whitespace(text: str) -> str:
    # pypdf's extraction wraps lines mid-sentence (e.g. "one hundred\ntwenty (120) days"),
    # so substring checks against known clause text need whitespace collapsed first - the
    # same normalization the grounding eval applies when matching quoted_text to chunk text.
    return re.sub(r"\s+", " ", text)


class TestListContracts:
    def test_returns_both_real_contracts(self):
        contracts = list_contracts("acme-distribution")
        assert contracts == ["vendor_contract_freight.pdf", "vendor_contract_raw_materials.pdf"]

    def test_missing_company_raises(self):
        with pytest.raises(FileNotFoundError):
            list_contracts("no-such-company-xyz")


class TestExtractChunks:
    def test_chunk_ids_are_well_formed(self):
        chunks = extract_chunks("acme-distribution", "vendor_contract_freight.pdf")
        assert len(chunks) > 0
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_id"] == f"vendor_contract_freight.pdf#{i}"
            assert "text" in chunk and "heading" in chunk

    def test_known_auto_renewal_clause_is_present(self):
        chunks = extract_chunks("acme-distribution", "vendor_contract_freight.pdf")
        combined_text = _normalize_whitespace("\n".join(c["text"] for c in chunks))
        assert "one hundred twenty (120) days" in combined_text

    def test_known_escalator_clause_present_in_raw_materials_contract(self):
        chunks = extract_chunks("acme-distribution", "vendor_contract_raw_materials.pdf")
        combined_text = _normalize_whitespace("\n".join(c["text"] for c in chunks))
        assert "four percent (4%)" in combined_text

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            extract_chunks("acme-distribution", "does_not_exist.pdf")
