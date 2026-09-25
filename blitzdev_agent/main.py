"""
BlitzDev CLI — Main Entrypoint
===============================
Usage:
    python -m blitzdev_agent --repo ./demo_api --pr 42
    python -m blitzdev_agent --repo ./demo-api
"""
import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

from .analyzer import BlitzDevAnalyzer
from .formatter import PRCommentFormatter
from .test_generator import TestGenerator
from .rules import Severity


def generate_sarif(result, repo_path: Path) -> dict:
    """Generate a standard SARIF v2.1.0 report for CI/CD and GitHub code scanning."""
    sarif_rules = []
    rule_indices = {}
    sarif_results = []

    for i, rule in enumerate(sorted(list({f.rule.id: f.rule for f in result.findings}.values()), key=lambda r: r.id)):
        rule_indices[rule.id] = i
        sarif_level = "error" if rule.severity == Severity.CRITICAL else "warning" if rule.severity == Severity.WARNING else "note"
        sarif_rules.append({
            "id": rule.id,
            "name": rule.title.replace(" ", ""),
            "shortDescription": {"text": rule.title},
            "fullDescription": {"text": rule.description},
            "defaultConfiguration": {"level": sarif_level},
            "help": {"text": f"Remediation: {rule.remediation}"},
            "properties": {
                "category": rule.category.value,
                "severity": rule.severity.value,
                "security-severity": "8.5" if rule.severity == Severity.CRITICAL else "5.0" if rule.severity == Severity.WARNING else "2.0"
            }
        })

    for finding in result.findings:
        sarif_level = "error" if finding.rule.severity == Severity.CRITICAL else "warning" if finding.rule.severity == Severity.WARNING else "note"
        sarif_results.append({
            "ruleId": finding.rule.id,
            "ruleIndex": rule_indices[finding.rule.id],
            "level": sarif_level,
            "message": {
                "text": f"[{finding.rule.id}] {finding.rule.title}: {finding.rule.description}"
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": finding.file_path,
                            "uriBaseId": "%SRCROOT%"
                        },
                        "region": {
                            "startLine": max(1, finding.line_number),
                            "startColumn": 1
                        }
                    }
                }
            ]
        })

    return {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "BlitzDev FinTech Validator",
                        "semanticVersion": "0.1.0",
                        "organization": "IBM Bob 2.0 / Team Royal Code",
                        "rules": sarif_rules
                    }
                },
                "results": sarif_results
            }
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="BlitzDev — FinTech-Aware PR Guardian powered by IBM Bob 2.0")
    parser.add_argument("--repo", default="./demo_api", help="Path to the repository to analyze")
    parser.add_argument("--pr", type=int, default=None, help="PR number (for report metadata)")
    parser.add_argument("--output", default="output", help="Output directory for reports")
    parser.add_argument("--format", choices=["markdown", "json", "sarif", "all"], default="all")
    args = parser.parse_args()

    repo_path_raw = args.repo
    # Handle demo-api vs demo_api seamlessly
    if not os.path.exists(repo_path_raw) and os.path.exists("demo_api") and "demo-api" in repo_path_raw:
        repo_path_raw = "demo_api"
    elif not os.path.exists(repo_path_raw) and os.path.exists("demo-api") and "demo_api" in repo_path_raw:
        repo_path_raw = "demo-api"

    repo_path = Path(repo_path_raw).resolve()
    if not repo_path.exists():
        print(f"❌ Error: Repository path '{args.repo}' does not exist.")
        sys.exit(1)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🛡️  BlitzDev — FinTech-Aware PR Guardian (IBM Bob 2.0)")
    print(f"🎯 Target Repository : {repo_path}")
    if args.pr:
        print(f"📦 Pull Request      : #{args.pr}")
    print("=" * 60)

    # Step 1: Run FinTech Validator Analysis
    print("\n[1/5] 🔍 Scanning codebase with FinTech Validator Mode...")
    analyzer = BlitzDevAnalyzer(str(repo_path))
    result = analyzer.analyze()
    print(f"      Analyzed {result.files_analyzed} files across database, routes, and services.")
    print(f"      Findings: {result.critical_count} 🔴 CRITICAL, {result.warning_count} ⚠️ WARNING, {result.info_count} ℹ️ INFO")

    # Step 2: Generate Formatted PR Comment (Markdown)
    print("\n[2/5] 📝 Formatting GitHub PR review comment & Blast Radius map...")
    formatter = PRCommentFormatter()
    report_md = formatter.format(result, pr_url=f"PR #{args.pr}" if args.pr else "")

    report_path = out_dir / "blitzdev_report.md"
    pr_comment_path = out_dir / "PR_COMMENT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    with open(pr_comment_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"      Saved PR comment to: {pr_comment_path}")

    # Step 3: Generate SARIF Report
    print("\n[3/5] 🛡️  Generating SARIF security audit standard output...")
    sarif_data = generate_sarif(result, repo_path)
    sarif_path = out_dir / "blitzdev_report.sarif"
    with open(sarif_path, "w", encoding="utf-8") as f:
        json.dump(sarif_data, f, indent=2)
    print(f"      Saved SARIF report to: {sarif_path}")

    # Step 4: Generate Targeted Exploit Tests
    print("\n[4/5] ⚡ Generating targeted pytest-asyncio race condition tests...")
    test_gen = TestGenerator(output_dir=str(out_dir))
    test_code = test_gen.generate(result)
    test_file = test_gen.save(test_code, filename="test_fintech_race_condition.py")
    print(f"      Saved exploit tests to: {test_file}")

    # Step 5: Save Bob Task Session Snapshot
    print("\n[5/5] 📸 Recording IBM Bob 2.0 task session snapshot...")
    session_dir = Path("bob_sessions")
    session_dir.mkdir(exist_ok=True)
    timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    session_file = session_dir / f"session_{timestamp_str}.json"

    session_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": "FinTech PR Guardian Automated Security Review",
        "engine": "IBM Bob 2.0 (Agent Mode)",
        "repo": str(repo_path),
        "pr": args.pr,
        "files_analyzed": result.files_analyzed,
        "metrics": {
            "critical_vulnerabilities": result.critical_count,
            "warnings": result.warning_count,
            "info": result.info_count
        },
        "artifacts_generated": [
            str(report_path),
            str(pr_comment_path),
            str(sarif_path),
            str(test_file)
        ]
    }
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)
    print(f"      Session snapshot saved: {session_file}")

    print("\n" + "=" * 60)
    print("✅ BlitzDev execution finished successfully!")
    print(f"👉 Run exploit test with: pytest {test_file} -v")
    print("=" * 60)


if __name__ == "__main__":
    main()
