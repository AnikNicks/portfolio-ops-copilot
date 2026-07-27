---
description: Run the data-quality-auditor subagent standalone against one company's data room
argument-hint: <company>
---

Use the `data-quality-auditor` subagent (via the Task tool) to audit the CRM export of company
`$ARGUMENTS`. It should write its findings to `output/$ARGUMENTS/data_quality_findings.json`.
Once it's done, print a short summary of what it found.
