"""
PR Risk Triage Agent - Historical Incident & PR Backtesting Benchmark
Provides measurable False Negative Rate (FNR), Precision, Recall, and Reviewer Hours Saved.
"""

import json
import math
import os
import sys
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pr_risk_engine import PRRiskEngine, PullRequestInput, FileChange


HISTORICAL_PR_DATASET = [
    # --- INCIDENT-CAUSING PRs (Ground Truth: RISKY) ---
    {
        "pr_number": 1001,
        "title": "Migrate payment ledger table index",
        "author": "carol_junior_newjoiner",
        "ground_truth_incident": True,
        "incident_sev": "SEV-1",
        "files": [
            {"filename": "src/payment/checkout.ts", "additions": 140, "deletions": 20},
            {"filename": "db/migrations/20250412_payment_locks.sql", "additions": 40, "deletions": 5}
        ]
    },
    {
        "pr_number": 1002,
        "title": "Upgrade auth token verification to handle cross-region JWTs",
        "author": "bob_backend_mid",
        "ground_truth_incident": True,
        "incident_sev": "SEV-1",
        "files": [
            {"filename": "src/auth/jwt_verifier.py", "additions": 88, "deletions": 12},
            {"filename": "src/auth/token_service.py", "additions": 45, "deletions": 10}
        ]
    },
    {
        "pr_number": 1003,
        "title": "Implement background analytics batch connection manager",
        "author": "bob_backend_mid",
        "ground_truth_incident": True,
        "incident_sev": "SEV-2",
        "files": [
            {"filename": "src/db/connection_pool.ts", "additions": 110, "deletions": 60},
            {"filename": "src/analytics/event_processor.ts", "additions": 95, "deletions": 20}
        ]
    },
    {
        "pr_number": 1004,
        "title": "Add wildcard S3 sync policy for k8s deployment automation",
        "author": "carol_junior_newjoiner",
        "ground_truth_incident": True,
        "incident_sev": "SEV-2",
        "files": [
            {"filename": "infra/terraform/iam_roles.tf", "additions": 50, "deletions": 5},
            {"filename": "infra/terraform/k8s_cluster.tf", "additions": 30, "deletions": 2}
        ]
    },
    {
        "pr_number": 1005,
        "title": "Global routing controller rewrite for v2 gateway",
        "author": "external_contractor_x",
        "ground_truth_incident": True,
        "incident_sev": "SEV-1",
        "files": [
            {"filename": "src/api/v2/auth_controller.py", "additions": 320, "deletions": 180},
            {"filename": "src/core/router.py", "additions": 210, "deletions": 90},
            {"filename": "src/payment/stripe_gateway.ts", "additions": 60, "deletions": 10}
        ]
    },
    {
        "pr_number": 1006,
        "title": "Database connection heartbeat refactoring",
        "author": "alice_sr_architect",
        "ground_truth_incident": True,
        "incident_sev": "SEV-2",
        "files": [
            {"filename": "src/db/connection_pool.ts", "additions": 190, "deletions": 140}
        ]
    },
    {
        "pr_number": 1007,
        "title": "Realtime notification socket thread management",
        "author": "bob_backend_mid",
        "ground_truth_incident": True,
        "incident_sev": "SEV-3",
        "files": [
            {"filename": "src/realtime/socket_hub.go", "additions": 80, "deletions": 25},
            {"filename": "src/realtime/client_listener.go", "additions": 45, "deletions": 15}
        ]
    },
    {
        "pr_number": 1008,
        "title": "Consensus state machine optimization",
        "author": "carol_junior_newjoiner",
        "ground_truth_incident": True,
        "incident_sev": "SEV-1",
        "files": [
            {"filename": "src/core/kernel/consensus.go", "additions": 410, "deletions": 290},
            {"filename": "src/core/protocol.go", "additions": 150, "deletions": 70}
        ]
    },

    # --- COSMETIC & LOW RISK PRs (Ground Truth: SAFE / COSMETIC) ---
    {
        "pr_number": 2001,
        "title": "Fix typo in onboarding documentation and API docstrings",
        "author": "carol_junior_newjoiner",
        "ground_truth_incident": False,
        "files": [
            {"filename": "docs/quickstart.md", "additions": 8, "deletions": 8},
            {"filename": "README.md", "additions": 2, "deletions": 2}
        ]
    },
    {
        "pr_number": 2002,
        "title": "Add unit tests for string utility functions",
        "author": "bob_backend_mid",
        "ground_truth_incident": False,
        "files": [
            {"filename": "tests/unit/utils_test.py", "additions": 65, "deletions": 0},
            {"filename": "tests/fixtures/sample_payload.json", "additions": 20, "deletions": 0}
        ]
    },
    {
        "pr_number": 2003,
        "title": "Update copyright headers to 2026",
        "author": "alice_sr_architect",
        "ground_truth_incident": False,
        "files": [
            {"filename": "LICENSE", "additions": 1, "deletions": 1},
            {"filename": "docs/contributing.md", "additions": 2, "deletions": 2}
        ]
    },
    {
        "pr_number": 2004,
        "title": "Bump linter config and prettier formatting rules",
        "author": "bob_backend_mid",
        "ground_truth_incident": False,
        "files": [
            {"filename": ".eslintrc.json", "additions": 6, "deletions": 4},
            {"filename": ".prettierrc", "additions": 2, "deletions": 1}
        ]
    },
    {
        "pr_number": 2005,
        "title": "Improve API endpoint documentation with OpenAPI schema comments",
        "author": "carol_junior_newjoiner",
        "ground_truth_incident": False,
        "files": [
            {"filename": "docs/api/v2.md", "additions": 75, "deletions": 10},
            {"filename": "examples/curl_demo.sh", "additions": 15, "deletions": 2}
        ]
    },
    {
        "pr_number": 2006,
        "title": "Add mocks for payment integration tests",
        "author": "alice_sr_architect",
        "ground_truth_incident": False,
        "files": [
            {"filename": "tests/mocks/stripe_mock.ts", "additions": 120, "deletions": 0},
            {"filename": "tests/unit/payment_mock_test.ts", "additions": 80, "deletions": 5}
        ]
    },

    # --- STANDARD / MEDIUM FEATURE PRs (Ground Truth: SAFE / STANDARD) ---
    {
        "pr_number": 3001,
        "title": "Add user preference dropdown in settings UI",
        "author": "bob_backend_mid",
        "ground_truth_incident": False,
        "files": [
            {"filename": "src/frontend/components/UserPreferences.tsx", "additions": 65, "deletions": 12},
            {"filename": "src/frontend/styles/preferences.css", "additions": 30, "deletions": 0}
        ]
    },
    {
        "pr_number": 3002,
        "title": "Add export CSV endpoint for user audit logs",
        "author": "alice_sr_architect",
        "ground_truth_incident": False,
        "files": [
            {"filename": "src/api/export_controller.py", "additions": 45, "deletions": 5},
            {"filename": "src/services/csv_generator.py", "additions": 55, "deletions": 0}
        ]
    },
    {
        "pr_number": 3003,
        "title": "Update landing page marketing banner",
        "author": "carol_junior_newjoiner",
        "ground_truth_incident": False,
        "files": [
            {"filename": "src/frontend/banner.tsx", "additions": 18, "deletions": 12}
        ]
    },
    {
        "pr_number": 3004,
        "title": "Add caching layer for user profile avatar URLs",
        "author": "alice_sr_architect",
        "ground_truth_incident": False,
        "files": [
            {"filename": "src/services/avatar_cache.py", "additions": 40, "deletions": 8},
            {"filename": "tests/unit/avatar_cache_test.py", "additions": 30, "deletions": 0}
        ]
    }
]


class BenchmarkEvaluator:
    """
    Evaluates PR Risk Triage Agent accuracy against historical ground-truth incident data.
    """

    def __init__(self, engine: PRRiskEngine = None, risk_threshold: float = 35.0):
        self.engine = engine or PRRiskEngine()
        self.risk_threshold = risk_threshold

    def run_benchmark(self, dataset: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        data = dataset or HISTORICAL_PR_DATASET
        tp = 0  # True Positive: Risky PR correctly flagged as High/Critical/Medium (> threshold)
        tn = 0  # True Negative: Safe/Cosmetic PR correctly flagged as Low (<= threshold)
        fp = 0  # False Positive: Safe/Cosmetic PR flagged as Risky (> threshold)
        fn = 0  # False Negative: Risky/Incident-causing PR incorrectly flagged as Low (CRITICAL DEFECT!)

        sev1_fn = 0  # SEV-1 missed
        results_detail = []

        total_prs = len(data)

        for item in data:
            files = [
                FileChange(
                    filename=f["filename"],
                    additions=f.get("additions", 0),
                    deletions=f.get("deletions", 0)
                ) for f in item["files"]
            ]
            pr = PullRequestInput(
                pr_number=item["pr_number"],
                title=item["title"],
                author=item["author"],
                files=files
            )
            eval_res = self.engine.evaluate(pr)
            score = eval_res.total_risk_score
            is_flagged_risky = score >= self.risk_threshold
            ground_truth = item.get("ground_truth_incident", False)
            sev = item.get("incident_sev", None)

            if ground_truth:
                if is_flagged_risky:
                    tp += 1
                    status = "TP (Caught Risky PR)"
                else:
                    fn += 1
                    status = "FN (MISSED INCIDENT!)"
                    if sev == "SEV-1":
                        sev1_fn += 1
            else:
                if is_flagged_risky:
                    fp += 1
                    status = "FP (False Alarm on Safe PR)"
                else:
                    tn += 1
                    status = "TN (Correctly Fast-Tracked Cosmetic PR)"

            results_detail.append({
                "pr_number": item["pr_number"],
                "title": item["title"],
                "author": item["author"],
                "risk_score": score,
                "risk_level": eval_res.risk_level,
                "ground_truth_incident": ground_truth,
                "incident_sev": sev,
                "status": status,
                "key_drivers": eval_res.key_drivers
            })

        # Metrics calculation
        fnr = (fn / (fn + tp)) * 100.0 if (fn + tp) > 0 else 0.0
        precision = (tp / (tp + fp)) * 100.0 if (tp + fp) > 0 else 0.0
        recall = (tp / (tp + fn)) * 100.0 if (tp + fn) > 0 else 0.0
        accuracy = ((tp + tn) / total_prs) * 100.0 if total_prs > 0 else 0.0
        specificity = (tn / (tn + fp)) * 100.0 if (tn + fp) > 0 else 0.0

        # Reviewer hours saved calculation:
        # Assume cosmetic PR review takes 45 mins without agent, 10 mins with fast-track triage.
        # Savings per TN = 35 mins.
        reviewer_hours_saved = (tn * 35) / 60.0

        return {
            "total_evaluated_prs": total_prs,
            "risk_threshold": self.risk_threshold,
            "confusion_matrix": {
                "true_positives": tp,
                "true_negatives": tn,
                "false_positives": fp,
                "false_negatives": fn,
                "sev1_escapes": sev1_fn
            },
            "metrics": {
                "false_negative_rate_pct": round(fnr, 2),
                "recall_sensitivity_pct": round(recall, 2),
                "precision_pct": round(precision, 2),
                "specificity_pct": round(specificity, 2),
                "overall_accuracy_pct": round(accuracy, 2),
                "estimated_reviewer_hours_saved": round(reviewer_hours_saved, 1),
                "cosmetic_fast_track_rate_pct": round((tn / (tn + fp)) * 100.0, 1) if (tn + fp) > 0 else 0.0
            },
            "pr_evaluations": results_detail
        }


if __name__ == "__main__":
    evaluator = BenchmarkEvaluator()
    bench_results = evaluator.run_benchmark()
    print("=" * 65)
    print("🎯 PR RISK TRIAGE AGENT - BACKTESTING BENCHMARK REPORT")
    print("=" * 65)
    print(f"Total PRs Tested     : {bench_results['total_evaluated_prs']}")
    print(f"False-Negative Rate  : {bench_results['metrics']['false_negative_rate_pct']}% (Target: < 2.0%)")
    print(f"SEV-1 Escaped Defect : {bench_results['confusion_matrix']['sev1_escapes']}")
    print(f"Recall (Sensitivity) : {bench_results['metrics']['recall_sensitivity_pct']}%")
    print(f"Precision            : {bench_results['metrics']['precision_pct']}%")
    print(f"Cosmetic Fast-Track  : {bench_results['metrics']['cosmetic_fast_track_rate_pct']}%")
    print(f"Reviewer Time Saved  : {bench_results['metrics']['estimated_reviewer_hours_saved']} hours across dataset")
    print("=" * 65)
