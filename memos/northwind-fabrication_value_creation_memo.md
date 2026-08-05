# Northwind Fabrication — Value Creation Memo

## Summary

All three specialist inputs were available and schema-validated (`financial_findings.json`,
`data_quality_findings.json`, `contract_risk_findings.json`). The 13 underlying findings were
consolidated into 7 prioritized action items below, merging findings that share a root cause
(e.g. gross-margin erosion and the EBITDA compression it causes) rather than double-counting the
same dollar leakage twice.

Two cross-agent correlations stand out. First, the financial-analyst's Aug-25 COGS step-up
(attributed to a new subcontractor) sits in the same COGS line as the contract-reviewer's finding
of an automatic, uncapped 6% annual price escalator on Northwind's steel/aluminum supply
agreement with Aldergate Metals — these are not confirmed to be the same vendor, but both are
structural cost-side pressures worth resolving in the same renegotiation cycle, and the
escalator's broken termination cross-reference (Section 3 points to a Warranty clause, not an
exit clause) makes it harder to walk away from if COGS pressure needs to be reversed quickly.
Second, the CRM data-quality audit found several accounts with missing or stale contact data (no
named contact on a $138K account, three simultaneously-missing critical fields on another, an
$88K account with ~21 months of no logged activity) that plausibly compound the
financial-analyst's finding of AR days climbing from 38 to 65 over the year — collections
follow-up is harder when the CRM doesn't reliably tell a rep who to call.

The single largest dollar exposure is the AR-days working-capital drag, followed closely by the
COGS/EBITDA margin erosion; both warrant immediate attention over the smaller CRM and
contract-hygiene items below.

---

## 1. AR Days Climbing — Working Capital Trapped in Receivables

**Dollar impact: $650,000 – $850,000/year**

**Problem:** AR days rose almost every month of 2025, from 38 days (Jan-25) to 65 days (Dec-25),
and the pace accelerated into year-end (+3 days Oct-to-Nov, +4 days Nov-to-Dec); Dec-25 source
notes explicitly flag "AR aging up sharply." Applying the 27-day increase to the Dec-25 revenue
run rate implies roughly $650K–$850K of cash now trapped in receivables instead of being
collected at the Jan-25 pace. Separately, the CRM data-quality audit found unreliable or missing
collections contact data on several accounts: Vantage Tooling Group (N-2004, $138K revenue) has
no named contact; Kestrel Industrial Supply (N-2012) is missing contact, email, and revenue
entirely; and Priory Fabrication Co (N-2011, $88K revenue) has shown no logged activity in ~21
months. Any of these would directly impede timely collections follow-up and plausibly contributes
to the AR-days trend.

**Solution:** Stand up a formal weekly AR-aging review tiered by days-outstanding, with a named
collections owner per account and priority outreach on anything over 45 days past due. In the same
effort, fix the CRM contact gaps identified in the data-quality audit — assign or verify a named
billing contact for every account over $50K in revenue — so collections calls aren't blocked by
missing contact data. Use revolver/factoring only as a short bridge while the underlying process
is fixed, not as the primary remedy.

**Trade-offs:** Tighter credit and collection terms can strain customer relationships and, pushed
too far, risk order volume the company can't afford to lose while margins are already compressing.
Dedicating finance/ops time to a weekly AR review is a real opportunity cost for a lean team.

**Success metrics:** AR days trending back toward the Jan-25 baseline (~38–45 days) within 2
quarters; 100% of accounts over $50K revenue have a verified named contact; DSO tracked and
reported monthly against target.

---

## 2. COGS-Driven Margin Erosion & EBITDA Compression

**Dollar impact: $560,000 – $700,000/year**

**Problem:** Gross margin fell from 30.18% (Jan-25) to 23.62% (Dec-25) while the opex ratio held
flat, isolating the decline to COGS, which rose from 69.82% to 76.38% of revenue; Aug-25 source
notes attribute the step-up to a new subcontractor. That COGS pressure flows straight to the
bottom line: EBITDA margin fell from 11.83% to 4.47% over the same period, with EBITDA dollars
declining every month from Aug-25 through Dec-25 — a $560K–$700K annualized hit — and on the
current trajectory the business could approach EBITDA breakeven within 6-9 months absent
remediation. Separately, the contract review found that Northwind's steel/aluminum supply
agreement (`component_supply_agreement.pdf`, Section 3) carries an automatic, uncapped 6% annual
price escalator on raw-material Base Prices — a structurally similar, compounding cost-side
pressure sitting in the same COGS line, independent of the subcontractor issue but worth
confirming isn't a second contributor during the renegotiation below.

**Solution:** Renegotiate or re-bid the subcontractor relationship onboarded in Aug-25, obtaining
updated unit pricing and at least one competitive quote. In the same review cycle, check whether
the Aldergate Metals steel/aluminum escalator has recently hit (or is approaching) an anniversary
and negotiate a cap or index-based pricing before it compounds further. Track COGS ratio monthly
by input category (subcontracted labor vs. raw material) to separate the two effects going
forward.

**Trade-offs:** Aggressively renegotiating or switching the subcontractor mid-relationship risks
near-term production disruption or quality issues during transition. Pushing back hard on
Aldergate's escalator could strain the primary steel/aluminum supply relationship if Northwind
lacks clean contractual leverage (see item 4 below).

**Success metrics:** COGS ratio back under ~71% of revenue within 2 quarters (the Jan-May-25
average); EBITDA margin recovering toward 8-10%; monthly COGS variance reporting by cost category
in place.

---

## 3. GBP FX Exposure & Unreconciled Gross-Profit Discrepancy (Jun–Jul 2025 UK Order)

**Dollar impact: $150,000 – $360,000**

**Problem:** Jun-25 and Jul-25 revenue/COGS (~$3.12M CAD-equivalent) were reported in GBP and
converted at a single fixed 1.74 rate, leaving that revenue unhedged against FX movement (roughly
$156K of sensitivity at a +/-5% rate move). In the same two months, the source-stated Gross Profit
disagreed with computed Revenue-minus-COGS by a combined $361,120, and this discrepancy was never
explained in the source data.

**Solution:** Reconcile the Jun/Jul-25 GBP-denominated UK order against the underlying ledger to
resolve the $361K gross-profit discrepancy (check for unrecorded returns, rebates, or freight
adjustments). If UK-denominated orders are a recurring or growing channel rather than a one-off,
put a simple forward or spot-hedging policy in place for GBP exposure above a set materiality
threshold.

**Trade-offs:** Hedging costs money and adds operational overhead for what may turn out to be a
one-off order; the reconciliation work competes for finance-team bandwidth with the higher-priority
AR and COGS items above.

**Success metrics:** Gross-profit discrepancy resolved and documented within 1 quarter; a written
FX policy in place before the next non-CAD order exceeding $500K.

---

## 4. Uncapped Steel/Aluminum Price Escalator with a Broken Exit Clause

**Dollar impact: $30,000 – $150,000**

**Problem:** `component_supply_agreement.pdf` Section 3 imposes an automatic, uncapped 6% annual
increase on the Base Prices Northwind pays Aldergate Metals for raw steel/aluminum stock, applied
without further notice or consent and compounding on every anniversary (estimated $15K–$90K in
the first affected year alone). Section 3 states Northwind can avoid the increase only by
terminating "in accordance with Section 6" — but Section 6 is actually the Warranty clause, not a
termination provision; the contract's only real exit is the Section 5 non-renewal notice, which
must be given at least 45 days before the then-current term ends. This broken cross-reference
creates genuine ambiguity about whether Northwind has any contractual way to stop the escalator
mid-term; if resolved against Northwind, exposure could span 1-2 more compounding cycles (roughly
$30K–$150K) before the issue can be renegotiated or the contract allowed to lapse. This sits in
the same COGS line implicated in item 2 above and should be reviewed in the same cycle.

**Solution:** Get outside counsel to formally clarify or fix the Section 3-to-Section 6
cross-reference (most likely intended to reference Section 5, Renewal). Use that leverage point to
negotiate a cap on the escalator — e.g., tying it to a published steel/aluminum price index instead
of a flat 6% — at the next renewal decision point, and calendar the 45-day non-renewal notice
window now so it is never missed by default.

**Trade-offs:** Reopening contract terms with Aldergate could prompt them to seek other
concessions, or take a firmer stance if they believe the ambiguity favors them. If no
better-priced alternative supplier exists, walking away entirely is not a realistic near-term
fallback.

**Success metrics:** Legal opinion on the cross-reference obtained within 30 days; escalator
either capped or replaced with index-based pricing at the next renewal; non-renewal decision date
calendared with a 60-day internal reminder buffer ahead of the 45-day contractual deadline.

---

## 5. Equipment-Maintenance Exclusivity with No SLA Credit and No Early Exit

**Dollar impact: $25,000 – $140,000**

**Problem:** `equipment_maintenance_agreement.pdf` locks Northwind into Precision Machine Services
for the full Initial Term through three compounding provisions: (1) Section 4 exclusivity bars
using any other provider for CNC/stamping maintenance "regardless of Provider's response time or
pricing," precluding competitive bidding (estimated $5K–$30K/year of overpayment risk); (2)
Section 5 sets only a best-efforts 48-hour emergency response target with explicitly no
service-level credit for a missed window, so a slow response carries no contractual remedy
(estimated $10K–$60K of downtime exposure); and (3) Section 6 bars termination for convenience
during the entire Initial Term, meaning none of the above can be fixed by switching providers
early (estimated $10K–$50K of switching-cost/overpayment exposure).

**Solution:** At minimum, negotiate a service-level credit into Section 5 tied to the existing
48-hour target, even without changing the exclusivity or term length. In parallel, benchmark
Precision's current pricing against 2-3 alternative CNC/stamping maintenance providers now, so
Northwind has a ready alternative queued up for the earliest available exit point (end of Initial
Term, then a 90-day notice period per Section 6).

**Trade-offs:** Precision may resist adding SLA credits without a corresponding price increase;
benchmarking alternatives consumes procurement time for savings that may not be realized until the
Initial Term ends.

**Success metrics:** SLA credit clause added, or contract formally benchmarked against at least 2
competitive quotes, within 1 quarter; end-of-Initial-Term date and 90-day notice deadline
calendared.

---

## 6. CRM Duplicate Accounts & Naming Inconsistency

**Dollar impact: $12,500 – $23,500/year**

**Problem:** 4 of Northwind's 12 CRM accounts (33%) are duplicate entries of the same underlying
company, caused by casing/whitespace inconsistency (e.g. "Halden Machine Works" vs "halden
machine works ", "ASHGROVE METALWORKS" vs "Ashgrove Metalworks") or region-naming drift ("AB" vs
"Alberta" on the Redbrook Assemblies pair). This double-counts revenue in territory/segment
rollups and risks two reps independently working the same account. Absent a name-normalization
standard enforced at data entry, this pattern is likely to keep generating new duplicates.

**Solution:** Merge the 4 identified duplicate pairs now (N-2001/N-2002, N-2005/N-2006,
N-2007/N-2008, N-2009/N-2010). Enforce trim-plus-consistent-casing validation on the Company Name
field and a standardized 2-letter Region code at the CRM field level — not just as process
guidance — to prevent recurrence.

**Trade-offs:** Merging records risks losing whichever fields were only populated on the record
being retired (e.g. Thistlewood's phone number) if done hastily; field-level validation may
require a CRM admin/config change that competes with other IT priorities.

**Success metrics:** 0 duplicate accounts found in the next quarterly CRM audit; field-level
casing/format validation live within 60 days.

---

## 7. CRM Missing-Field & Stale-Account Gaps

**Dollar impact: $10,000 – $24,500/year**

**Problem:** Three accounts have data gaps that block segmentation, outreach, or retention: Carrow
Precision Ltd (N-2003) has no Annual Revenue on file; Vantage Tooling Group (N-2004, $138K
revenue) has no named Contact; and Kestrel Industrial Supply (N-2012) is missing Contact, Email,
and Revenue simultaneously, making it effectively invisible outside a raw phone-number lookup.
Separately, Priory Fabrication Co (N-2011, $88K revenue) shows no logged activity in ~21 months,
risking silent churn. The same contact gaps on N-2004 and N-2012 plausibly compound the AR-days
finding above (item 1) by blocking timely collections outreach on affected accounts.

**Solution:** Assign account owners to fill the missing Contact/Revenue/Email fields for N-2003,
N-2004, and N-2012 within the next reporting cycle. Require a same-quarter re-engagement
touchpoint for N-2011 and log the outcome. Add a CRM validation rule that flags any account
missing 2 or more critical fields for manager review.

**Trade-offs:** Filling gaps requires direct account-owner time that could otherwise go to net-new
pipeline; some fields (e.g. Priory's true engagement status) may reveal a genuinely lost account
rather than just a data gap.

**Success metrics:** 0 accounts missing 2+ critical fields within 1 quarter; Priory Fabrication
re-engagement logged within 30 days with a documented outcome (active / at-risk / churned).
