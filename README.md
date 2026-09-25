# 🛡️ BlitzDev: FinTech Transactional Security & ACID Compliance Engine

An enterprise-grade FinTech vulnerability scanner and automated remediation agent built for **IBM Bob IDE**. BlitzDev inspects financial ledger APIs, flags ACID violations and concurrency flaws, visualizes the financial blast radius, and synthesizes verifiable remediations.

---

## 🎯 Domain Vulnerability Coverage

| Rule ID | Severity | Description | Remediated Status |
| :--- | :--- | :--- | :--- |
| **FIN-001** | High | IEEE-754 Floating-Point Currency Drift | Fixed (Quantized precision / Numeric) |
| **FIN-002** | Critical | Missing Row-Level Locks / Race Conditions | Fixed (Serialized mutex locks / with_for_update) |
| **FIN-003** | Critical | Non-Atomic Multi-Commit Ledger Mutations | Fixed (Consolidated atomic transaction) |
| **FIN-004** | High | Unchecked Idempotency Key Injection | Fixed (Idempotency ledger verification) |
| **FIN-005** | Medium | Missing Authentication Dependencies | Flagged |
| **FIN-006** | Medium | Incomplete Rollback Exception Handlers | Fixed (Explicit transaction rollback) |
| **FIN-007** | High | Implicit Floating-Point Primitives | Fixed (Decimal module imports) |

---

## 🧪 Deterministic Concurrency Verification

BlitzDev includes executable pytest-asyncio verification suites proving both the vulnerability and its remediation:

### 1. Flawed Ledger (tests/test_concurrency_exploit.py)
Fires 5 simultaneous $30.00 withdrawal requests against an initial balance of $100.00 without row locks:
* **Result:** All 5 requests succeed (HTTP 200), resulting in an illegal balance state (FIN-002 Confirmed).

### 2. Remediated Ledger (tests/test_concurrency_remediated.py)
Fires the same 5 concurrent requests after applying BlitzDev serialized row-locking remediation:
* **Result:** Exactly 3 requests succeed ($90.00 total debit), 2 are safely rejected (HTTP 400 Insufficient Funds), leaving the ledger balance at an exact, positive $10.00.

---

## 🚀 Reproduction Quickstart

```bash
# 1. Clone and install dependencies
git clone https://github.com/shridharkale/royal-code-blitzdev.git
cd royal-code-blitzdev
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Seed deterministic ledger database
python3 -m demo_api.seed

# 3. Run the vulnerability exploit test
python3 -m pytest -s tests/test_concurrency_exploit.py

# 4. Run the remediated concurrency test
python3 -m pytest -s tests/test_concurrency_remediated.py

# 5. Run AST Static Scanner
python3 -m blitzdev_agent.scanner
```

---

## 📑 Generated Artifacts
* **Audit Report:** output/audit_report.md
* **SARIF Export (OASIS v2.1.0):** output/blitzdev_report.sarif
