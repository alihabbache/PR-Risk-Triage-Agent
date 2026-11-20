/**
 * IBM DevOps Loop - PR Risk Triage Agent
 * Client-side Engine, Simulator, Backtest Suite & ROI Calculator
 */

// Historical incidents database
const HISTORICAL_INCIDENTS = [
  {
    id: "INC-8821",
    title: "Payment gateway deadlock during peak checkout",
    severity: "SEV-1",
    files_involved: [
      "src/payment/checkout.ts",
      "src/payment/stripe_gateway.ts",
      "db/migrations/20250412_payment_locks.sql"
    ],
    root_cause: "Race condition in unindexed optimistic locking",
    recency_days: 24
  },
  {
    id: "INC-7430",
    title: "Auth token bypass on token refresh endpoint",
    severity: "SEV-1",
    files_involved: [
      "src/auth/token_service.py",
      "src/auth/jwt_verifier.py",
      "src/api/v2/auth_controller.py"
    ],
    root_cause: "Missing signature verification on kid mismatch",
    recency_days: 65
  },
  {
    id: "INC-6921",
    title: "Database connection pool exhaustion on analytics sync",
    severity: "SEV-2",
    files_involved: [
      "src/db/connection_pool.ts",
      "src/analytics/event_processor.ts"
    ],
    root_cause: "Unreleased connection in catch block",
    recency_days: 110
  },
  {
    id: "INC-5104",
    title: "Terraform IAM policy over-permission vulnerability",
    severity: "SEV-2",
    files_involved: [
      "infra/terraform/iam_roles.tf",
      "infra/terraform/k8s_cluster.tf"
    ],
    root_cause: "Wildcard S3 access grant in deploy role",
    recency_days: 150
  },
  {
    id: "INC-4819",
    title: "Memory leak in real-time notification socket worker",
    severity: "SEV-3",
    files_involved: [
      "src/realtime/socket_hub.go",
      "src/realtime/client_listener.go"
    ],
    root_cause: "Unbounded map growth on client disconnect",
    recency_days: 210
  }
];

// Author Profiles
const AUTHOR_PROFILES = {
  "alice_sr_architect": {
    tenure_months: 36,
    merged_prs: 420,
    reverts: 1,
    familiarity: { payment: 0.95, auth: 0.92, db: 0.88, infra: 0.85, core: 0.90 }
  },
  "bob_backend_mid": {
    tenure_months: 14,
    merged_prs: 85,
    reverts: 3,
    familiarity: { api: 0.80, db: 0.65, payment: 0.35, auth: 0.20 }
  },
  "carol_junior_newjoiner": {
    tenure_months: 2,
    merged_prs: 8,
    reverts: 1,
    familiarity: { docs: 0.90, frontend: 0.60, api: 0.25, auth: 0.05, payment: 0.05 }
  },
  "external_contributor": {
    tenure_months: 0,
    merged_prs: 0,
    reverts: 0,
    familiarity: {}
  }
};

// Critical Path Rules
const CRITICAL_PATHS = [
  { regex: /(^|\/)(auth|security|crypto|jwt|session|oauth|iam)\//i, weight: 28, desc: "Authentication & Security Module" },
  { regex: /(^|\/)(payment|billing|stripe|ledger|wallet|checkout)\//i, weight: 30, desc: "Payment & Financial Transactions" },
  { regex: /(^|\/)(db|database|migrations?|schema|sql|models?)\//i, weight: 25, desc: "Database Schema & Migrations" },
  { regex: /(^|\/)(infra|terraform|k8s|kubernetes|helm|docker|deploy|ci|cd|\.github)\//i, weight: 22, desc: "Infrastructure & CI/CD Pipeline" },
  { regex: /(^|\/)(core|kernel|engine|protocol|networking|consensus)\//i, weight: 24, desc: "Core Engine & Low-Level Subsystems" },
  { regex: /(^|\/)(api|routes|endpoints|controllers?)\//i, weight: 16, desc: "Public APIs & Routing" },
  { regex: /(^|\/)(config|settings|env|\.env)\//i, weight: 18, desc: "Global Configuration & Environment" },
  { regex: /\.(sql|proto|graphql|tf|tfvars|lock|ya?ml)$/i, weight: 14, desc: "Config / Schema / Lockfile Definition" },
  { regex: /(^|\/)(docs|documentation|examples?|\.md|\.txt)$/i, weight: -15, desc: "Documentation (Low Risk)" },
  { regex: /(^|\/)(tests?|spec|mocks?|fixtures?)\//i, weight: -10, desc: "Test / Mock Files (Low Direct Risk)" }
];

// Presets for demo
const PRESETS = [
  {
    name: "🔥 Critical Incident Hotspot (Junior)",
    title: "Refactor checkout idempotency and stripe webhook lock",
    author: "carol_junior_newjoiner",
    files: [
      { filename: "src/payment/checkout.ts", additions: 120, deletions: 45 },
      { filename: "src/payment/stripe_gateway.ts", additions: 85, deletions: 30 },
      { filename: "db/migrations/20250412_payment_locks.sql", additions: 25, deletions: 2 }
    ]
  },
  {
    name: "🛡️ Auth JWT Verification (Mid-level)",
    title: "Add cross-region JWT kid validation",
    author: "bob_backend_mid",
    files: [
      { filename: "src/auth/jwt_verifier.py", additions: 90, deletions: 15 },
      { filename: "src/auth/token_service.py", additions: 40, deletions: 5 }
    ]
  },
  {
    name: "📄 Cosmetic Doc & Typo Fix",
    title: "Fix typo in onboarding docs and quickstart guide",
    author: "carol_junior_newjoiner",
    files: [
      { filename: "docs/quickstart.md", additions: 8, deletions: 8 },
      { filename: "README.md", additions: 2, deletions: 2 }
    ]
  },
  {
    name: "🧪 Unit Tests & Mocks Fix",
    title: "Add unit tests for payment mock service",
    author: "alice_sr_architect",
    files: [
      { filename: "tests/mocks/stripe_mock.ts", additions: 110, deletions: 0 },
      { filename: "tests/unit/payment_mock_test.ts", additions: 80, deletions: 5 }
    ]
  },
  {
    name: "☁️ Terraform IAM Permissions Overhaul",
    title: "Update S3 sync deployment IAM roles",
    author: "carol_junior_newjoiner",
    files: [
      { filename: "infra/terraform/iam_roles.tf", additions: 55, deletions: 12 },
      { filename: "infra/terraform/k8s_cluster.tf", additions: 30, deletions: 2 }
    ]
  }
];

// Benchmark dataset
const BENCHMARK_DATA = [
  { pr_number: 1001, title: "Migrate payment ledger table index", author: "carol_junior_newjoiner", incident: true, sev: "SEV-1", files: [{ filename: "src/payment/checkout.ts", additions: 140, deletions: 20 }, { filename: "db/migrations/20250412_payment_locks.sql", additions: 40, deletions: 5 }] },
  { pr_number: 1002, title: "Upgrade auth token verification for cross-region JWTs", author: "bob_backend_mid", incident: true, sev: "SEV-1", files: [{ filename: "src/auth/jwt_verifier.py", additions: 88, deletions: 12 }, { filename: "src/auth/token_service.py", additions: 45, deletions: 10 }] },
  { pr_number: 1003, title: "Implement background analytics connection manager", author: "bob_backend_mid", incident: true, sev: "SEV-2", files: [{ filename: "src/db/connection_pool.ts", additions: 110, deletions: 60 }, { filename: "src/analytics/event_processor.ts", additions: 95, deletions: 20 }] },
  { pr_number: 1004, title: "Add wildcard S3 sync policy for k8s automation", author: "carol_junior_newjoiner", incident: true, sev: "SEV-2", files: [{ filename: "infra/terraform/iam_roles.tf", additions: 50, deletions: 5 }, { filename: "infra/terraform/k8s_cluster.tf", additions: 30, deletions: 2 }] },
  { pr_number: 1005, title: "Global routing controller rewrite for v2 gateway", author: "external_contributor", incident: true, sev: "SEV-1", files: [{ filename: "src/api/v2/auth_controller.py", additions: 320, deletions: 180 }, { filename: "src/core/router.py", additions: 210, deletions: 90 }] },
  { pr_number: 1006, title: "Database connection heartbeat refactoring", author: "alice_sr_architect", incident: true, sev: "SEV-2", files: [{ filename: "src/db/connection_pool.ts", additions: 190, deletions: 140 }] },
  { pr_number: 1007, title: "Realtime notification socket thread management", author: "bob_backend_mid", incident: true, sev: "SEV-3", files: [{ filename: "src/realtime/socket_hub.go", additions: 80, deletions: 25 }, { filename: "src/realtime/client_listener.go", additions: 45, deletions: 15 }] },
  { pr_number: 1008, title: "Consensus state machine optimization", author: "carol_junior_newjoiner", incident: true, sev: "SEV-1", files: [{ filename: "src/core/kernel/consensus.go", additions: 410, deletions: 290 }, { filename: "src/core/protocol.go", additions: 150, deletions: 70 }] },
  { pr_number: 2001, title: "Fix typo in onboarding documentation and docstrings", author: "carol_junior_newjoiner", incident: false, files: [{ filename: "docs/quickstart.md", additions: 8, deletions: 8 }, { filename: "README.md", additions: 2, deletions: 2 }] },
  { pr_number: 2002, title: "Add unit tests for string utility functions", author: "bob_backend_mid", incident: false, files: [{ filename: "tests/unit/utils_test.py", additions: 65, deletions: 0 }] },
  { pr_number: 2003, title: "Update copyright headers to 2026", author: "alice_sr_architect", incident: false, files: [{ filename: "LICENSE", additions: 1, deletions: 1 }] },
  { pr_number: 2004, title: "Bump linter config and prettier formatting rules", author: "bob_backend_mid", incident: false, files: [{ filename: ".eslintrc.json", additions: 6, deletions: 4 }] },
  { pr_number: 2005, title: "Improve API endpoint documentation with OpenAPI comments", author: "carol_junior_newjoiner", incident: false, files: [{ filename: "docs/api/v2.md", additions: 75, deletions: 10 }] },
  { pr_number: 2006, title: "Add mocks for payment integration tests", author: "alice_sr_architect", incident: false, files: [{ filename: "tests/mocks/stripe_mock.ts", additions: 120, deletions: 0 }] },
  { pr_number: 3001, title: "Add user preference dropdown in settings UI", author: "bob_backend_mid", incident: false, files: [{ filename: "src/frontend/components/UserPreferences.tsx", additions: 65, deletions: 12 }] },
  { pr_number: 3002, title: "Add export CSV endpoint for user audit logs", author: "alice_sr_architect", incident: false, files: [{ filename: "src/api/export_controller.py", additions: 45, deletions: 5 }] },
  { pr_number: 3003, title: "Update landing page marketing banner", author: "carol_junior_newjoiner", incident: false, files: [{ filename: "src/frontend/banner.tsx", additions: 18, deletions: 12 }] },
  { pr_number: 3004, title: "Add caching layer for user profile avatar URLs", author: "alice_sr_architect", incident: false, files: [{ filename: "src/services/avatar_cache.py", additions: 40, deletions: 8 }] }
];

// Evaluation Engine
function evaluatePR(pr) {
  const files = pr.files || [];
  const author = pr.author || "carol_junior_newjoiner";
  const drivers = [];
  const criticalPathsDetected = [];
  const correlatedIncidents = [];
  const recommendedReviewers = [];
  const recommendedChecks = [];

  const totalFiles = files.length;
  let totalAdditions = 0;
  let totalDeletions = 0;
  files.forEach(f => {
    totalAdditions += parseInt(f.additions || 0, 10);
    totalDeletions += parseInt(f.deletions || 0, 10);
  });
  const totalLoc = totalAdditions + totalDeletions;

  // 1. Blast Radius Score
  let blastScore = 5.0;
  if (totalFiles > 30) {
    blastScore += 35.0;
    drivers.push(`Very large blast radius: ${totalFiles} files touched across repo.`);
  } else if (totalFiles > 15) {
    blastScore += 25.0;
    drivers.push(`Broad blast radius: ${totalFiles} files modified.`);
  } else if (totalFiles > 5) {
    blastScore += 15.0;
  }

  if (totalLoc > 1200) {
    blastScore += 30.0;
    drivers.push(`Massive code delta: +${totalAdditions}/-${totalDeletions} (${totalLoc} LOC).`);
  } else if (totalLoc > 400) {
    blastScore += 20.0;
    drivers.push(`Substantial code delta: ${totalLoc} lines altered.`);
  } else if (totalLoc > 100) {
    blastScore += 10.0;
  } else if (totalLoc < 25 && totalFiles <= 2) {
    blastScore -= 10.0;
    drivers.push(`Compact cosmetic diff (${totalLoc} LOC).`);
  }

  let pathPenalty = 0.0;
  let isOnlyDocsOrTests = true;

  files.forEach(f => {
    let matched = false;
    CRITICAL_PATHS.forEach(cp => {
      if (cp.regex.test(f.filename)) {
        if (cp.weight > 0) {
          pathPenalty += cp.weight;
          criticalPathsDetected.push(`${f.filename} (${cp.desc})`);
          matched = true;
          isOnlyDocsOrTests = false;
        } else if (cp.weight < 0) {
          pathPenalty += cp.weight;
        }
      }
    });
    if (!matched && !/(\.md|docs|tests?)/i.test(f.filename)) {
      isOnlyDocsOrTests = false;
    }
  });

  if (isOnlyDocsOrTests) {
    blastScore = Math.max(5.0, blastScore * 0.2);
    drivers.push("Diff is isolated purely to documentation, tests, or non-production files.");
  } else if (criticalPathsDetected.length > 0) {
    drivers.push(`Touches ${criticalPathsDetected.length} high-criticality architecture boundary files.`);
  }

  blastScore += Math.min(45.0, Math.max(-10.0, pathPenalty));
  if (totalDeletions > 250 && totalDeletions > totalAdditions * 2) {
    blastScore += 12.0;
    drivers.push("High deletion ratio indicates breaking change / structural deprecation.");
  }
  blastScore = Math.max(0.0, Math.min(100.0, blastScore));

  // 2. Incident Correlation Score
  let incidentScore = 10.0;
  const touchedFiles = new Set(files.map(f => f.filename));

  HISTORICAL_INCIDENTS.forEach(inc => {
    const incFiles = new Set(inc.files_involved);
    const overlap = [...touchedFiles].filter(x => incFiles.has(x));

    if (overlap.length > 0) {
      const recency = inc.recency_days || 90;
      const decay = Math.exp(-0.005 * recency);
      let baseWeight = 45.0;
      let floor = 30.0;

      if (inc.severity === "SEV-1") {
        baseWeight = 90.0;
        floor = 70.0;
      } else if (inc.severity === "SEV-2") {
        baseWeight = 70.0;
        floor = 50.0;
      }

      const impact = Math.max(floor, baseWeight * decay);
      incidentScore += impact;

      correlatedIncidents.push({
        id: inc.id,
        title: inc.title,
        severity: inc.severity,
        matching_files: overlap,
        recency_days: recency,
        root_cause: inc.root_cause
      });
      drivers.push(`Correlated with past ${inc.severity} outage (${inc.id}: '${inc.title}') in files: ${overlap.join(", ")}.`);
    }
  });

  if (correlatedIncidents.length === 0) {
    incidentScore = Math.max(5.0, incidentScore - 5.0);
  }
  incidentScore = Math.max(0.0, Math.min(100.0, incidentScore));

  // 3. Author Risk Score
  let authorScore = 30.0;
  const authorData = AUTHOR_PROFILES[author];

  if (!authorData) {
    authorScore = 65.0;
    drivers.push(`Author '${author}' has no recorded merge history (First-time / External author).`);
    recommendedReviewers.push("@core-maintainers");
    if (criticalPathsDetected.length > 0) {
      authorScore += 20.0;
      drivers.push("New contributor modifying tier-1 critical paths without prior merge track record.");
    }
  } else {
    if (authorData.merged_prs > 150 && authorData.tenure_months > 24) {
      authorScore = 10.0;
      drivers.push(`Author '${author}' is a veteran maintainer (${authorData.merged_prs} PRs, ${authorData.tenure_months}m tenure).`);
    } else if (authorData.merged_prs > 40) {
      authorScore = 25.0;
    } else {
      authorScore = 55.0;
      drivers.push(`Author '${author}' is relatively junior/new (${authorData.merged_prs} PRs merged).`);
    }

    if (authorData.reverts > 2) {
      authorScore += Math.min(25.0, authorData.reverts * 6.0);
      drivers.push(`Author has ${authorData.reverts} past incident rollbacks/reverts on record.`);
    }

    files.forEach(f => {
      Object.entries(authorData.familiarity || {}).forEach(([domain, fam]) => {
        if (f.filename.toLowerCase().includes(domain)) {
          if (fam < 0.3) {
            authorScore += 20.0;
            drivers.push(`Author has low domain expertise (${Math.round(fam * 100)}%) in '${domain}' subsystem.`);
            recommendedReviewers.push(`@${domain}-domain-lead`);
          } else if (fam > 0.8) {
            authorScore = Math.max(5.0, authorScore - 8.0);
            recommendedReviewers.push(`@${domain}-peer`);
          }
        }
      });
    });
  }
  authorScore = Math.max(0.0, Math.min(100.0, authorScore));

  // Composite Weighted Score
  let totalScore = (blastScore * 0.40) + (incidentScore * 0.35) + (authorScore * 0.25);

  // Safety Guardrails: Prevent False Negatives on known SEV-1/SEV-2 incident files
  if (correlatedIncidents.length > 0) {
    const hasSev1 = correlatedIncidents.some(i => i.severity === "SEV-1");
    const hasSev2 = correlatedIncidents.some(i => i.severity === "SEV-2");
    if (hasSev1) totalScore = Math.max(totalScore, 55.0);
    else if (hasSev2) totalScore = Math.max(totalScore, 45.0);
    else totalScore = Math.max(totalScore, 36.0);
  }

  totalScore = Math.max(0.0, Math.min(100.0, Math.round(totalScore * 10) / 10));

  let riskLevel = "LOW";
  let riskLabel = "risk:low-cosmetic";

  if (totalScore >= 80.0) {
    riskLevel = "CRITICAL";
    riskLabel = "risk:critical-blocking-review";
    recommendedChecks.push("Mandatory 2+ Senior/Principal Reviewers");
    recommendedChecks.push("Staging Canary Deployment with Automated Rollback Guard");
    recommendedChecks.push("End-to-End Stress/Idempotency Test Suite");
  } else if (totalScore >= 60.0) {
    riskLevel = "HIGH";
    riskLabel = "risk:high-targeted-review";
    recommendedChecks.push("Domain Specialist Approval Required");
    recommendedChecks.push("Integration Test Regression Suite Execution");
  } else if (totalScore >= 35.0) {
    riskLevel = "MEDIUM";
    riskLabel = "risk:medium-standard-review";
    recommendedChecks.push("Standard Peer Review (1 Approver)");
    recommendedChecks.push("Standard Unit/Lint CI Checks");
  } else {
    riskLevel = "LOW";
    riskLabel = "risk:low-cosmetic";
    recommendedChecks.push("Fast-Track / Auto-Merge Eligible upon passing CI");
  }

  if (recommendedReviewers.length === 0) {
    recommendedReviewers.push(riskLevel === "CRITICAL" || riskLevel === "HIGH" ? "@team-leads" : "@peer-reviewer");
  }

  // Generate markdown comment
  const comment = [
    `### 🛡️ IBM DevOps Loop — PR Risk Triage Agent`,
    ``,
    `**Assigned Risk Tier**: \`${riskLevel}\` (\`${riskLabel}\`) | **Composite Score**: **\`${totalScore}/100\`**`,
    ``,
    `| Metric Component | Score | Weight | Assessment |`,
    `| :--- | :---: | :---: | :--- |`,
    `| 🌐 **Blast Radius** | \`${Math.round(blastScore)}/100\` | 40% | ${totalFiles} files, ${totalLoc} LOC altered |`,
    `| 🔥 **Incident Correlation** | \`${Math.round(incidentScore)}/100\` | 35% | ${correlatedIncidents.length} matching past incident hotspots |`,
    `| 👤 **Author & Domain Context** | \`${Math.round(authorScore)}/100\` | 25% | Profile check for author \`@${author}\` |`,
    ``,
    `---`,
    `#### 🔍 Key Risk Drivers`
  ];

  drivers.slice(0, 5).forEach(d => comment.push(`- ⚠️ ${d}`));

  if (correlatedIncidents.length > 0) {
    comment.push(``, `#### 🚨 Historical Incidents Correlated with Modified Code`);
    correlatedIncidents.forEach(inc => {
      comment.push(`- **${inc.id}** (\`${inc.severity}\`): *${inc.title}* (${inc.recency_days} days ago)`);
      comment.push(`  - Root cause: \`${inc.root_cause}\``);
      comment.push(`  - Overlapping files: \`${inc.matching_files.join(", ")}\``);
    });
  }

  comment.push(``, `#### 🎯 Recommended Action Plan`);
  comment.push(`- **Suggested Reviewers**: ${[...new Set(recommendedReviewers)].join(", ")}`);
  recommendedChecks.forEach(c => comment.push(`- [ ] ${c}`));
  comment.push(``, `*> 💡 Automated by IBM DevOps Loop PR Risk Triage Agent (POC). Target: <2.0% False Negative Rate.*`);

  return {
    blastScore: Math.round(blastScore * 10) / 10,
    incidentScore: Math.round(incidentScore * 10) / 10,
    authorScore: Math.round(authorScore * 10) / 10,
    totalScore,
    riskLevel,
    riskLabel,
    drivers: [...new Set(drivers)],
    criticalPaths: [...new Set(criticalPathsDetected)],
    correlatedIncidents,
    recommendedReviewers: [...new Set(recommendedReviewers)],
    recommendedChecks,
    markdownComment: comment.join("\n")
  };
}

// UI Rendering & Interaction
let currentFiles = [
  { filename: "src/payment/checkout.ts", additions: 120, deletions: 45 },
  { filename: "src/payment/stripe_gateway.ts", additions: 85, deletions: 30 },
  { filename: "db/migrations/20250412_payment_locks.sql", additions: 25, deletions: 2 }
];

function initApp() {
  setupTabs();
  setupPresets();
  renderFileList();
  setupEventListeners();
  runLiveEvaluation();
  runBacktestBenchmark(35.0);
  calculateROI();
}

function setupTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");
    });
  });
}

function setupPresets() {
  const container = document.getElementById("presetChips");
  if (!container) return;
  container.innerHTML = "";

  PRESETS.forEach(p => {
    const chip = document.createElement("button");
    chip.className = "preset-chip";
    chip.innerText = p.name;
    chip.addEventListener("click", () => {
      document.getElementById("prTitleInput").value = p.title;
      document.getElementById("prAuthorSelect").value = p.author;
      currentFiles = JSON.parse(JSON.stringify(p.files));
      renderFileList();
      runLiveEvaluation();
    });
    container.appendChild(chip);
  });
}

function renderFileList() {
  const tbody = document.getElementById("fileTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  currentFiles.forEach((file, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <input type="text" class="file-input" value="${file.filename}" onchange="updateFile(${index}, 'filename', this.value)" />
      </td>
      <td>
        <input type="number" class="file-input num-input" value="${file.additions}" onchange="updateFile(${index}, 'additions', this.value)" />
      </td>
      <td>
        <input type="number" class="file-input num-input" value="${file.deletions}" onchange="updateFile(${index}, 'deletions', this.value)" />
      </td>
      <td style="text-align: center;">
        <button class="btn-icon-del" onclick="removeFile(${index})" title="Remove file">✕</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

window.updateFile = function(index, field, val) {
  if (field === "filename") currentFiles[index].filename = val;
  else if (field === "additions") currentFiles[index].additions = parseInt(val, 10) || 0;
  else if (field === "deletions") currentFiles[index].deletions = parseInt(val, 10) || 0;
  runLiveEvaluation();
};

window.removeFile = function(index) {
  currentFiles.splice(index, 1);
  renderFileList();
  runLiveEvaluation();
};

window.addNewFileRow = function() {
  currentFiles.push({ filename: "src/new_module.ts", additions: 25, deletions: 5 });
  renderFileList();
  runLiveEvaluation();
};

function setupEventListeners() {
  document.getElementById("prTitleInput")?.addEventListener("input", runLiveEvaluation);
  document.getElementById("prAuthorSelect")?.addEventListener("change", runLiveEvaluation);

  // Backtest Threshold Slider
  const slider = document.getElementById("riskThresholdSlider");
  const sliderVal = document.getElementById("sliderThresholdVal");
  slider?.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    if (sliderVal) sliderVal.innerText = val.toFixed(1);
    runBacktestBenchmark(val);
  });

  // ROI Calculator Inputs
  ["teamSizeInput", "prsPerWeekInput", "avgReviewTimeInput"].forEach(id => {
    document.getElementById(id)?.addEventListener("input", calculateROI);
  });
}

function runLiveEvaluation() {
  const title = document.getElementById("prTitleInput")?.value || "PR Title";
  const author = document.getElementById("prAuthorSelect")?.value || "carol_junior_newjoiner";

  const result = evaluatePR({
    title,
    author,
    files: currentFiles
  });

  // Update Score Card
  const scoreNum = document.getElementById("scoreValue");
  if (scoreNum) scoreNum.innerText = result.totalScore;

  const tierBadge = document.getElementById("riskTierBadge");
  if (tierBadge) {
    tierBadge.className = `score-tier-badge tier-${result.riskLevel}`;
    tierBadge.innerText = `${result.riskLevel} RISK`;
  }

  const labelBadge = document.getElementById("riskLabelBadge");
  if (labelBadge) labelBadge.innerText = result.riskLabel;

  // Breakdown Bars
  const setBar = (fillId, textId, score) => {
    const fill = document.getElementById(fillId);
    const text = document.getElementById(textId);
    if (fill) {
      fill.style.width = `${Math.min(100, score)}%`;
      if (score >= 70) fill.style.backgroundColor = "var(--risk-crit)";
      else if (score >= 40) fill.style.backgroundColor = "var(--risk-high)";
      else fill.style.backgroundColor = "var(--risk-low)";
    }
    if (text) text.innerText = `${score} / 100`;
  };

  setBar("blastBarFill", "blastBarVal", result.blastScore);
  setBar("incBarFill", "incBarVal", result.incidentScore);
  setBar("authBarFill", "authBarVal", result.authorScore);

  // Drivers List
  const driverContainer = document.getElementById("keyDriversList");
  if (driverContainer) {
    driverContainer.innerHTML = "";
    result.drivers.forEach(d => {
      const li = document.createElement("li");
      li.className = "driver-item";
      li.innerHTML = `<span>⚠️</span> <span>${d}</span>`;
      driverContainer.appendChild(li);
    });
  }

  // Correlated Incidents
  const incSection = document.getElementById("correlatedIncidentsBox");
  if (incSection) {
    if (result.correlatedIncidents.length === 0) {
      incSection.innerHTML = `<p style="font-size:0.85rem; color:var(--cds-text-03);">No historical incidents directly correlate with touched files.</p>`;
    } else {
      incSection.innerHTML = "";
      result.correlatedIncidents.forEach(inc => {
        const div = document.createElement("div");
        div.className = "incident-card-mini";
        div.innerHTML = `
          <div class="incident-title">
            <span>🔥 ${inc.id} (${inc.severity})</span>
            <span style="font-size:0.75rem; color:var(--cds-text-03);">${inc.recency_days}d ago</span>
          </div>
          <div style="margin: 0.3rem 0; font-weight:500;">${inc.title}</div>
          <div style="font-size:0.8rem; color:var(--cds-text-02);">Root Cause: <code>${inc.root_cause}</code></div>
          <div style="font-size:0.75rem; color:var(--cds-text-03); margin-top:0.2rem;">Matched files: ${inc.matching_files.join(", ")}</div>
        `;
        incSection.appendChild(div);
      });
    }
  }

  // Markdown Bot Comment Preview
  const commentPreview = document.getElementById("markdownBotComment");
  if (commentPreview) {
    commentPreview.innerText = result.markdownComment;
  }
}

function runBacktestBenchmark(threshold) {
  let tp = 0, tn = 0, fp = 0, fn = 0, sev1Misses = 0;
  const evaluations = [];

  BENCHMARK_DATA.forEach(item => {
    const evalRes = evaluatePR(item);
    const isRisky = evalRes.totalScore >= threshold;

    let status = "";
    if (item.incident) {
      if (isRisky) {
        tp++;
        status = "TP (Caught Incident)";
      } else {
        fn++;
        status = "FN (MISSED INCIDENT!)";
        if (item.sev === "SEV-1") sev1Misses++;
      }
    } else {
      if (isRisky) {
        fp++;
        status = "FP (Flagged Safe PR)";
      } else {
        tn++;
        status = "TN (Fast-Tracked Cosmetic)";
      }
    }

    evaluations.push({
      ...item,
      riskScore: evalRes.totalScore,
      riskLevel: evalRes.riskLevel,
      status
    });
  });

  const total = BENCHMARK_DATA.length;
  const fnr = (fn + tp) > 0 ? (fn / (fn + tp)) * 100 : 0;
  const precision = (tp + fp) > 0 ? (tp / (tp + fp)) * 100 : 0;
  const recall = (tp + fn) > 0 ? (tp / (tp + fn)) * 100 : 0;
  const accuracy = total > 0 ? ((tp + tn) / total) * 100 : 0;
  const hoursSaved = (tn * 35) / 60;

  // Update UI Elements
  document.getElementById("cmTP").innerText = tp;
  document.getElementById("cmTN").innerText = tn;
  document.getElementById("cmFP").innerText = fp;
  document.getElementById("cmFN").innerText = fn;

  document.getElementById("metricFNR").innerText = `${fnr.toFixed(1)}%`;
  document.getElementById("metricRecall").innerText = `${recall.toFixed(1)}%`;
  document.getElementById("metricPrecision").innerText = `${precision.toFixed(1)}%`;
  document.getElementById("metricAccuracy").innerText = `${accuracy.toFixed(1)}%`;
  document.getElementById("metricHoursSaved").innerText = `${hoursSaved.toFixed(1)} hrs`;

  // Render Table
  const tbody = document.getElementById("backtestTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  evaluations.forEach(ev => {
    const tr = document.createElement("tr");
    let statusBadge = "background: rgba(36,161,72,0.2); color:#42be65;";
    if (ev.status.startsWith("FN")) statusBadge = "background: rgba(218,30,40,0.3); color:#ff8389;";
    else if (ev.status.startsWith("FP")) statusBadge = "background: rgba(241,194,27,0.2); color:#f1c21b;";

    tr.innerHTML = `
      <td><strong>#${ev.pr_number}</strong></td>
      <td>${ev.title}</td>
      <td><code>@${ev.author}</code></td>
      <td><strong>${ev.riskScore}</strong></td>
      <td><span class="badge-tag" style="background:var(--cds-layer-03);">${ev.riskLevel}</span></td>
      <td>${ev.incident ? `🔥 ${ev.sev}` : '✅ Clean/Cosmetic'}</td>
      <td><span class="badge-tag" style="${statusBadge}">${ev.status}</span></td>
    `;
    tr.addEventListener("click", () => {
      // Load into simulator
      document.getElementById("prTitleInput").value = ev.title;
      document.getElementById("prAuthorSelect").value = ev.author;
      currentFiles = JSON.parse(JSON.stringify(ev.files));
      renderFileList();
      runLiveEvaluation();
      // Switch tab to simulator
      document.querySelector('[data-tab="tabSimulator"]').click();
    });
    tbody.appendChild(tr);
  });
}

function calculateROI() {
  const teamSize = parseInt(document.getElementById("teamSizeInput")?.value || 30, 10);
  const prsPerWeek = parseInt(document.getElementById("prsPerWeekInput")?.value || 60, 10);
  const avgReviewMins = parseInt(document.getElementById("avgReviewTimeInput")?.value || 45, 10);

  // Assumptions backed by TPM benchmarks:
  // 40% of PRs are cosmetic/low risk (docs, tests, minor fixes, config)
  // PR Agent saves ~30 mins per cosmetic PR through fast-tracking and clear diff scoping.
  // Escaped defect reduction: ~3.5 SEV-1/SEV-2 outages prevented per year (each outage costs ~$40k).
  // Blended engineering hourly cost: $95/hr.

  const annualPRs = prsPerWeek * 52;
  const cosmeticPRs = annualPRs * 0.40;
  const hoursSavedPerYear = (cosmeticPRs * 30) / 60;
  const engineeringCostSavings = hoursSavedPerYear * 95;
  const outageSavings = 3.5 * 40000;
  const totalAnnualValue = engineeringCostSavings + outageSavings;

  document.getElementById("roiHoursSaved").innerText = Math.round(hoursSavedPerYear).toLocaleString();
  document.getElementById("roiEngSavings").innerText = `$${Math.round(engineeringCostSavings).toLocaleString()}`;
  document.getElementById("roiOutageSavings").innerText = `$${Math.round(outageSavings).toLocaleString()}`;
  document.getElementById("roiTotalValue").innerText = `$${Math.round(totalAnnualValue).toLocaleString()}`;
}

window.copyBotComment = function() {
  const text = document.getElementById("markdownBotComment")?.innerText;
  if (text) {
    navigator.clipboard.writeText(text);
    const btn = document.getElementById("copyBtn");
    if (btn) {
      btn.innerText = "Copied!";
      setTimeout(() => { btn.innerText = "Copy Markdown"; }, 1800);
    }
  }
};

document.addEventListener("DOMContentLoaded", initApp);
