import sys
import json
from pathlib import Path
from blitzdev_agent.analyzer import BlitzDevAnalyzer
from blitzdev_agent.formatter import PRCommentFormatter

def run():
    repo_path = Path(".").resolve()
    analyzer = BlitzDevAnalyzer(str(repo_path))
    result = analyzer.analyze()

    print(f"\n🛡️ BlitzDev Scan Complete: {result.files_analyzed} files analyzed.")
    print(f"   🔴 Critical: {result.critical_count}")
    print(f"   ⚠️  Warnings: {result.warning_count}")
    print(f"   ℹ️  Info:     {result.info_count}\n")

    # Ensure output directory exists
    output_dir = repo_path / "output"
    output_dir.mkdir(exist_ok=True)

    # Write formatted Markdown
    formatter = PRCommentFormatter()
    report_md = formatter.format(result)
    (output_dir / "audit_report.md").write_text(report_md, encoding="utf-8")
    print("✅ Generated: output/audit_report.md")

if __name__ == "__main__":
    run()
