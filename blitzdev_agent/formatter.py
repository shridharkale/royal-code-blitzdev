"""
BlitzDev Formatter — GitHub PR Comment Generator
=================================================
Transforms analysis findings into a structured GitHub PR Markdown comment.
"""
from .analyzer import AnalysisResult, Finding
from .rules import Severity
from datetime import datetime, timezone

class PRCommentFormatter:
    def format(self, result: AnalysisResult, pr_url: str = "") -> str:
        """Generate full PR comment markdown."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        md = [
            "## 🛡️ BlitzDev — FinTech PR Guardian Report",
            f"**Scan Summary**: {result.files_analyzed} files analyzed, {result.critical_count} critical, {result.warning_count} warnings, {result.info_count} info.",
            ""
        ]
        
        critical_findings = [f for f in result.findings if f.rule.severity == Severity.CRITICAL]
        if critical_findings:
            md.append("### 🔴 Critical Financial Risks")
            for f in critical_findings:
                md.append(f"**[{f.rule.id}] {f.rule.title}**")
                md.append(f"- **Location**: `{f.file_path}` at line {f.line_number}")
                md.append(f"- **Impact**: {f.rule.description}")
                md.append(f"- **Remediation**: {f.rule.remediation}")
                md.append("```python")
                md.append(f.context)
                md.append("```")
                md.append("")
                
        warning_findings = [f for f in result.findings if f.rule.severity == Severity.WARNING]
        if warning_findings:
            md.append("### ⚠️ Warnings & Missing Controls")
            for f in warning_findings:
                md.append(f"**[{f.rule.id}] {f.rule.title}**")
                md.append(f"- **Location**: `{f.file_path}` at line {f.line_number}")
                md.append(f"- **Impact**: {f.rule.description}")
                md.append(f"- **Remediation**: {f.rule.remediation}")
                md.append("```python")
                md.append(f.context)
                md.append("```")
                md.append("")
        
        info_findings = [f for f in result.findings if f.rule.severity == Severity.INFO]
        if info_findings:
            md.append("### ℹ️ Info")
            for f in info_findings:
                md.append(f"**[{f.rule.id}] {f.rule.title}**")
                md.append(f"- **Location**: `{f.file_path}` at line {f.line_number}")
                md.append("")
                
        md.append("### 📊 Financial Blast Radius Diagram")
        md.append("```mermaid")
        md.append(result.blast_radius_mermaid)
        md.append("```")
        md.append("")
        
        md.append("### 💡 Concrete Remediations")
        md.append("1. **Use `decimal.Decimal`**: Convert all float currency values to `Decimal` types.")
        md.append("2. **Add `with_for_update()`**: When deducting balances, lock the row to prevent race conditions.")
        md.append("3. **Atomic Transactions**: Ensure all database operations in a financial transaction commit together.")
        md.append("")
        md.append("---")
        md.append(f"_Powered by BlitzDev + IBM Bob 2.0 | Scanned at {timestamp}_")
        
        return "\n".join(md)
