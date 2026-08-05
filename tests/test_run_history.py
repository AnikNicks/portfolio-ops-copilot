from __future__ import annotations

from pipeline.run_history import (
    all_runs,
    most_retries,
    record_run,
    record_run_from_artifacts,
    summary_by_company,
)


def test_record_run_and_read_back(tmp_path):
    db = tmp_path / "test.db"
    record_run(
        "acme-distribution",
        guardrail_pass=True,
        guardrail_retry_count=1,
        grounding_score=100.0,
        dollar_impact_low=1000,
        dollar_impact_high=2000,
        db_path=db,
    )
    rows = all_runs(db_path=db)
    assert len(rows) == 1
    assert rows[0]["company"] == "acme-distribution"
    assert rows[0]["guardrail_pass"] == 1
    assert rows[0]["grounding_score"] == 100.0


def test_summary_by_company_averages(tmp_path):
    db = tmp_path / "test.db"
    record_run("acme", guardrail_pass=True, grounding_score=100.0, db_path=db)
    record_run("acme", guardrail_pass=True, grounding_score=80.0, db_path=db)
    record_run("other-co", guardrail_pass=True, grounding_score=50.0, db_path=db)

    summary = {row["company"]: row for row in summary_by_company(db_path=db)}
    assert summary["acme"]["run_count"] == 2
    assert summary["acme"]["avg_grounding_score"] == 90.0
    assert summary["other-co"]["run_count"] == 1


def test_most_retries_orders_descending(tmp_path):
    db = tmp_path / "test.db"
    record_run("low-retry", guardrail_pass=True, guardrail_retry_count=0, db_path=db)
    record_run("high-retry", guardrail_pass=True, guardrail_retry_count=3, db_path=db)

    top = most_retries(limit=5, db_path=db)
    assert top[0]["company"] == "high-retry"
    assert top[0]["guardrail_retry_count"] == 3


def test_record_run_from_artifacts_uses_real_acme_output(tmp_path):
    db = tmp_path / "test.db"
    row_id = record_run_from_artifacts("acme-distribution", guardrail_retry_count=0, db_path=db)
    assert row_id == 1

    rows = all_runs(db_path=db)
    assert rows[0]["grounding_score"] == 100.0
    assert rows[0]["dollar_impact_low"] > 0
    assert rows[0]["dollar_impact_high"] >= rows[0]["dollar_impact_low"]
