"""
BlitzDev Analyzer — Code Analysis Engine
=========================================
Inspects changed files and diffs, traces affected database entities,
and generates findings + blast radius Mermaid diagrams with 100% deterministic output.
"""
import ast
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .rules import FINTECH_RULES, Category, FinTechRule, Severity


@dataclass
class Finding:
    rule: FinTechRule
    file_path: str
    line_number: int
    line_content: str
    context: str  # surrounding lines for context


@dataclass
class AffectedEntity:
    entity_type: str  # 'route', 'model', 'service', 'middleware'
    name: str
    file_path: str
    connections: List[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    findings: List[Finding]
    affected_entities: List[AffectedEntity]
    blast_radius_mermaid: str
    files_analyzed: int
    critical_count: int
    warning_count: int
    info_count: int


class FunctionCommitVisitor(ast.NodeVisitor):
    """AST visitor to deterministically count database commit() calls per function."""

    def __init__(self):
        self.functions_with_multiple_commits: List[Tuple[str, int, int]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._check_func(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._check_func(node)
        self.generic_visit(node)

    def _check_func(self, node):
        commits = 0
        for sub_node in ast.walk(node):
            if isinstance(sub_node, ast.Call):
                func = sub_node.func
                if isinstance(func, ast.Attribute) and func.attr == "commit":
                    commits += 1
        if commits > 1:
            self.functions_with_multiple_commits.append((node.name, node.lineno, commits))


class BlitzDevAnalyzer:
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.findings: List[Finding] = []
        self.entities: List[AffectedEntity] = []
        self.files_analyzed = 0

    def analyze(self, changed_files: Optional[List[str]] = None) -> AnalysisResult:
        """Run full, deterministic analysis on the repository or changed files."""
        # Reset state for deterministic idempotency
        self.findings = []
        self.entities = []
        self.files_analyzed = 0

        files_to_scan: List[Path] = []
        if changed_files:
            for f in changed_files:
                p = (self.repo_path / f).resolve()
                if p.exists() and p.suffix == ".py":
                    files_to_scan.append(p)
        else:
            for root, dirs, files in os.walk(self.repo_path):
                # Deterministic directory skipping
                dirs[:] = sorted([d for d in dirs if d not in {".venv", "venv", ".git", "__pycache__", ".pytest_cache", "output", "bob_sessions"}])
                for file in sorted(files):
                    if file.endswith(".py"):
                        files_to_scan.append(Path(root) / file)

        # Sort files deterministically
        files_to_scan = sorted(files_to_scan)

        for file_path in files_to_scan:
            self.files_analyzed += 1
            self._scan_file(file_path)

        # Sort findings deterministically: Severity -> Rule ID -> File Path -> Line Number
        severity_order = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}
        self.findings.sort(key=lambda f: (severity_order.get(f.rule.severity, 3), f.rule.id, f.file_path, f.line_number))

        critical_count = sum(1 for f in self.findings if f.rule.severity == Severity.CRITICAL)
        warning_count = sum(1 for f in self.findings if f.rule.severity == Severity.WARNING)
        info_count = sum(1 for f in self.findings if f.rule.severity == Severity.INFO)

        mermaid = self._generate_blast_radius()

        return AnalysisResult(
            findings=self.findings,
            affected_entities=self.entities,
            blast_radius_mermaid=mermaid,
            files_analyzed=self.files_analyzed,
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
        )

    def _scan_file(self, file_path: Path) -> None:
        """Scan a single Python file using AST analysis and regex validation."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            lines = content.splitlines()
        except Exception:
            return

        self._extract_entities(file_path, content)

        try:
            rel_path = str(file_path.relative_to(self.repo_path))
        except ValueError:
            rel_path = file_path.name

        has_decimal_import = bool(
            re.search(r"^\s*(import\s+decimal|from\s+decimal\s+import)", content, re.MULTILINE)
        )

        # 1. AST Analysis for Multi-Commit Non-Atomic Transactions (FIN-003)
        try:
            tree = ast.parse(content, filename=str(file_path))
            commit_visitor = FunctionCommitVisitor()
            commit_visitor.visit(tree)
            for func_name, lineno, count in commit_visitor.functions_with_multiple_commits:
                if any(kw in func_name.lower() for kw in ["transfer", "payment", "checkout", "payout"]):
                    rule = next((r for r in FINTECH_RULES if r.id == "FIN-003"), None)
                    if rule:
                        self.findings.append(
                            Finding(
                                rule=rule,
                                file_path=rel_path,
                                line_number=lineno,
                                line_content=f"async def {func_name}(...): # {count} separate .commit() calls found",
                                context=self._get_context(lines, lineno - 1),
                            )
                        )
        except Exception:
            pass

        # 2. Rule & Pattern Analysis
        for rule in FINTECH_RULES:
            if rule.id == "FIN-003":
                continue  # Handled deterministically via AST

            elif rule.id == "FIN-007":
                # Only flag FIN-007 if financial terms exist and Decimal import is missing
                if not has_decimal_import and re.search(r"\b(balance|amount|price|total|fee)\b", content, re.IGNORECASE):
                    self.findings.append(
                        Finding(
                            rule=rule,
                            file_path=rel_path,
                            line_number=1,
                            line_content="# Missing Decimal module import",
                            context="1: " + (lines[0] if lines else ""),
                        )
                    )
            else:
                for i, line in enumerate(lines):
                    clean_line = line.strip()
                    if clean_line.startswith("#"):
                        continue  # Skip comments to prevent false positives

                    for pattern in rule.detection_patterns:
                        if re.search(pattern, line):
                            # FIN-002: Missing Row Lock refinement
                            if rule.id == "FIN-002":
                                is_balance_write_route = any(kw in content.lower() for kw in ["withdraw", "debit", "payout"])
                                if is_balance_write_route and "with_for_update" not in line:
                                    self.findings.append(
                                        Finding(
                                            rule=rule,
                                            file_path=rel_path,
                                            line_number=i + 1,
                                            line_content=clean_line,
                                            context=self._get_context(lines, i),
                                        )
                                    )
                                break
                            else:
                                self.findings.append(
                                    Finding(
                                        rule=rule,
                                        file_path=rel_path,
                                        line_number=i + 1,
                                        line_content=clean_line,
                                        context=self._get_context(lines, i),
                                    )
                                )
                                break

    def _extract_entities(self, file_path: Path, content: str) -> None:
        """Extract routes and models deterministically."""
        try:
            rel_path = str(file_path.relative_to(self.repo_path))
        except ValueError:
            rel_path = file_path.name

        seen_entities: Set[str] = {f"{e.entity_type}:{e.name}" for e in self.entities}

        # Routes: handles multi-line FastAPI decorators (@app.post, @router.get, etc.)
        route_matches = re.finditer(
            r"@\w+\.(get|post|put|delete|patch)\(\s*[\"']([^\"']+)[\"'].*?\)\s*\n\s*(?:async\s+)?def\s+(\w+)",
            content,
            re.DOTALL,
        )
        for match in route_matches:
            method = match.group(1).upper()
            path = match.group(2)
            name = f"{method} {path}"
            key = f"route:{name}"
            if key not in seen_entities:
                seen_entities.add(key)
                self.entities.append(AffectedEntity(entity_type="route", name=name, file_path=rel_path))

        # Models: class ModelName(Base):
        model_matches = re.finditer(r"class\s+(\w+)\s*\(\s*Base\s*\)\s*:", content)
        for match in model_matches:
            name = match.group(1)
            key = f"model:{name}"
            if key not in seen_entities:
                seen_entities.add(key)
                self.entities.append(AffectedEntity(entity_type="model", name=name, file_path=rel_path))

    def _generate_blast_radius(self) -> str:
        """Generate a deterministic Mermaid flowchart showing the financial blast radius."""
        routes = [e for e in self.entities if e.entity_type == "route"]
        models = [e for e in self.entities if e.entity_type == "model"]

        # Deduplicate findings by rule id for a clean, deterministic diagram
        seen_rule_ids: Set[str] = set()
        unique_findings: List[Finding] = []
        for f in self.findings:
            if f.rule.id not in seen_rule_ids:
                seen_rule_ids.add(f.rule.id)
                unique_findings.append(f)

        # Sort for deterministic output
        unique_findings.sort(key=lambda f: f.rule.id)

        mermaid = ["flowchart TD"]

        if routes:
            mermaid.append("    subgraph Routes")
            for i, r in enumerate(routes):
                mermaid.append(f'        R{i}["{r.name}"]')
            mermaid.append("    end")

        if models:
            mermaid.append("    subgraph Database")
            for i, m in enumerate(models):
                mermaid.append(f'        DB{i}[("{m.name}")]')
            mermaid.append("    end")

        # Connect routes to database tables
        if routes and models:
            for ri, _ in enumerate(routes):
                for di, _ in enumerate(models):
                    mermaid.append(f"    R{ri} --> DB{di}")

        if unique_findings:
            mermaid.append("    subgraph Missing Controls")
            for i, f in enumerate(unique_findings):
                style = (
                    "critical"
                    if f.rule.severity == Severity.CRITICAL
                    else "warning"
                    if f.rule.severity == Severity.WARNING
                    else "info"
                )
                mermaid.append(f'        M{i}["❌ [{f.rule.id}] {f.rule.title}"]:::{style}')
            mermaid.append("    end")

            # Deterministic topological linkage: Map specific rules to their affected endpoints
            keywords: Dict[str, List[str]] = {
                "FIN-002": ["withdraw", "debit"],
                "FIN-003": ["transfer"],
                "FIN-004": ["deposit", "withdraw"],
            }
            for fi, finding in enumerate(unique_findings):
                match_words = keywords.get(finding.rule.id, [])
                if match_words:
                    for ri, route in enumerate(routes):
                        if any(kw in route.name.lower() for kw in match_words):
                            mermaid.append(f"    R{ri} -.-> M{fi}")
                else:
                    # Global rules link to all routes
                    for ri in range(len(routes)):
                        mermaid.append(f"    R{ri} -.-> M{fi}")

        # Standard styles
        mermaid.append("    classDef critical fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#c62828")
        mermaid.append("    classDef warning fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#ef6c00")
        mermaid.append("    classDef info fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#1565c0")

        return "\n".join(mermaid)

    def _get_context(self, lines: List[str], line_idx: int, window: int = 3) -> str:
        """Get surrounding lines for context with line numbers."""
        start = max(0, line_idx - window)
        end = min(len(lines), line_idx + window + 1)

        context_lines = []
        for i in range(start, end):
            prefix = ">> " if i == line_idx else "   "
            context_lines.append(f"{prefix}{i+1}: {lines[i]}")

        return "\n".join(context_lines)
