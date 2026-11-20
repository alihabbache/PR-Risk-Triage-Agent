"""
PR Risk Triage Agent - GitHub Action Runner & CLI Tool
Interacts with GitHub API or local JSON mock to analyze PRs and post triage comments.
"""

import argparse
import json
import os
import sys
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pr_risk_engine import PRRiskEngine, PullRequestInput, FileChange


def parse_github_event(event_path: str) -> PullRequestInput:
    """Parses standard GitHub Actions pull_request event payload."""
    with open(event_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pr_data = data.get("pull_request", {})
    pr_number = pr_data.get("number", 0)
    title = pr_data.get("title", "Untitled PR")
    author = pr_data.get("user", {}).get("login", "unknown")
    base_branch = pr_data.get("base", {}).get("ref", "main")
    head_branch = pr_data.get("head", {}).get("ref", "feature")
    description = pr_data.get("body", "") or ""

    # Note: In real GH Action, files are fetched via octokit or GH REST API
    # Here we support mock or pre-fetched files
    files = []
    if "mock_files" in pr_data:
        for f in pr_data["mock_files"]:
            files.append(
                FileChange(
                    filename=f.get("filename", ""),
                    additions=f.get("additions", 0),
                    deletions=f.get("deletions", 0),
                    status=f.get("status", "modified")
                )
            )

    return PullRequestInput(
        pr_number=pr_number,
        title=title,
        author=author,
        base_branch=base_branch,
        head_branch=head_branch,
        files=files,
        description=description
    )


def run_cli():
    parser = argparse.ArgumentParser(description="PR Risk Triage Agent CLI")
    parser.add_argument("--event-path", help="Path to GitHub event.json payload")
    parser.add_argument("--pr-json", help="Path to custom PR json input")
    parser.add_argument("--author", default="alice_sr_architect", help="PR Author username")
    parser.add_argument("--title", default="Demo Pull Request", help="PR Title")
    parser.add_argument("--files", nargs="*", help="List of file paths touched (format: path:additions:deletions)")
    parser.add_argument("--output-json", help="Save triage result breakdown to JSON file")
    parser.add_argument("--github-output", help="Write step outputs for GitHub Actions environment", default=None)

    args = parser.parse_args()

    engine = PRRiskEngine()

    if args.event_path and os.path.exists(args.event_path):
        pr = parse_github_event(args.event_path)
    elif args.pr_json and os.path.exists(args.pr_json):
        with open(args.pr_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            files = [
                FileChange(
                    filename=fc["filename"],
                    additions=fc.get("additions", 0),
                    deletions=fc.get("deletions", 0)
                ) for fc in data.get("files", [])
            ]
            pr = PullRequestInput(
                pr_number=data.get("pr_number", 1),
                title=data.get("title", "Demo PR"),
                author=data.get("author", "unknown"),
                files=files
            )
    elif args.files:
        files = []
        for file_spec in args.files:
            parts = file_spec.split(":")
            filename = parts[0]
            adds = int(parts[1]) if len(parts) > 1 else 10
            dels = int(parts[2]) if len(parts) > 2 else 2
            files.append(FileChange(filename=filename, additions=adds, deletions=dels))
        pr = PullRequestInput(
            pr_number=999,
            title=args.title,
            author=args.author,
            files=files
        )
    else:
        # Default sample run
        pr = PullRequestInput(
            pr_number=101,
            title="Update payment checkout locking logic",
            author="carol_junior_newjoiner",
            files=[
                FileChange("src/payment/checkout.ts", additions=95, deletions=35),
                FileChange("db/migrations/2026_03_payment.sql", additions=12, deletions=0),
                FileChange("docs/checkout.md", additions=5, deletions=1)
            ]
        )

    breakdown = engine.evaluate(pr)

    print("\n" + "=" * 65)
    print("🛡️  PR RISK TRIAGE EVALUATION REPORT")
    print("=" * 65)
    print(f"PR #{pr.pr_number}: {pr.title}")
    print(f"Author: {pr.author} | Files Touched: {len(pr.files)}")
    print(f"Composite Risk Score : {breakdown.total_risk_score} / 100")
    print(f"Risk Tier            : {breakdown.risk_level}")
    print(f"Recommended Label    : {breakdown.risk_label}")
    print(f"Blast Radius Score   : {breakdown.blast_radius_score} / 100")
    print(f"Incident Correlation : {breakdown.incident_correlation_score} / 100")
    print(f"Author Risk Score    : {breakdown.author_risk_score} / 100")
    print("\nKey Drivers:")
    for kd in breakdown.key_drivers:
        print(f" • {kd}")

    if breakdown.correlated_incidents:
        print("\nHistorical Incident Correlation:")
        for inc in breakdown.correlated_incidents:
            print(f" • [{inc['severity']}] {inc['id']}: {inc['title']} (Files: {', '.join(inc['matching_files'])})")

    print("\nSuggested PR Markdown Comment:")
    print("-" * 50)
    print(breakdown.suggested_bot_comment)
    print("-" * 50)

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(breakdown.to_dict(), f, indent=2)
        print(f"\n[✓] Results exported to {args.output_json}")

    # Set GitHub Actions output if running in GH workflow
    gh_output_path = args.github_output or os.environ.get("GITHUB_OUTPUT")
    if gh_output_path and os.path.exists(gh_output_path):
        with open(gh_output_path, "a", encoding="utf-8") as f:
            f.write(f"risk_score={breakdown.total_risk_score}\n")
            f.write(f"risk_level={breakdown.risk_level}\n")
            f.write(f"risk_label={breakdown.risk_label}\n")


if __name__ == "__main__":
    run_cli()
