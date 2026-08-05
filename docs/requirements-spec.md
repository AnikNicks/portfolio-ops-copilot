# Requirements spec — Portfolio Ops Copilot

One-pager framing the original scoping decisions for this project, the way a discovery session
would be documented before build starts.

## Problem statement

A portfolio company's first 90 days after a PE close typically produce three disconnected data
exports — a messy financial P&L, a CRM/ERP export, and a folder of vendor/customer contracts —
and no single view of what's actually wrong or what it's worth fixing. Operating partners read
all three by hand and write the diagnostic memo themselves. That's slow, inconsistent between
analysts, and easy to get wrong on the contract side in particular (clause citations from memory
are exactly the kind of thing that quietly drifts from what the contract actually says).

## Success criteria

- A single command (`/diagnose <company>`) turns the three raw exports into one prioritized,
  dollar-quantified memo in the fixed Problem → Solution → Trade-offs → Success-Metrics format.
- Every dollar-impact estimate traces back to specific evidence (a cell range, an Account ID, a
  contract clause) — no unsourced numbers.
- Every contract citation is retrieval-grounded: a real `chunk_id` and a verbatim quote, checked
  automatically (`evals/grounding_eval.py`) rather than trusted on the agent's word.
- Malformed agent output is caught and retried automatically (`pipeline/guardrails.py`), not
  silently passed downstream.
- The pipeline generalizes across at least two differently-messy data rooms, not hand-tuned to
  one example (`data/synthetic/{acme-distribution,northwind-fabrication}/`).

## Explicitly out of scope, and why

- **Payments, subscriptions, billing.** This is a portfolio/engineering-demonstration piece, not
  a product being sold — adding a paywall would misrepresent what it is.
- **Multi-tenant auth / user accounts.** Nothing here handles real client data or needs to
  distinguish between users; auth would add real complexity for a demo that doesn't need it.
- **Production-scale infrastructure** (managed database, horizontal scaling, monitoring/alerting
  beyond structured logging). Two synthetic companies at demo scale is enough to prove the
  architecture and the guardrail discipline; scaling infrastructure that will never see real load
  would be performative, not useful.
- **Refactoring a real legacy codebase.** This is greenfield synthetic data by design — the point
  is to demonstrate the AI-native multi-agent methodology and its guardrails, not to also tell a
  legacy-migration story that would need an actual legacy codebase to be honest.

## What "done" means here

Tests passing, CI green, the grounding eval automatically re-verifying the "no hallucinated
citations" claim on every run, two data rooms proven to work end to end, and documentation that
accurately describes what's built — not a system handling real client data or real money.
