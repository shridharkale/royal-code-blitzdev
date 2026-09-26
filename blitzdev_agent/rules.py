"""
FinTech Validator Mode — Rule Definitions
==========================================
Deterministic rule definitions for financial transactional integrity.
Covers IEEE 754 precision, concurrency race conditions, atomicity,
and idempotency boundaries.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List

class Severity(Enum):
    CRITICAL = "critical"   # 🔴
    WARNING = "warning"     # ⚠️
    INFO = "info"           # ℹ️

class Category(Enum):
    CURRENCY_PRECISION = "currency_precision"
    ACID_ROLLBACK = "acid_rollback"
    CONCURRENCY = "concurrency"
    IDEMPOTENCY = "idempotency"
    AUTH = "auth"

@dataclass(frozen=True)
class FinTechRule:
    id: str
    title: str
    severity: Severity
    category: Category
    description: str
    detection_patterns: List[str]
    remediation: str
    references: List[str] = field(default_factory=list)

FINTECH_RULES: List[FinTechRule] = [
    FinTechRule(
        id="FIN-001",
        title="Float Currency Precision Drift",
        severity=Severity.CRITICAL,
        category=Category.CURRENCY_PRECISION,
        description="Using IEEE 754 float types for money fields can lead to precision loss and fractional-cent drift.",
        detection_patterns=[
            r"(?i)(balance|amount|price|total|fee)\s*:\s*float",
            r"(?i)(balance|amount|price|total|fee)\s*=\s*\d+\.\d+(?!\s*M|\s*D|\s*Decimal)"
        ],
        remediation="Enforce decimal.Decimal or integer cents with explicit quantization.",
        references=["CWE-682", "OASIS SARIF v2.1.0"]
    ),
    FinTechRule(
        id="FIN-002",
        title="Missing Row-Level Concurrency Lock",
        severity=Severity.CRITICAL,
        category=Category.CONCURRENCY,
        description="Missing serialized mutex locks or SELECT FOR UPDATE during concurrent balance updates.",
        detection_patterns=[
            r"db\.query\(.*Account.*\).*filter\(.*(?:id|account_id).*\)\.first\(\)",
            r"select\(Account\)\.where\(",
            r"select\(.*\)\.filter_by\("
        ],
        remediation="Acquire an asynchronous mutex lock or use with_for_update() on balance reads.",
        references=["CWE-362", "ACID Isolation"]
    ),
    FinTechRule(
        id="FIN-003",
        title="Non-Atomic Multi-Commit Transaction",
        severity=Severity.CRITICAL,
        category=Category.ACID_ROLLBACK,
        description="Multiple commit() calls inside transfer functions risk partial ledger execution on failure.",
        detection_patterns=[],
        remediation="Wrap all ledger balance updates into a single atomic transaction block.",
        references=["CWE-662", "ACID Atomicity"]
    ),
    FinTechRule(
        id="FIN-004",
        title="Unvalidated Idempotency Key",
        severity=Severity.WARNING,
        category=Category.IDEMPOTENCY,
        description="Accepting an idempotency_key without verifying previous execution allows double-charging on network retry.",
        detection_patterns=[r"idempotency_key(?!\s*.*?query\()"],
        remediation="Query database for key existence inside transaction boundary before mutating balances.",
        references=["IETF Idempotency-Key-Spec"]
    ),
    FinTechRule(
        id="FIN-005",
        title="Missing Authentication Dependency",
        severity=Severity.WARNING,
        category=Category.AUTH,
        description="Financial ledger mutation endpoints declared without Depends() security guards.",
        detection_patterns=[r"@app\.(get|post|put|delete|patch)\((?!.*Depends)"],
        remediation="Add authentication guards such as Depends(get_current_user) to all routes.",
        references=["OWASP API1:2023"]
    ),
    FinTechRule(
        id="FIN-006",
        title="Missing Rollback Exception Guard",
        severity=Severity.WARNING,
        category=Category.ACID_ROLLBACK,
        description="Database session operations without explicit await session.rollback() on exception.",
        detection_patterns=[r"except\s*(?:Exception(?:\s+as\s+\w+)?)?:(?!.*\s*rollback\(\))"],
        remediation="Include explicit await session.rollback() inside exception handling blocks.",
        references=["CWE-755"]
    ),
    FinTechRule(
        id="FIN-007",
        title="Missing Decimal Module Import",
        severity=Severity.INFO,
        category=Category.CURRENCY_PRECISION,
        description="Financial arithmetic detected in module without explicit decimal.Decimal import.",
        detection_patterns=[],
        remediation="Import and use decimal.Decimal for all monetary calculations.",
        references=["PEP 327"]
    )
]

def get_rules_by_severity(severity: Severity) -> List[FinTechRule]:
    return [rule for rule in FINTECH_RULES if rule.severity == severity]

def get_rules_by_category(category: Category) -> List[FinTechRule]:
    return [rule for rule in FINTECH_RULES if rule.category == category]
