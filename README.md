# 📊 Portfolio Ops Copilot: Autonomous Multi-Agent Portfolio Diagnostics Engine

An advanced, production-grade autonomous diagnostics and value-creation orchestration platform
designed to convert a portfolio company's messy financial, CRM, and vendor-contract exports into a
board-ready, dollar-quantified action plan. **Portfolio Ops Copilot** orchestrates a four-agent
framework: three specialist agents running in parallel that independently mine financial ledgers,
CRM/ERP exports, and vendor contracts for risk signals, and a synthesis engine that correlates
their findings into a single prioritized memo.

Built natively using **Claude Code multi-agent orchestration**, the **Model Context Protocol**
(Docker MCP Toolkit), **Pydantic schema contracts**, and **pandas/pypdf** data-normalization
tooling, Portfolio Ops Copilot eliminates spreadsheet fatigue — instantly transforming
unstructured financial, CRM, and contract noise into a fixed
Problem→Solution→Trade-offs→Success-Metrics action plan with a dollar-impact estimate attached to
every recommendation, gated end-to-end by code-enforced validation instead of prompt-only trust.

---

## 📸 Screenshots

### Before / After Diagnostic Workspace
![Before/after overview](docs/screenshots/01-before-after-overview.jpg)

---

## ⚡ Core Features

* **Multi-Agent Diagnostic Pipeline:** Dispatches three specialist agents in parallel against a
  company's data room, each producing a schema-validated JSON findings file, then merges them
  through a synthesis agent that ranks every action item by dollar impact.
* **Code-Enforced Guardrail Gate:** A preflight checkpoint sanitizes the company input and
  confirms required source files exist before any agent is dispatched; a post-output checkpoint
  loads every agent's JSON against its Pydantic contract — including business-rule checks like
  impact-range ordering and closed enums — and retries a failing agent once (with the exact
  validation error appended to its prompt) before hard-stopping the run.
* **Retrieval-Only Contract Forensics:** The contract-review agent has no raw file-read tool at
  all — every clause it cites carries a `chunk_id` and a verbatim quote pulled from a dedicated
  PDF-chunking tool, eliminating paraphrased or hallucinated clause references by construction.
* **Cross-Agent Correlation Synthesis:** The synthesis agent actively looks for findings that
  reinforce each other across specialists (e.g., a contract pricing escalator that explains a
  COGS trend the financial agent flagged independently) and calls out the connection explicitly
  instead of listing three disconnected silos.
* **Least-Privilege Tool Scoping:** Every agent's tool allowlist is declared explicitly and scoped
  to the minimum it needs — the contract-review and data-quality agents have no generic file-read
  tool, enforced structurally in the agent definition, not just requested in a prompt.
* **Fail-Safe Regeneration Matrix:** The orchestrator clears stale output before every run so a
  no-read-tool agent's write never collides with the write-tool's overwrite-protection check —
  every diagnostic run is a clean, reproducible regeneration, never a stale partial merge.

---

## 🛠️ Tech Stack

### Backend, Agentic Core & Orchestration
* **Claude Code** (Subagent & Task-Tool Orchestration)
* **Model Context Protocol / Docker MCP Toolkit** (Scoped, Read-Only Filesystem Access)
* **Pydantic** (Schema Contracts + Business-Rule Validation Engine)
* **pandas** (Financial Normalization Layer)
* **pypdf** (Contract Chunking & Citation Engine)

### Guardrails & Reliability
* **`pipeline/guardrails.py`** (Preflight Input Sanitization + Post-Output Validation CLI)
* **Retry-Once-Then-Hard-Stop Policy** (Self-Correcting Agent Dispatch on Validation Failure)

### Frontend & App State
* **Streamlit** (Before/After Diagnostic Visualization Console)

---

## 📐 Project Architecture

```text
                    +-------------------------------+
                    |     /diagnose <company>       |
                    |   (Orchestrator, .claude/)     |
                    +---------------+-----------------+
                                    |
                                    v
                    +---------------+-----------------+
                    |   ① Preflight Guardrail Check   |
                    |  slug sanitized, inputs present  |
                    +---------------+-----------------+
                                    |
                    +---------------+-----------------+
                    |     Parallel Task Dispatch       |
                    +----+-------------+-------------+-+
                         |             |             |
                         v             v             v
                  [financial-    [data-quality-  [contract-
                    analyst]        auditor]      reviewer]
                         |             |             |
                         v             v             v
                  financial_    data_quality_   contract_risk_
                  findings.json  findings.json   findings.json
                         |             |             |
                         +-------------+-------------+
                                    |
                                    v
                    +---------------+-----------------+
                    |  ② Post-Output Guardrail Check  |
                    |  schema + business-rule validate |
                    |  retry once, else hard-stop      |
                    +---------------+-----------------+
                                    |
                                    v
                    +---------------+-----------------+
                    |        synthesis-writer          |
                    |   (cross-agent correlation)       |
                    +---------------+-----------------+
                                    |
                    (② guardrail re-applied to the final memo JSON)
                                    v
                    +---------------+-----------------+
                    |  action_memo.json  +  <company>  |
                    |   _value_creation_memo.md        |
                    +-----------------------------------+
```

---

## 🖼️ Interface Matrix

| Cross-Agent Correlation | Fixed Memo Format |
|:---:|:---:|
| ![Cross-agent correlation](docs/screenshots/02-memo-cross-agent-correlation.jpg) | ![Trade-offs and success metrics](docs/screenshots/03-memo-tradeoffs-success-metrics.jpg) |
| *Synthesis agent tying an independently-flagged financial trend to a contract clause.* | *Every action item enforces Problem → Solution → Trade-offs → Success Metrics.* |

---

## 💻 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/AnikNicks/portfolio-ops-copilot.git
cd portfolio-ops-copilot
```

### 2. Create and Activate a Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Model Context Protocol Gateway

`.mcp.json` is checked in, but it points at a Docker MCP **profile**
(`portfolio-ops-copilot`) that lives on your machine, not in the repo, so a fresh clone needs to
recreate it once:

```bash
docker mcp profile create --name "Portfolio Ops Copilot" --id portfolio-ops-copilot \
  --server catalog://mcp/docker-mcp-catalog/filesystem
docker mcp profile config portfolio-ops-copilot --set 'filesystem.paths=["<absolute-path-to-repo>/data/synthetic"]'
docker mcp client connect claude-code --profile portfolio-ops-copilot
```

On Windows, configure `filesystem.paths` as a POSIX-style path **without** a drive letter (e.g.
`/Users/<you>/.../data/synthetic`) — a Windows-style path collides with Docker's `-v src:dst` bind
syntax on the drive-letter colon. Then fill in the two `<ABSOLUTE_PATH_...>` placeholders in
`.mcp.json`'s `env` block with your own machine's paths.

---

## 🚀 Running the Application

### 5. Run a Full Diagnostic

```bash
claude
/diagnose acme-distribution
```

### 6. Launch the Visualization Console

```bash
streamlit run app/streamlit_app.py
```

1. Select a portfolio company from the sidebar (or upload a new company's financials, CRM export,
   and contract PDFs).
2. Review the raw data room in the **Before** panel.
3. Click **Run Diagnostic** to stream the live multi-agent run, then review the generated
   value-creation memo in the **After** panel.

---

## 🛡️ Guardrails & Reliability Engineering

Schema conformance is enforced by code, not by asking an LLM nicely. `pipeline/schemas.py` defines
a Pydantic contract for every inter-agent handoff, and `pipeline/guardrails.py` is the CLI the
orchestrator actually runs and branches on:

* **Preflight** — rejects a company slug that doesn't match `^[a-z0-9][a-z0-9-]*$` (the value gets
  interpolated into file paths and shell commands, so this blocks path-traversal/injection before
  it reaches a dispatch), and confirms the required source files exist.
* **Post-output validation** — loads the target JSON and validates it against its Pydantic model
  for real, including business-rule checks (`dollar_impact_high >= dollar_impact_low`, closed
  `Literal` enums instead of free strings, non-empty required fields). On failure, the orchestrator
  re-dispatches the single failing agent once with the validation error appended to its prompt; a
  second failure hard-stops the run and reports exactly which agent and field broke.

This is a real, load-bearing gate rather than a formality — during an end-to-end run, it caught a
specialist agent (deliberately scoped with no read access to the schema file) producing a
differently-shaped JSON document, and forced a corrected retry before synthesis was allowed to run.

---

## 🧪 Diagnostic Scenario Matrix

### 1. AR Collections Compounded by CRM Contact Gaps (Critical Priority)

* **Finding Reference:** `AR-COLLECT-01`
* **Signal Surface:** Accounts-receivable aging (financial agent) cross-referenced with missing
  CRM contact channels and stale last-activity dates on the same accounts (data-quality agent).
* **Correlation Target:** Verifies the synthesis agent's ability to tie a financial trend to a data
  hygiene root cause instead of reporting them as two unrelated line items. Estimated impact:
  $595,000–$749,000/year.

### 2. Margin Compression Explained by a Contract Escalator (High Priority)

* **Finding Reference:** `MARGIN-ESC-01`
* **Signal Surface:** Gross-margin compression (financial agent) correlated with a compounding
  annual pricing escalator and an 85% volume-lock-in clause on a raw-materials contract
  (contract-review agent).
* **Correlation Target:** Confirms retrieval-only contract citation (`chunk_id` + verbatim quote)
  is precise enough to ground a dollar estimate instead of a directional guess. Estimated impact:
  $180,000–$450,000/year.

### 3. CRM Duplicate & Schema-Drift Cleanup (Standard Priority)

* **Finding Reference:** `CRM-HYGIENE-01`
* **Signal Surface:** Duplicate accounts under separate IDs, a blank-name record fragment, and
  inconsistent region-naming conventions across a CRM export.
* **Correlation Target:** Confirms every finding carries a traceable Account ID in its evidence
  list rather than an unverifiable summary claim.

---

## 🔮 Future Enhancements

* **Additional Specialist Agents:** A dedicated churn/retention-risk agent and a vendor-pricing
  benchmarking agent, dispatched into the same parallel Task-tool fan-out.
* **Live Data-Room Connectors:** Secured MCP connectors into real ERP/CRM systems, replacing the
  synthetic data room while keeping the same normalize-before-reasoning tool boundary.
* **Automated Remediation Ticketing:** Auto-filing a ticket per ranked action item into an issue
  tracker, with the dollar-impact estimate and evidence carried into the ticket body.
* **Guardrail Telemetry:** Structured logging of every guardrail pass/fail/retry across runs, to
  quantify how often each agent needs a corrective retry over time.

---

## 🔗 Repository & Meta

* **GitHub Repository:** [https://github.com/AnikNicks/portfolio-ops-copilot](https://github.com/AnikNicks/portfolio-ops-copilot)
* **Author Profile:** [Anik Das (AnikNicks)](https://github.com/AnikNicks)
* **License:** This project is open-source and intended for technical portfolio, research, and
  educational purposes.

---

## 🤝 Acknowledgements

* Anthropic Claude Code Multi-Agent Framework
* Docker MCP Toolkit / Model Context Protocol
* Pydantic Validation Ecosystem
* Streamlit Visualization Framework
