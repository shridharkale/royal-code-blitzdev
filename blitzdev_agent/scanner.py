import json
import sys
from pathlib import Path
from blitzdev_agent.analyzer import BlitzDevAnalyzer
from blitzdev_agent.rules import Severity

def export_sarif(result, output_path: Path):
    """Synthesize valid OASIS SARIF v2.1.0 security report."""
    rules_map = {}
    sarif_results = []

    for f in result.findings:
        if f.rule.id not in rules_map:
            rules_map[f.rule.id] = {
                "id": f.rule.id,
                "name": f.rule.title.replace(" ", ""),
                "shortDescription": {"text": f.rule.title},
                "fullDescription": {"text": f.rule.description},
                "help": {"text": f.rule.remediation}
            }

        level = "error" if f.rule.severity == Severity.CRITICAL else ("warning" if f.rule.severity == Severity.WARNING else "note")
        sarif_results.append({
            "ruleId": f.rule.id,
            "level": level,
            "message": {"text": f"{f.rule.title}: {f.rule.description}"},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": f.file_path},
                        "region": {
                            "startLine": f.line_number,
                            "snippet": {"text": f.line_content}
                        }
                    }
                }
            ]
        })

    sarif_data = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "BlitzDev FinTech PR Guardian",
                        "semanticVersion": "1.0.0",
                        "rules": list(rules_map.values())
                    }
                },
                "results": sarif_results
            }
        ]
    }

    output_path.write_text(json.dumps(sarif_data, indent=2), encoding="utf-8")

def run_scan(target_dir: str = "."):
    repo_path = Path(target_dir).resolve()
    analyzer = BlitzDevAnalyzer(str(repo_path))
    result = analyzer.analyze()

    output_dir = repo_path / "output"
    output_dir.mkdir(exist_ok=True)

    # 1. Export JSON findings
    output_data = [
        {
            "rule_id": f.rule.id,
            "title": f.rule.title,
            "severity": f.rule.severity.value,
            "category": f.rule.category.value,
            "description": f.rule.description,
            "remediation": f.rule.remediation,
            "file_path": f.file_path,
            "line_number": f.line_number,
            "line_content": f.line_content
        }
        for f in result.findings
    ]
    with open(output_dir / "findings.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    # 2. Export OASIS SARIF v2.1.0
    export_sarif(result, output_dir / "blitzdev_report.sarif")

    print("\n" + "=" * 80)
    print(f"🛡️  BLITZDEV FINTECH SECURITY SCAN: {len(result.findings)} VULNERABILITIES IDENTIFIED")
    print("=" * 80)
    print(f"Files Analyzed:  {result.files_analyzed}")
    print(f"🔴 Critical:     {result.critical_count}")
    print(f"⚠️  Warnings:     {result.warning_count}")
    print(f"ℹ️  Info:         {result.info_count}")
    print("=" * 80)

    for f in result.findings[:5]:
        print(f"[{f.rule.severity.value.upper()}] {f.rule.id} -> {f.file_path}:{f.line_number}")
        print(f"  Title: {f.rule.title}")
        print(f"  Fix:   {f.rule.remediation}\n")

    if len(result.findings) > 5:
        print(f"... and {len(result.findings) - 5} more findings. Full audit report in output/findings.json")

    print(f"\n✅ Artifacts generated:")
    print(f"  - output/findings.json")
    print(f"  - output/blitzdev_report.sarif")

if __name__ == "__main__":
    run_scan()
