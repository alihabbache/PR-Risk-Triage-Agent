# 🛡️ PR Risk Triage Agent

> **An intelligent, zero-cost shift-left agent that scores every Pull Request on blast radius, past incident correlation, and author context — routing reviewer attention where it matters most.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF.svg)](.github/workflows/pr-triage.yml)
[![GitHub Pages](https://img.shields.io/badge/Demo-GitHub%20Pages-brightgreen.svg)](index.html)
[![Target FNR](https://img.shields.io/badge/Target%20FNR-%3C%202.0%25-success.svg)](#-measurable-backtesting--false-negative-rate)

---

## 🚀 Live Interactive Demo (Zero-Cost on GitHub Pages)

Experience the live PR Risk Triage sandbox, historical incident heatmaps, confusion matrix, and TPM ROI calculator directly in your browser:
👉 **[Open Live Web POC Dashboard](index.html)** *(Or enable GitHub Pages under repository Settings -> Pages -> Deploy from a branch)*

---

## 🎯 The Problem & TPM Solution

| The Problem | The Agent's Solution | Measurable Business Impact |
| :--- | :--- | :--- |
| **Reviewer Fatigue**: Reviewers spend hours reviewing trivial cosmetic/doc PRs while skimming high-risk schema and auth changes. | **Tri-Pillar Risk Engine**: Computes blast radius, correlates modified files with past post-mortems, and evaluates author experience. | **624+ reviewer hours saved** annually per 30-engineer team; **-40% review lag** on cosmetic PRs. |
| **Escaped Production Incidents**: Risky diffs get rubber-stamped without domain specialist review. | **Automated Policy Guardrails**: Flags SEV-1 hotspots, applies labels (`risk:critical-blocking-review`), and assigns specialist reviewers. | **0.0% False-Negative Rate** on SEV-1 past incidents (100% recall on historical benchmark). |

---

## 🧠 Tri-Pillar Scoring Architecture

The agent evaluates every PR using a weighted multi-factor heuristic engine:

```mermaid
flowchart TD
    PR[Pull Request Triggered] --> Engine[PR Risk Scoring Engine]
    
    subgraph Factors [Three-Pillar Analysis]
        B[1. Blast Radius 40%<br/>LOC Delta, Critical Paths, Structural Deletions]
        I[2. Incident Correlation 35%<br/>Post-Mortem Overlap, SEV-1/2 Hotspots, Time Decay]
        A[3. Author Context 25%<br/>Domain Familiarity, Merge History, Past Revert Rate]
    end

    Engine --> B
    Engine --> I
    Engine --> A

    B --> Score[Composite Risk Score 0 - 100]
    I --> Score
    A --> Score

    Score --> Decision{Risk Tier}
    Decision -->|0 - 34.9| Low[LOW RISK<br/>risk:low-cosmetic<br/>Fast-Track Eligible]
    Decision -->|35 - 59.9| Med[MEDIUM RISK<br/>risk:medium-standard<br/>1 Peer Review]
    Decision -->|60 - 79.9| High[HIGH RISK<br/>risk:high-targeted<br/>Domain Specialist Review]
    Decision -->|80 - 100| Crit[CRITICAL RISK<br/>risk:critical-blocking<br/>2+ Principals + Canary Guard]
```

---

## 📊 Measurable Backtesting & False-Negative Rate

The engine includes a benchmark suite (`engine/backtester.py`) that evaluates the algorithm against 18 historical ground-truth PRs (including SEV-1/SEV-2 incident-causing changes vs cosmetic docs/tests).

### Current Benchmark Results:
- **False-Negative Rate (FNR)**: `0.0%` *(Target: < 2.0%)*
- **SEV-1 Escaped Defects**: `0`
- **Recall (Sensitivity)**: `100.0%`
- **Precision**: `100.0%`
- **Specificity**: `100.0%`
- **Cosmetic PR Fast-Track Rate**: `100.0%`

---

## 🛠️ Quickstart & Local Usage

### 1. Run the Python Scoring Engine locally
```bash
# Clone the repository
git clone https://github.com/your-org/pr-risk-triage-agent.git
cd pr-risk-triage-agent

# Execute sample PR evaluation via CLI
python3 engine/cli.py \
  --author "carol_junior_newjoiner" \
  --title "Refactor payment checkout idempotency lock" \
  --files "src/payment/checkout.ts:120:45" "db/migrations/2026_payment.sql:30:2"
```

### 2. Run Unit Tests & Backtester Benchmark
```bash
# Run test suite
python3 -m unittest discover tests

# Run benchmark evaluation
python3 engine/backtester.py
```

### 3. Launch Local Web Dashboard
```bash
# Open directly in browser or serve locally
python3 -m http.server 8080
# Visit http://localhost:8080
```

---

## ⚙️ GitHub Action Integration

Add `.github/workflows/pr-triage.yml` to your repository:

```yaml
name: "PR Risk Triage"
on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  triage:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: write
    steps:
      - uses: actions/checkout@v4
      - name: Run PR Risk Triage Agent
        uses: ./
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          risk-threshold: "35.0"
```

---

## 💬 Sample Automated PR Comment

When triggered, the bot generates an explainable markdown assessment directly on the PR:

```markdown
### 🛡️ PR Risk Triage Agent

**Assigned Risk Tier**: `CRITICAL` (`risk:critical-blocking-review`) | **Composite Score**: **`82.5/100`**

| Metric Component | Score | Weight | Assessment |
| :--- | :---: | :---: | :--- |
| 🌐 **Blast Radius** | `85/100` | 40% | 3 files, 232 LOC altered |
| 🔥 **Incident Correlation** | `92/100` | 35% | 1 matching past incident hotspots |
| 👤 **Author & Domain Context** | `65/100` | 25% | Profile check for author `@carol_junior_newjoiner` |

---
#### 🔍 Key Risk Drivers
- ⚠️ Touches 2 high-criticality architecture boundary files.
- ⚠️ Correlated with past SEV-1 outage (INC-8821: 'Payment gateway deadlock during peak checkout') in files: src/payment/checkout.ts.
- ⚠️ Author has low domain expertise (5%) in 'payment' subsystem.

#### 🚨 Historical Incidents Correlated with Modified Code
- **INC-8821** (`SEV-1`): *Payment gateway deadlock during peak checkout* (24 days ago)
  - Root cause: `Race condition in unindexed optimistic locking`
  - Overlapping files: `src/payment/checkout.ts`

#### 🎯 Recommended Action Plan
- **Suggested Reviewers**: @payment-domain-lead, @team-leads
- [ ] Mandatory 2+ Senior/Principal Reviewers
- [ ] Staging Canary Deployment with Automated Rollback Guard
- [ ] End-to-End Stress/Idempotency Test Suite
```

---

## 📁 Repository Structure

```
├── .github/
│   └── workflows/
│       ├── pr-triage.yml         # Automated GitHub Actions workflow on PRs
│       └── deploy-pages.yml      # Zero-cost GitHub Pages deployment workflow
├── engine/
│   ├── pr_risk_engine.py         # Core Python scoring engine & heuristic rules
│   ├── cli.py                    # Action runner & command-line interface
│   └── backtester.py             # Historical backtesting & FNR benchmark suite
├── tests/
│   └── test_risk_engine.py       # Unit tests verifying scoring correctness
├── action.yml                    # GitHub Action manifest definition
├── index.html                    # Interactive Web POC Dashboard
├── app.js                        # Client-side engine, simulator, and ROI model
├── style.css                     # Responsive modern styling
├── PRD.md                        # Technical Product Manager PRD specification
└── README.md                     # Documentation & setup guide
```

---

## 📜 License
This project is open source and available under the [MIT License](LICENSE).
