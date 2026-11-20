"""
PR Risk Triage Agent - Core Scoring Engine
IBM DevOps Loop - Product Prototype
"""

import json
import math
import os
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

# Default Critical Path Weights
CRITICAL_PATH_PATTERNS = [
    (r"(^|/)(auth|security|crypto|jwt|session|oauth|iam)/", 28, "Authentication & Security Module"),
    (r"(^|/)(payment|billing|stripe|ledger|wallet|checkout)/", 30, "Payment & Financial Transactions"),
    (r"(^|/)(db|database|migrations?|schema|sql|models?)/", 25, "Database Schema & Migrations"),
    (r"(^|/)(infra|terraform|k8s|kubernetes|helm|docker|deploy|ci|cd|\.github)/", 22, "Infrastructure & CI/CD Pipeline"),
    (r"(^|/)(core|kernel|engine|protocol|networking|consensus)/", 24, "Core Engine & Low-Level Subsystems"),
    (r"(^|/)(api|routes|endpoints|controllers?)/", 16, "Public APIs & Routing"),
    (r"(^|/)(config|settings|env|\.env)/", 18, "Global Configuration & Environment"),
    (r"\.(sql|proto|graphql|tf|tfvars|lock|ya?ml)$", 14, "Config / Schema / Lockfile Definition"),
    (r"(^|/)(docs|documentation|examples?|\.md|\.txt)$", -15, "Documentation (Low Risk)"),
    (r"(^|/)(tests?|spec|mocks?|fixtures?)/", -10, "Test / Mock Files (Low Direct Production Risk)"),
]

# Historical Incident Database (Mock / Seed data of past incident correlations)
DEFAULT_HISTORICAL_INCIDENTS = [
    {
        "id": "INC-8821",
        "title": "Payment gateway deadlock during peak checkout",
        "severity": "SEV-1",
        "files_involved": [
            "src/payment/checkout.ts",
            "src/payment/stripe_gateway.ts",
            "db/migrations/20250412_payment_locks.sql"
        ],
        "root_cause": "Race condition in unindexed optimistic locking",
        "recency_days": 24,
        "blast_radius_impact": "High"
    },
    {
        "id": "INC-7430",
        "title": "Auth token bypass on token refresh endpoint",
        "severity": "SEV-1",
        "files_involved": [
            "src/auth/token_service.py",
            "src/auth/jwt_verifier.py",
            "src/api/v2/auth_controller.py"
        ],
        "root_cause": "Missing signature verification on kid mismatch",
        "recency_days": 65,
        "blast_radius_impact": "Critical"
    },
    {
        "id": "INC-6921",
        "title": "Database connection pool exhaustion on analytics sync",
        "severity": "SEV-2",
        "files_involved": [
            "src/db/connection_pool.ts",
            "src/analytics/event_processor.ts"
        ],
        "root_cause": "Unreleased connection in catch block",
        "recency_days": 110,
        "blast_radius_impact": "High"
    },
    {
        "id": "INC-5104",
        "title": "Terraform IAM policy over-permission vulnerability",
        "severity": "SEV-2",
        "files_involved": [
            "infra/terraform/iam_roles.tf",
            "infra/terraform/k8s_cluster.tf"
        ],
        "root_cause": "Wildcard wildcard S3 access grant",
        "recency_days": 150,
        "blast_radius_impact": "Medium"
    },
    {
        "id": "INC-4819",
        "title": "Memory leak in real-time notification socket worker",
        "severity": "SEV-3",
        "files_involved": [
            "src/realtime/socket_hub.go",
            "src/realtime/client_listener.go"
        ],
        "root_cause": "Unbounded map growth on client disconnect",
        "recency_days": 210,
        "blast_radius_impact": "Medium"
    }
]

# Author Knowledge Repository (Seed)
DEFAULT_AUTHOR_PROFILES = {
    "alice_sr_architect": {
        "repo_tenure_months": 36,
        "total_merged_prs": 420,
        "incident_revert_count": 1,
        "module_familiarity": {
            "payment": 0.95,
            "auth": 0.92,
            "db": 0.88,
            "infra": 0.85,
            "core": 0.90
        }
    },
    "bob_backend_mid": {
        "repo_tenure_months": 14,
        "total_merged_prs": 85,
        "incident_revert_count": 3,
        "module_familiarity": {
            "api": 0.80,
            "db": 0.65,
            "payment": 0.35,
            "auth": 0.20
        }
    },
    "carol_junior_newjoiner": {
        "repo_tenure_months": 2,
        "total_merged_prs": 8,
        "incident_revert_count": 1,
        "module_familiarity": {
            "docs": 0.90,
            "frontend": 0.60,
            "api": 0.25,
            "auth": 0.05,
            "payment": 0.05
        }
    },
    "dependabot": {
        "repo_tenure_months": 48,
        "total_merged_prs": 500,
        "incident_revert_count": 4,
        "module_familiarity": {
            "infra": 0.70,
            "config": 0.70
        }
    }
}


@dataclass
class FileChange:
    filename: str
    additions: int = 0
    deletions: int = 0
    status: str = "modified"  # modified, added, removed, renamed
    patch: str = ""


@dataclass
class PullRequestInput:
    pr_number: int
    title: str
    author: str
    base_branch: str = "main"
    head_branch: str = "feature/change"
    files: List[FileChange] = field(default_factory=list)
    description: str = ""
    is_draft: bool = False
    labels: List[str] = field(default_factory=list)


@dataclass
class RiskBreakdown:
    blast_radius_score: float  # 0-100 (Weight: 40%)
    incident_correlation_score: float  # 0-100 (Weight: 35%)
    author_risk_score: float  # 0-100 (Weight: 25%)
    total_risk_score: float  # 0-100
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    risk_label: str  # e.g., risk:critical-blocking-review
    key_drivers: List[str] = field(default_factory=list)
    correlated_incidents: List[Dict[str, Any]] = field(default_factory=list)
    critical_paths_detected: List[str] = field(default_factory=list)
    recommended_reviewers: List[str] = field(default_factory=list)
    recommended_checks: List[str] = field(default_factory=list)
    suggested_bot_comment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PRRiskEngine:
    """
    Intelligent PR Risk Evaluation Engine.
    Combines AST/Path blast radius, historical incident correlation, and author context.
    """

    def __init__(
        self,
        historical_incidents: Optional[List[Dict[str, Any]]] = None,
        author_profiles: Optional[Dict[str, Any]] = None,
        custom_critical_paths: Optional[List[tuple]] = None,
        weights: Optional[Dict[str, float]] = None
    ):
        self.incidents = historical_incidents or DEFAULT_HISTORICAL_INCIDENTS
        self.authors = author_profiles or DEFAULT_AUTHOR_PROFILES
        self.critical_paths = custom_critical_paths or CRITICAL_PATH_PATTERNS
        self.weights = weights or {
            "blast_radius": 0.40,
            "incident_correlation": 0.35,
            "author_risk": 0.25
        }

    def evaluate(self, pr: PullRequestInput) -> RiskBreakdown:
        key_drivers = []
        critical_paths_detected = []
        correlated_incidents = []
        recommended_reviewers = []
        recommended_checks = []

        # 1. Compute Blast Radius Score
        blast_score, blast_drivers, detected_paths = self._compute_blast_radius(pr)
        key_drivers.extend(blast_drivers)
        critical_paths_detected.extend(detected_paths)

        # 2. Compute Past Incident Correlation Score
        incident_score, incident_drivers, matched_incidents = self._compute_incident_correlation(pr)
        key_drivers.extend(incident_drivers)
        correlated_incidents.extend(matched_incidents)

        # 3. Compute Author Context & Experience Risk Score
        author_score, author_drivers, suggested_roles = self._compute_author_risk(pr, critical_paths_detected)
        key_drivers.extend(author_drivers)
        recommended_reviewers.extend(suggested_roles)

        # Weighted Aggregate Score
        w_blast = self.weights["blast_radius"]
        w_inc = self.weights["incident_correlation"]
        w_auth = self.weights["author_risk"]

        total_score = (blast_score * w_blast) + (incident_score * w_inc) + (author_score * w_auth)

        # Safety Guardrails: Prevent False Negatives on known SEV-1/SEV-2 incident files
        if correlated_incidents:
            highest_sev = min([inc.get("severity", "SEV-3") for inc in correlated_incidents])
            if highest_sev == "SEV-1":
                total_score = max(total_score, 55.0)
            elif highest_sev == "SEV-2":
                total_score = max(total_score, 45.0)
            else:
                total_score = max(total_score, 36.0)

        total_score = max(0.0, min(100.0, round(total_score, 1)))

        # Determine Risk Level & Label
        if total_score >= 80.0:
            risk_level = "CRITICAL"
            risk_label = "risk:critical-blocking-review"
            recommended_checks.append("Mandatory 2+ Senior/Principal Reviewers")
            recommended_checks.append("Staging Canary Deployment with Automated Rollback Guard")
            recommended_checks.append("End-to-End Stress/Idempotency Test Suite")
        elif total_score >= 60.0:
            risk_level = "HIGH"
            risk_label = "risk:high-targeted-review"
            recommended_checks.append("Domain Specialist Approval Required")
            recommended_checks.append("Integration Test Regression Suite Execution")
        elif total_score >= 35.0:
            risk_level = "MEDIUM"
            risk_label = "risk:medium-standard-review"
            recommended_checks.append("Standard Peer Review (1 Approver)")
            recommended_checks.append("Standard Unit/Lint CI Checks")
        else:
            risk_level = "LOW"
            risk_label = "risk:low-cosmetic"
            recommended_checks.append("Fast-Track / Auto-Merge Eligible upon passing CI")

        # Fallback reviewer suggestions
        if not recommended_reviewers:
            if "CRITICAL" in risk_level or "HIGH" in risk_level:
                recommended_reviewers.append("@team-leads")
                recommended_reviewers.append("@domain-architects")
            else:
                recommended_reviewers.append("@peer-reviewer")

        # Generate Suggested Bot Markdown Comment
        bot_comment = self._generate_markdown_comment(
            pr=pr,
            total_score=total_score,
            risk_level=risk_level,
            risk_label=risk_label,
            blast_score=blast_score,
            incident_score=incident_score,
            author_score=author_score,
            key_drivers=key_drivers,
            correlated_incidents=correlated_incidents,
            critical_paths_detected=critical_paths_detected,
            recommended_reviewers=recommended_reviewers,
            recommended_checks=recommended_checks
        )

        return RiskBreakdown(
            blast_radius_score=round(blast_score, 1),
            incident_correlation_score=round(incident_score, 1),
            author_risk_score=round(author_score, 1),
            total_risk_score=total_score,
            risk_level=risk_level,
            risk_label=risk_label,
            key_drivers=key_drivers[:6],
            correlated_incidents=correlated_incidents,
            critical_paths_detected=list(set(critical_paths_detected)),
            recommended_reviewers=list(set(recommended_reviewers)),
            recommended_checks=recommended_checks,
            suggested_bot_comment=bot_comment
        )

    def _compute_blast_radius(self, pr: PullRequestInput):
        score = 0.0
        drivers = []
        detected_paths = []

        total_files = len(pr.files)
        total_additions = sum(f.additions for f in pr.files)
        total_deletions = sum(f.deletions for f in pr.files)
        total_loc = total_additions + total_deletions

        # 1. File count baseline
        if total_files == 0:
            return 5.0, ["Empty diff or zero files touched."], []
        
        if total_files > 30:
            score += 35.0
            drivers.append(f"Very large blast radius: {total_files} files touched across repo.")
        elif total_files > 15:
            score += 25.0
            drivers.append(f"Broad blast radius: {total_files} files modified.")
        elif total_files > 5:
            score += 15.0
        else:
            score += 5.0

        # 2. Volume of lines changed (LOC)
        if total_loc > 1200:
            score += 30.0
            drivers.append(f"Massive code delta: +{total_additions}/-{total_deletions} ({total_loc} LOC).")
        elif total_loc > 400:
            score += 20.0
            drivers.append(f"Substantial code delta: {total_loc} lines altered.")
        elif total_loc > 100:
            score += 10.0
        elif total_loc < 25 and total_files <= 2:
            score -= 10.0
            drivers.append(f"Compact cosmetic diff ({total_loc} LOC).")

        # 3. Path criticality inspection
        path_penalty = 0.0
        is_only_docs_or_tests = True

        for f in pr.files:
            file_path = f.filename
            file_matched_critical = False

            for pattern, weight, description in self.critical_paths:
                if re.search(pattern, file_path, re.IGNORECASE):
                    if weight > 0:
                        path_penalty += weight
                        detected_paths.append(f"{file_path} ({description})")
                        file_matched_critical = True
                        is_only_docs_or_tests = False
                    elif weight < 0:
                        path_penalty += weight  # reduce risk for doc/test

            if not file_matched_critical and not re.search(r"(\.md|docs|tests?)", file_path):
                is_only_docs_or_tests = False

        if is_only_docs_or_tests:
            score = max(5.0, score * 0.2)
            drivers.append("Diff is isolated purely to documentation, tests, or non-production files.")
        else:
            if detected_paths:
                drivers.append(f"Touches {len(detected_paths)} high-criticality architecture boundary files.")

        score += min(45.0, path_penalty)

        # 4. Deletion vs Addition asymmetry (risky refactoring / breaking contract)
        if total_deletions > 250 and total_deletions > (total_additions * 2):
            score += 12.0
            drivers.append("High deletion ratio indicates breaking change / structural deprecation.")

        normalized_blast = max(0.0, min(100.0, score))
        return normalized_blast, drivers, detected_paths

    def _compute_incident_correlation(self, pr: PullRequestInput):
        score = 10.0  # baseline minimal baseline
        drivers = []
        matched_incidents = []

        touched_files = {f.filename for f in pr.files}

        for inc in self.incidents:
            inc_files = set(inc.get("files_involved", []))
            overlap = touched_files.intersection(inc_files)

            if overlap:
                severity = inc.get("severity", "SEV-3")
                recency_days = inc.get("recency_days", 90)

                # Time decay multiplier: more recent incidents matter more
                # Halflife ~ 90 days
                decay = math.exp(-0.005 * recency_days)

                if severity == "SEV-1":
                    base_inc_weight = 90.0
                    floor = 70.0
                elif severity == "SEV-2":
                    base_inc_weight = 70.0
                    floor = 50.0
                else:
                    base_inc_weight = 45.0
                    floor = 30.0

                inc_impact = max(floor, base_inc_weight * decay)
                score += inc_impact

                matched_info = {
                    "id": inc["id"],
                    "title": inc["title"],
                    "severity": inc["severity"],
                    "matching_files": list(overlap),
                    "recency_days": recency_days,
                    "root_cause": inc.get("root_cause", "Unspecified")
                }
                matched_incidents.append(matched_info)
                drivers.append(
                    f"Correlated with past {severity} outage ({inc['id']}: '{inc['title']}') in files: {', '.join(overlap)}."
                )

        if not matched_incidents:
            # Check for partial folder hotspot match
            matched_folder = False
            for inc in self.incidents:
                for f in pr.files:
                    folder = os.path.dirname(f.filename)
                    if folder and any(folder in inc_f for inc_f in inc.get("files_involved", [])):
                        score += 8.0
                        matched_folder = True
                        break
            if not matched_folder:
                score = max(5.0, score - 5.0)

        normalized_inc = max(0.0, min(100.0, score))
        return normalized_inc, drivers, matched_incidents

    def _compute_author_risk(self, pr: PullRequestInput, critical_paths: List[str]):
        author_name = pr.author
        drivers = []
        suggested_roles = []
        score = 30.0  # default baseline for unknown author

        author_data = self.authors.get(author_name)

        if not author_data:
            # Unknown or first-time contributor
            score = 65.0
            drivers.append(f"Author '{author_name}' has no recorded history in this repository (First-time / External author).")
            suggested_roles.append("@core-maintainers")
            if critical_paths:
                score += 20.0
                drivers.append("New contributor modifying tier-1 critical paths without prior merge track record.")
        else:
            tenure = author_data.get("repo_tenure_months", 0)
            merged_prs = author_data.get("total_merged_prs", 0)
            reverts = author_data.get("incident_revert_count", 0)
            familiarity_map = author_data.get("module_familiarity", {})

            # Tenure & merge volume bonus/penalty
            if merged_prs > 150 and tenure > 24:
                score = 10.0
                drivers.append(f"Author '{author_name}' is a veteran maintainer ({merged_prs} PRs, {tenure}m tenure).")
            elif merged_prs > 40:
                score = 25.0
            else:
                score = 55.0
                drivers.append(f"Author '{author_name}' is relatively junior/new ({merged_prs} PRs merged).")

            # Prior revert rate penalty
            if reverts > 2:
                revert_penalty = min(25.0, reverts * 6.0)
                score += revert_penalty
                drivers.append(f"Author has {reverts} past incident rollbacks/reverts on record.")

            # Domain familiarity cross-check against touched files
            for f in pr.files:
                for domain, fam_score in familiarity_map.items():
                    if domain in f.filename.lower():
                        if fam_score < 0.3:
                            score += 20.0
                            drivers.append(f"Author has low domain expertise ({int(fam_score*100)}%) in '{domain}' subsystem.")
                            suggested_roles.append(f"@{domain}-domain-lead")
                        elif fam_score > 0.8:
                            score = max(5.0, score - 8.0)
                            suggested_roles.append(f"@{domain}-peer")

        normalized_auth = max(0.0, min(100.0, score))
        return normalized_auth, drivers, suggested_roles

    def _generate_markdown_comment(
        self,
        pr: PullRequestInput,
        total_score: float,
        risk_level: str,
        risk_label: str,
        blast_score: float,
        incident_score: float,
        author_score: float,
        key_drivers: List[str],
        correlated_incidents: List[Dict[str, Any]],
        critical_paths_detected: List[str],
        recommended_reviewers: List[str],
        recommended_checks: List[str]
    ) -> str:
        unique_drivers = list(dict.fromkeys(key_drivers))
        unique_reviewers = list(dict.fromkeys(recommended_reviewers))

        lines = [
            f"### 🛡️ IBM DevOps Loop — PR Risk Triage Agent",
            f"",
            f"**Assigned Risk Tier**: `{risk_level}` (`{risk_label}`) | **Composite Score**: **`{total_score}/100`**",
            f"",
            f"| Metric Component | Score | Weight | Assessment |",
            f"| :--- | :---: | :---: | :--- |",
            f"| 🌐 **Blast Radius** | `{round(blast_score, 1)}/100` | 40% | {len(pr.files)} files, {sum(f.additions + f.deletions for f in pr.files)} LOC altered |",
            f"| 🔥 **Incident Correlation** | `{round(incident_score, 1)}/100` | 35% | {len(correlated_incidents)} matching past incident hotspots |",
            f"| 👤 **Author & Domain Context** | `{round(author_score, 1)}/100` | 25% | Profile check for author `@{pr.author}` |",
            f"",
            f"---",
            f"#### 🔍 Key Risk Drivers",
        ]

        for d in unique_drivers[:5]:
            lines.append(f"- ⚠️ {d}")

        if correlated_incidents:
            lines.append("")
            lines.append("#### 🚨 Historical Incidents Correlated with Modified Code")
            for inc in correlated_incidents:
                lines.append(
                    f"- **{inc['id']}** (`{inc['severity']}`): *{inc['title']}* ({inc['recency_days']} days ago)"
                )
                lines.append(f"  - Root cause: `{inc['root_cause']}`")
                lines.append(f"  - Overlapping files: `{', '.join(inc['matching_files'])}`")

        lines.append("")
        lines.append("#### 🎯 Recommended Action Plan")
        lines.append(f"- **Suggested Reviewers**: {', '.join(unique_reviewers) if unique_reviewers else '@peer'}")
        for check in recommended_checks:
            lines.append(f"- [ ] {check}")

        lines.append("")
        lines.append(
            f"*> 💡 Automated by IBM DevOps Loop PR Risk Triage Agent (POC). Target: <2.0% False Negative Rate.*"
        )

        return "\n".join(lines)
