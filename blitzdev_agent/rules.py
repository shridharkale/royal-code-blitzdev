"""
FinTech Validator Mode — Rule Definitions
==========================================
These rules define the financial-domain checks that BlitzDev performs
on every pull request. Each rule has an ID, severity, category,
pattern to detect, and recommended remediation.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List
import re

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

@dataclass
class FinTechRule:
    id: str
    title: str
    severity: Severity
    category: Category
    description: str
    detection_patterns: List[str]  # regex patterns
    remediation: str
    references: List[str] = field(default_factory=list)

FINTECH_RULES: List[FinTechRule] = [
    FinTechRule(
        id="FIN-001",
        title="Float Currency",
        severity=Severity.CRITICAL,
        category=Category.CURRENCY_PRECISION,
        description="Using float for money fields (balance, amount, price, total, fee) can lead to precision errors.",
        detection_patterns=[r"(?i)(balance|amount|price|total|fee)\s*:\s*float", r"(?i)(balance|amount|price|total|fee)\s*=\s*\d+\.\d+(?!\s*M|\s*D|\s*Decimal)"],
        remediation="Use decimal.Decimal for all monetary values.",
    ),
    FinTechRule(
        id="FIN-002",
        title="Missing Row Lock",
        severity=Severity.CRITICAL,
        category=Category.CONCURRENCY,
        description="Missing 'FOR UPDATE' or 'with_for_update' in withdraw/debit patterns.",
        detection_patterns=[
            r"db\.query\(.*Account.*\).*filter\(.*(?:id|account_id).*\)\.first\(\)",
            r"select\(Account\)\.where\(",
            r"select\(.*\)\.filter_by\(",
        ],
        remediation="Use with_for_update() in SQLAlchemy when querying balances to update.",
    ),
    FinTechRule(
        id="FIN-003",
        title="Non-Atomic Transfer",
        severity=Severity.CRITICAL,
        category=Category.ACID_ROLLBACK,
        description="Multiple commit() calls within a single function that handles transfers.",
        detection_patterns=[], # Analyzed via full file string in analyzer
        remediation="Use a single database transaction and commit only once.",
    ),
    FinTechRule(
        id="FIN-004",
        title="Missing Idempotency Check",
        severity=Severity.WARNING,
        category=Category.IDEMPOTENCY,
        description="Endpoints accepting idempotency_key but not querying for existing keys.",
        detection_patterns=[r"idempotency_key(?!\s*.*?query\()"],
        remediation="Check the database for the idempotency_key before processing the request.",
    ),
    FinTechRule(
        id="FIN-005",
        title="Missing Auth Middleware",
        severity=Severity.WARNING,
        category=Category.AUTH,
        description="Route definitions without Depends() for auth.",
        detection_patterns=[r"@app\.(get|post|put|delete|patch)\((?!.*Depends)"],
        remediation="Add authentication dependencies like Depends(get_current_user) to your routes.",
    ),
    FinTechRule(
        id="FIN-006",
        title="Bare Exception Handler",
        severity=Severity.WARNING,
        category=Category.ACID_ROLLBACK,
        description="Bare 'except:' or 'except Exception' without proper rollback in financial endpoints.",
        detection_patterns=[r"except\s*(?:Exception(?:\s+as\s+\w+)?)?:(?!.*\s*rollback\(\))"],
        remediation="Catch specific exceptions and ensure session.rollback() is called on failure.",
    ),
    FinTechRule(
        id="FIN-007",
        title="Missing Decimal Import",
        severity=Severity.INFO,
        category=Category.CURRENCY_PRECISION,
        description="Financial calculations in files that don't import decimal.Decimal.",
        detection_patterns=[], # Analyzed manually
        remediation="Import and use decimal.Decimal.",
    )
]

def get_rules_by_severity(severity: Severity) -> List[FinTechRule]:
    return [rule for rule in FINTECH_RULES if rule.severity == severity]

def get_rules_by_category(category: Category) -> List[FinTechRule]:
    return [rule for rule in FINTECH_RULES if rule.category == category]
