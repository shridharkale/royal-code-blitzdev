# BlitzDev Agent: FinTech Validator Mode

## Overview
**BlitzDev** is an AI-powered code review engine acting as a FinTech-Aware PR Guardian, powered by IBM Bob 2.0. It automatically scans Pull Requests for domain-specific financial risks, generates visual impact diagrams, and automatically crafts exploit tests to prove vulnerabilities.

**Purpose**: To prevent critical financial logic bugs (race conditions, precision errors, atomic transfer failures) from reaching production.
**Trigger Conditions**: Triggered on every Pull Request opened or updated in repositories tagged with the `fintech` domain.

## Rule Definitions

The FinTech Validator Mode implements 7 core rules:

| ID | Title | Severity | Description |
|---|---|---|---|
| **FIN-001** | Float Currency | 🔴 CRITICAL | Detects float type hints or assignments for money fields (balance, amount, price, total, fee). |
| **FIN-002** | Missing Row Lock | 🔴 CRITICAL | Detects withdraw/debit patterns without `FOR UPDATE` or `with_for_update()`. |
| **FIN-003** | Non-Atomic Transfer | 🔴 CRITICAL | Detects multiple `commit()` calls within a single function that handles transfers. |
| **FIN-004** | Missing Idempotency Check | ⚠️ WARNING | Detects endpoints accepting `idempotency_key` but not querying for existing keys. |
| **FIN-005** | Missing Auth Middleware | ⚠️ WARNING | Detects route definitions without `Depends()` for authentication. |
| **FIN-006** | Bare Exception Handler | ⚠️ WARNING | Detects bare `except:` or `except Exception` without proper rollback in financial endpoints. |
| **FIN-007** | Missing Decimal Import | ℹ️ INFO | Detects financial calculations in files that don't import `decimal.Decimal`. |

## Analysis Pipeline

1. **Scan**: Traces affected database entities and extracts code elements (routes, models).
2. **Analyze**: Runs regex-based static analysis against the `FINTECH_RULES` dataset.
3. **Diagram**: Generates a Mermaid flowchart illustrating the "Blast Radius" of the detected flaws.
4. **Format**: Converts the findings into a rich, structured GitHub PR Markdown comment.
5. **Test-Gen**: Emits runnable `pytest-asyncio` exploit scripts tailored to the found vulnerabilities (e.g. firing 10 concurrent requests to test missing row locks).

## IBM Bob 2.0 Integration

- **Custom Modes**: Runs as a specialized "Validator Mode" tailored to FinTech repositories.
- **Subagents**: Spawns test-generation subagents via IBM Bob's multi-agent runtime to write exploits.
- **Skills**: Plugs into Bob's GitHub PR review hooks, leaving inline comments and automated blocking reviews.

## Example Output Snippet

```markdown
## 🛡️ BlitzDev — FinTech PR Guardian Report
**Scan Summary**: 15 files analyzed, 2 critical, 1 warnings, 0 info.

### 🔴 Critical Financial Risks
**[FIN-002] Missing Row Lock**
- **Location**: `api/routes.py` at line 45
- **Impact**: Missing 'FOR UPDATE' or 'with_for_update' in withdraw/debit patterns.
- **Remediation**: Use with_for_update() in SQLAlchemy when querying balances to update.
```
