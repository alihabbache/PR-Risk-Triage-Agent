# 📋 Product Requirements Document (PRD)
## IBM DevOps Loop — PR Risk Triage Agent

---

### **Document Metadata**
- **Product Name**: PR Risk Triage Agent
- **Initiative**: IBM DevOps Loop — Intelligent Shift-Left Code Review
- **Role**: Technical Product Manager (TPM)
- **Status**: Prototype / Proof-of-Concept (POC)
- **Target Release**: Q2 2026
- **Hosting / Operating Cost**: **$0.00 (Zero-Cost GitHub Actions + GitHub Pages)**

---

## 1. Executive Summary & Problem Framing

### 1.1 Problem Statement
In high-velocity engineering organizations, code reviewers suffer from **review fatigue** and **signal-to-noise degradation**. They cannot reliably distinguish between:
1. **Cosmetic / Low-Risk PRs** (e.g., documentation edits, unit test mocks, formatting, localization strings).
2. **High-Risk / High-Blast PRs** (e.g., database lock migrations, JWT verification logic, payment gateway handlers, IAM role alterations).

**Consequences:**
- Mission-critical bugs escape into production because reviewers skim over critical architectural changes.
- Safe, cosmetic PRs sit in review queues for days, slowing developer velocity.

### 1.2 Proposed Solution
The **PR Risk Triage Agent** is an autonomous shift-left agent integrated directly into the CI/CD pull request lifecycle. It computes a transparent, explainable **Composite Risk Score (0–100)** based on:
1. **Blast Radius (40%)**: File count, line delta entropy, and sensitivity of architectural boundaries touched.
2. **Historical Incident Correlation (35%)**: Direct matching with past SEV-1/SEV-2 post-mortem incident files with time-decay weighting.
3. **Author Context & Domain Expertise (25%)**: Author tenure, merge history, prior revert rate, and subsystem familiarity.

The agent automatically posts an explainable GitHub PR comment, assigns clear triage labels (e.g., `risk:critical-blocking-review`, `risk:low-cosmetic`), suggests specialized reviewers, and prescribes mandatory verification checklists.

---

## 2. Product Objectives & Success Metrics

| Key Metric | Target Goal | Baseline (Without Agent) | Measurement Method |
| :--- | :---: | :---: | :--- |
| **False-Negative Rate (FNR)** | **&lt; 2.0%** (Zero SEV-1 Escapes) | ~25.0% | Historical backtesting against ground-truth incident dataset |
| **Reviewer Recall / Sensitivity** | **&gt; 95.0%** | ~75.0% | Ratio of incident PRs caught as High/Critical |
| **Cosmetic PR Fast-Track Rate** | **&gt; 80.0%** | 0.0% | % of safe PRs routed for lightweight approval |
| **Review Turnaround Time (Cosmetic)** | **-40% reduction** | ~48 hours | Mean time to merge (MTTM) on docs/tests |
| **Annual Engineering Hours Saved** | **600+ hours / 30 devs** | 0 | Accumulated review lag reduction |

---

## 3. User Personas & User Journeys

### 3.1 Personas
1. **DevOps / Senior Reviewer (Alex)**: Wants to immediately spot risky schema changes and authentication logic without sifting through 50 PRs manually.
2. **Junior Software Engineer (Carol)**: Wants clear feedback on why her PR touched a sensitive module and who the recommended senior reviewers are.
3. **Security & Reliability Architect (Dave)**: Needs automated policy enforcement ensuring SEV-1 incident hotspots are never merged without 2+ principal approvals.
4. **Engineering Director / TPM (Sarah)**: Wants quantitative visibility into repository risk distribution, reviewer bandwidth, and escaped defect trends.

---

## 4. Scoring Algorithm & Policy Matrix

### 4.1 Formula Specification
$$S = \max(0, \min(100, (0.40 \cdot B) + (0.35 \cdot I) + (0.25 \cdot A)))$$

Where:
- $B$ = Blast Radius Factor ($0 \le B \le 100$)
- $I$ = Past Incident Correlation Factor ($0 \le I \le 100$)
- $A$ = Author & Domain Risk Factor ($0 \le A \le 100$)

#### Safety Guardrail Rule:
If a PR modifies files directly correlated with a prior **SEV-1 Incident**, the composite score is bounded by a **hard floor**:
$$\text{Score}_{\text{final}} = \max(S, 55.0)$$

### 4.2 Triage Matrix & Actions

| Risk Tier | Score Range | Label Assigned | Automated Action & Review Policy |
| :--- | :---: | :--- | :--- |
| **LOW** | $0.0 - 34.9$ | `risk:low-cosmetic` | Fast-track merge eligible once CI passes. 1 standard peer reviewer. |
| **MEDIUM** | $35.0 - 59.9$ | `risk:medium-standard-review` | Standard peer review required. Regular unit and lint checks. |
| **HIGH** | $60.0 - 79.9$ | `risk:high-targeted-review` | Requires Domain Specialist approval. Regression integration suite. |
| **CRITICAL** | $80.0 - 100.0$ | `risk:critical-blocking-review` | Mandatory 2+ Principal approvers. Staging canary deployment with automated rollback guard. |

---

## 5. System Architecture & Zero-Cost Infrastructure

```
                   +------------------------------------+
                   |        GitHub Pull Request         |
                   |   (Opened / Synchronize / Edit)    |
                   +-----------------+------------------+
                                     |
                                     v
                   +------------------------------------+
                   |     GitHub Actions CI Runner       |
                   |      (Free Tier - 0 USD)           |
                   +-----------------+------------------+
                                     |
                                     v
                   +------------------------------------+
                   |   PR Risk Scoring Engine (Python)  |
                   |  - Blast Radius AST Analyzer       |
                   |  - Incident Post-Mortem Matcher    |
                   |  - Author Expertise Evaluator      |
                   +-----------------+------------------+
                                     |
                                     v
         +---------------------------+---------------------------+
         |                                                       |
         v                                                       v
+-------------------------------+               +-------------------------------+
|  Automated GitHub PR Comment  |               |  Interactive Web Dashboard    |
|  - Assigned Label             |               |  - Live Sandbox Simulator     |
|  - Key Explainable Drivers    |               |  - Backtesting FNR Analyzer   |
|  - Checklist & Approvers      |               |  - Hosted on GitHub Pages ($0)|
+-------------------------------+               +-------------------------------+
```

---

## 6. TPM ROI & Business Case

For a standard mid-market enterprise team (30 developers, 60 PRs/week):
- **Cosmetic PRs per year**: $\approx 1,248$ PRs ($40\%$ of volume).
- **Time saved per cosmetic PR**: $30\text{ minutes}$.
- **Annual Reviewer Capacity Saved**: **$624\text{ hours}$** ($\approx \$59,280$ value at $\$95/\text{hr}$).
- **Escaped Incident Mitigation**: Prevents $3.5\text{ major outages/year}$ ($\approx \$140,000$ value).
- **Total Annual Value Delivered**: **$\$199,280$** at **$\$0.00$ incremental SaaS/server cost**.

---

## 7. Product Roadmap

- **Phase 1 (Current POC)**: Standalone Python scoring engine, CLI tool, Backtesting benchmark suite, and interactive GitHub Pages dashboard.
- **Phase 2 (Q3 2026)**: Live GitHub Action marketplace release with automated Slack/Teams notification webhooks.
- **Phase 3 (Q4 2026)**: Integration with IBM watsonx / IBM DevOps Loop observability platform to auto-ingest ServiceNow and Jira post-mortem incidents.
- **Phase 4 (Q1 2027)**: Self-learning Bayesian weight calibration based on repository merge success rates and rollback telemetry.
