import ast
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Finding:
    rule_id: str
    severity: str
    file_path: str
    line_number: int
    title: str
    description: str
    suggested_fix: str

class FinTechASTVisitor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.findings: List[Finding] = []
        self.has_decimal_import = False

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name == "decimal":
                self.has_decimal_import = True
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module == "decimal":
            self.has_decimal_import = True
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        # Inspect SQLAlchemy ORM Models for Float balances (FIN-001)
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and "balance" in target.id.lower():
                        if isinstance(stmt.value, ast.Call):
                            for arg in stmt.value.args:
                                if isinstance(arg, ast.Name) and arg.id == "Float":
                                    self.findings.append(Finding(
                                        rule_id="FIN-001",
                                        severity="HIGH",
                                        file_path=self.filename,
                                        line_number=stmt.lineno,
                                        title="Float Precision in Ledger Balance",
                                        description="Column 'balance' uses Float instead of Decimal or integer cents, leading to IEEE-754 rounding drift.",
                                        suggested_fix="Use Numeric(18, 4) or Integer (cents)."
                                    ))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._analyze_function(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._analyze_function(node)
        self.generic_visit(node)

    def _analyze_function(self, node):
        has_select_account = False
        has_row_lock = False
        commit_count = 0
        has_idempotency_validation = False
        is_transfer_or_withdraw = any(keyword in node.name.lower() for keyword in ["withdraw", "transfer", "payout"])

        for child in ast.walk(node):
            # Check for with_for_update() row lock (FIN-002)
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute) and child.func.attr == "with_for_update":
                    has_row_lock = True
                if isinstance(child.func, ast.Attribute) and child.func.attr == "commit":
                    commit_count += 1
                if isinstance(child.func, ast.Name) and child.func.id == "select":
                    has_select_account = True

            # Check if idempotency_key is queried against DB (FIN-004)
            if isinstance(child, ast.Attribute) and child.attr == "idempotency_key":
                has_idempotency_validation = True

        # FIN-002: Missing Row Lock on Withdraw
        if is_transfer_or_withdraw and has_select_account and not has_row_lock:
            self.findings.append(Finding(
                rule_id="FIN-002",
                severity="CRITICAL",
                file_path=self.filename,
                line_number=node.lineno,
                title="Missing Row-Level Lock on Mutable Balance",
                description=f"Function '{node.name}' reads account balance without with_for_update(). Vulnerable to concurrent race-condition overdrafts.",
                suggested_fix="Append .with_for_update() to the select statement."
            ))

        # FIN-003: Non-Atomic Dual Commit
        if commit_count > 1:
            self.findings.append(Finding(
                rule_id="FIN-003",
                severity="CRITICAL",
                file_path=self.filename,
                line_number=node.lineno,
                title="Non-Atomic Dual-Commit Ledger Operation",
                description=f"Function '{node.name}' commits transactions {commit_count} times. Partial failures will leave ledger in an inconsistent state.",
                suggested_fix="Consolidate all ledger stage updates into a single atomic commit or context manager transaction."
            ))

def scan_file(filepath: str) -> List[Finding]:
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source, filename=filepath)
    visitor = FinTechASTVisitor(filepath)
    visitor.visit(tree)
    return visitor.findings
