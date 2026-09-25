---
name: sarif-exporter
description: Translates FinTech code review findings into OASIS standard SARIF v2.1.0 format for automated ingestion into GitHub Advanced Security, CI/CD pipelines, and enterprise security dashboards.
---

# 🛡️ SARIF Exporter Skill

This skill formats AST and static analysis findings into standard **SARIF (Static Analysis Results Interchange Format) v2.1.0** JSON.

## 📋 Schema Compliance
The generated output satisfies:
- **Schema**: `https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json`
- **Driver Name**: `BlitzDev FinTech Validator`
- **Severity Mapping**:
  - `Severity.CRITICAL` $\rightarrow$ Level `error` (Security Severity `8.5`)
  - `Severity.WARNING` $\rightarrow$ Level `warning` (Security Severity `5.0`)
  - `Severity.INFO` $\rightarrow$ Level `note` (Security Severity `2.0`)

## 📤 Output Location
Emits to `output/blitzdev_report.sarif` for direct upload via GitHub Action (`github/codeql-action/upload-sarif@v3`).
