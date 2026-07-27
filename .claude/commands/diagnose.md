---
description: Run the full value-creation diagnostic pipeline for one portfolio company
argument-hint: <company>
---

Run the full Portfolio Ops Copilot diagnostic for company `$ARGUMENTS`.

**Always regenerate.** Dispatch all four subagents fresh and overwrite their output files, even
if `output/$ARGUMENTS/*.json` or the memo already exist from a previous run. Pre-existing output
is not a reason to skip an agent — this command means "run the diagnostic now," not "run it if it
hasn't been run before."

## Guardrails

This pipeline has two code-enforced guardrail checkpoints, both run via `pipeline/guardrails.py`
(never skip these or replace them with your own eyeball check — they are real pydantic
validation, not a formality):

- **Preflight, before any subagent is dispatched** — rejects an unsafe or unknown company slug
  and confirms the required input files exist.
- **Post-output validation, after every JSON file a subagent writes** — validates the file
  against its pydantic model in `pipeline/schemas.py` for real. On failure: re-dispatch that one
  subagent a single time via Task, with the exact validation error text appended to its prompt so
  it can correct the specific field, then re-run validation against the new output. If it fails a
  **second** time, stop the entire run immediately and report exactly which agent and which field
  failed — do not proceed to the next stage, and do not paper over it.

## Steps

0. **Preflight.** Run `python pipeline/guardrails.py preflight --company $ARGUMENTS` via Bash.
   If it prints `GUARDRAIL_FAIL`, stop immediately, show the reported errors to the user, and do
   not dispatch any subagent — a bad company slug must never reach a Task dispatch or a shell
   command. If it passes, also delete any pre-existing
   `output/$ARGUMENTS/{financial_findings,data_quality_findings,contract_risk_findings,action_memo}.json`
   and `memos/$ARGUMENTS_value_creation_memo.md` **before** dispatching anyone. Two of the four
   subagents (`data-quality-auditor`, `contract-reviewer`) have no `Read` tool by design (least
   privilege), and the `Write` tool refuses to overwrite a file it hasn't first read — so if last
   run's output is still sitting there, their write fails with a permission error instead of
   regenerating. Deleting first means every subagent is always writing a brand-new file.
1. Dispatch the `financial-analyst`, `data-quality-auditor`, and `contract-reviewer` subagents
   via the Task tool **in parallel** (they're independent — send all three Task calls in one
   message), each analyzing company `$ARGUMENTS`. These run asynchronously — you will get a
   separate completion notification for each one, not all at once.
2. **Wait for all three notifications before doing anything else.** Do not dispatch
   `synthesis-writer`, and do not produce any summary or final response, until you have received
   and confirmed a completion notification for `financial-analyst`, `data-quality-auditor`, AND
   `contract-reviewer` — all three, every time. If a notification for one of them hasn't arrived
   yet, wait longer; do not guess at its result, do not treat a slow agent as skippable, and do
   not finish your turn while any of the three is still outstanding.
3. For each of the three, once its output file exists (verify with Read before proceeding — don't
   just trust that the notification implies the file was written), run the matching guardrail
   validation via Bash:
   - `python pipeline/guardrails.py validate --schema FinancialFindings --file output/$ARGUMENTS/financial_findings.json`
   - `python pipeline/guardrails.py validate --schema DataQualityFindings --file output/$ARGUMENTS/data_quality_findings.json`
   - `python pipeline/guardrails.py validate --schema ContractRiskFindings --file output/$ARGUMENTS/contract_risk_findings.json`

   On `GUARDRAIL_FAIL` for any of them: re-dispatch that single subagent once via Task, appending
   the printed validation errors to its prompt, then re-run the same validate command against the
   new output. If it fails again, stop the whole run and report which agent/field failed — do not
   dispatch `synthesis-writer` while any of the three has not passed validation.
4. Once all three have passed validation, dispatch the `synthesis-writer` subagent to merge them
   into `output/$ARGUMENTS/action_memo.json` and `memos/$ARGUMENTS_value_creation_memo.md`, and
   **wait for its completion notification too** before finishing.
5. Once `synthesis-writer` has completed and you've confirmed `output/$ARGUMENTS/action_memo.json`
   exists, run `python pipeline/guardrails.py validate --schema ActionMemo --file output/$ARGUMENTS/action_memo.json`.
   On `GUARDRAIL_FAIL`, re-dispatch `synthesis-writer` once with the validation errors appended to
   its prompt and re-validate; if it fails again, stop and report the failure rather than
   presenting an unvalidated memo as done.
6. Only after `action_memo.json` has passed validation and
   `memos/$ARGUMENTS_value_creation_memo.md` exists: print a short summary — how many action
   items were generated, the total dollar-impact range across all of them, and the path to the
   final memo.

If your own turn would otherwise end before all four subagents (three specialists +
synthesis-writer) have confirmed completion *and* passed their guardrail validation, that is a
bug — go back and wait rather than reporting success early.
