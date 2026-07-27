---
description: Run the financial-analyst subagent standalone against one company's data room
argument-hint: <company>
---

Use the `financial-analyst` subagent (via the Task tool) to analyze the financials of company
`$ARGUMENTS`. It should write its findings to `output/$ARGUMENTS/financial_findings.json`. Once
it's done, print a short summary of what it found.
