---
description: Run the contract-reviewer subagent standalone against one company's data room
argument-hint: <company>
---

Use the `contract-reviewer` subagent (via the Task tool) to review the contracts of company
`$ARGUMENTS`. It should write its findings to `output/$ARGUMENTS/contract_risk_findings.json`.
Once it's done, print a short summary of what it found.
