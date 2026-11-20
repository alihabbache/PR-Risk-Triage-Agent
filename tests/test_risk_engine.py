"""
Unit & Integration Tests for PR Risk Triage Agent
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
from pr_risk_engine import PRRiskEngine, PullRequestInput, FileChange
from backtester import BenchmarkEvaluator, HISTORICAL_PR_DATASET


class TestPRRiskEngine(unittest.TestCase):

    def setUp(self):
        self.engine = PRRiskEngine()

    def test_cosmetic_doc_pr_receives_low_risk(self):
        pr = PullRequestInput(
            pr_number=1,
            title="Update installation instructions in README",
            author="carol_junior_newjoiner",
            files=[
                FileChange("README.md", additions=5, deletions=2),
                FileChange("docs/setup.md", additions=12, deletions=1)
            ]
        )
        result = self.engine.evaluate(pr)
        self.assertEqual(result.risk_level, "LOW")
        self.assertEqual(result.risk_label, "risk:low-cosmetic")
        self.assertLess(result.total_risk_score, 35.0)
        self.assertIn("documentation", ("".join(result.key_drivers) + "".join(result.critical_paths_detected)).lower())

    def test_auth_security_pr_receives_high_or_critical_risk(self):
        pr = PullRequestInput(
            pr_number=2,
            title="Refactor JWT token validation and kid lookup",
            author="carol_junior_newjoiner",
            files=[
                FileChange("src/auth/jwt_verifier.py", additions=90, deletions=20),
                FileChange("src/auth/token_service.py", additions=40, deletions=5)
            ]
        )
        result = self.engine.evaluate(pr)
        self.assertIn(result.risk_level, ["HIGH", "CRITICAL"])
        self.assertGreaterEqual(result.total_risk_score, 60.0)
        self.assertTrue(len(result.correlated_incidents) > 0)
        self.assertTrue(any("INC-7430" == inc["id"] for inc in result.correlated_incidents))

    def test_database_migration_with_past_incident_correlation(self):
        pr = PullRequestInput(
            pr_number=3,
            title="Add payment lock migration",
            author="bob_backend_mid",
            files=[
                FileChange("src/payment/checkout.ts", additions=150, deletions=40),
                FileChange("db/migrations/20250412_payment_locks.sql", additions=30, deletions=0)
            ]
        )
        result = self.engine.evaluate(pr)
        self.assertIn(result.risk_level, ["HIGH", "CRITICAL"])
        self.assertGreaterEqual(result.total_risk_score, 60.0)
        self.assertTrue(any(inc["severity"] == "SEV-1" for inc in result.correlated_incidents))

    def test_senior_architect_routine_pr_gets_moderate_score(self):
        pr = PullRequestInput(
            pr_number=4,
            title="Small helper in API controller",
            author="alice_sr_architect",
            files=[
                FileChange("src/api/helpers.py", additions=15, deletions=5)
            ]
        )
        result = self.engine.evaluate(pr)
        self.assertIn(result.risk_level, ["LOW", "MEDIUM"])
        self.assertLess(result.total_risk_score, 50.0)

    def test_backtester_meets_target_zero_false_negatives(self):
        evaluator = BenchmarkEvaluator(risk_threshold=35.0)
        res = evaluator.run_benchmark()
        self.assertEqual(res["metrics"]["false_negative_rate_pct"], 0.0)
        self.assertEqual(res["confusion_matrix"]["sev1_escapes"], 0)
        self.assertGreaterEqual(res["metrics"]["recall_sensitivity_pct"], 95.0)
        self.assertGreater(res["metrics"]["estimated_reviewer_hours_saved"], 0.0)


if __name__ == "__main__":
    unittest.main()
