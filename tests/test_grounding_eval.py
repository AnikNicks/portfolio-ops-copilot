from __future__ import annotations

from evals.grounding_eval import evaluate


def test_acme_distribution_is_fully_grounded():
    report = evaluate("acme-distribution")
    assert report["total"] == 6
    assert report["grounded"] == report["total"]
    assert report["score_pct"] == 100.0
    assert all(r["status"] == "PASS" for r in report["results"])


def test_every_entry_resolves_a_chunk_id():
    report = evaluate("acme-distribution")
    for r in report["results"]:
        assert r["status"] == "PASS"
        assert r["chunk_id"].startswith(r["contract_file"] + "#")
