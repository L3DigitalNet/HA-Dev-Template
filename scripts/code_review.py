#!/usr/bin/env python3
"""
Automated Code Review Script for Home Assistant Integrations.

This script performs comprehensive code review checks including:
- Security vulnerability scanning
- Code quality assessment
- Home Assistant pattern compliance
- Test coverage analysis
- Documentation completeness

Usage:
    python scripts/code_review.py [--files FILE1 FILE2...] [--full] [--json]
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Severity(Enum):
    """Issue severity levels."""

    BLOCKING = "blocking"  # Must fix before merge
    WARNING = "warning"  # Should fix
    NITPICK = "nitpick"  # Optional improvement


class Category(Enum):
    """Issue categories."""

    SECURITY = "security"
    QUALITY = "quality"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ASYNC = "async"
    PATTERN = "pattern"


@dataclass
class Issue:
    """Represents a code review issue."""

    severity: Severity
    category: Category
    file: str
    line: int | None
    title: str
    description: str
    suggestion: str | None = None
    code_example: str | None = None
    reference: str | None = None


@dataclass
class ReviewResult:
    """Results of code review."""

    blocking: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    nitpicks: list[Issue] = field(default_factory=list)
    positives: list[str] = field(default_factory=list)
    coverage_percent: float = 0.0
    quality_tier: str = "Unknown"
    files_reviewed: int = 0

    def add_issue(self, issue: Issue) -> None:
        """Add an issue to the appropriate list."""
        if issue.severity == Severity.BLOCKING:
            self.blocking.append(issue)
        elif issue.severity == Severity.WARNING:
            self.warnings.append(issue)
        else:
            self.nitpicks.append(issue)

    def has_blocking_issues(self) -> bool:
        """Check if there are blocking issues."""
        return len(self.blocking) > 0

    def total_issues(self) -> int:
        """Total number of issues found."""
        return len(self.blocking) + len(self.warnings) + len(self.nitpicks)


class CodeReviewer:
    """Automated code reviewer for Home Assistant integrations."""

    def __init__(self, root_path: Path):
        """Initialize the code reviewer."""
        self.root_path = root_path
        self.result = ReviewResult()

        # Security patterns to detect
        self.security_patterns = {
            "hardcoded_key": re.compile(
                r'(?:api[_-]?key|password|secret|token)\s*=\s*["\'][\w\-]+["\']',
                re.IGNORECASE,
            ),
            "sql_injection": re.compile(
                r'(?:execute|executemany|query)\s*\(\s*["\'].*?\{|\%',
                re.IGNORECASE,
            ),
            "eval_usage": re.compile(r"\beval\s*\("),
            "pickle_usage": re.compile(r"\bpickle\s*\."),
            "requests_in_async": re.compile(r"requests\s*\.(?:get|post|put|delete)"),
            "shell_injection": re.compile(r"subprocess\s*\.\s*(?:call|run|Popen).*shell\s*=\s*True"),
        }

        # HA anti-patterns
        self.ha_patterns = {
            "blocking_sleep": re.compile(r"time\.sleep\s*\("),
            "missing_async": re.compile(r"def\s+(?!__)[\w]+.*:\s*\n.*(?:requests|urllib)"),
            "no_unique_id": re.compile(r"class\s+\w+.*Entity.*:\s*(?:.*\n)*?(?!.*unique_id)"),
        }

    def review_files(self, files: list[Path]) -> ReviewResult:
        """Review the specified files."""
        self.result.files_reviewed = len(files)

        for file in files:
            if file.suffix == ".py":
                self._review_python_file(file)
            elif file.name == "manifest.json":
                self._review_manifest(file)
            elif file.name == "strings.json":
                self._review_strings(file)

        # Run automated checks
        self._run_linter()
        self._run_type_checker()
        self._check_test_coverage()

        # Assess quality tier
        self._assess_quality_tier()

        return self.result

    def _review_python_file(self, file: Path) -> None:
        """Review a Python file for issues."""
        try:
            content = file.read_text()
            lines = content.split("\n")

            # Security checks
            self._check_security_issues(file, content, lines)

            # HA pattern checks
            self._check_ha_patterns(file, content, lines)

            # AST-based checks
            try:
                tree = ast.parse(content)
                self._check_ast_patterns(file, tree, lines)
            except SyntaxError as e:
                self.result.add_issue(
                    Issue(
                        severity=Severity.BLOCKING,
                        category=Category.QUALITY,
                        file=str(file),
                        line=e.lineno,
                        title="Syntax Error",
                        description=f"Python syntax error: {e.msg}",
                    )
                )

        except Exception as e:
            print(f"Error reviewing {file}: {e}", file=sys.stderr)

    def _check_security_issues(
        self, file: Path, content: str, lines: list[str]
    ) -> None:
        """Check for security vulnerabilities."""
        # Hardcoded credentials
        for i, line in enumerate(lines, 1):
            if self.security_patterns["hardcoded_key"].search(line):
                # Check if it's not in a test file or comment
                if "test" not in str(file).lower() and not line.strip().startswith("#"):
                    self.result.add_issue(
                        Issue(
                            severity=Severity.BLOCKING,
                            category=Category.SECURITY,
                            file=str(file),
                            line=i,
                            title="Hardcoded Credential",
                            description="Hardcoded API key, password, or secret detected",
                            suggestion="Store credentials in config entry data",
                            code_example='api_key = entry.data[CONF_API_KEY]',
                            reference="https://developers.home-assistant.io/docs/config_entries_config_flow_handler",
                        )
                    )

        # SQL injection
        if self.security_patterns["sql_injection"].search(content):
            self.result.add_issue(
                Issue(
                    severity=Severity.BLOCKING,
                    category=Category.SECURITY,
                    file=str(file),
                    line=None,
                    title="Potential SQL Injection",
                    description="SQL query using string formatting detected",
                    suggestion="Use parameterized queries",
                    code_example='cursor.execute("SELECT * FROM t WHERE id = ?", (id,))',
                )
            )

        # eval() usage
        if self.security_patterns["eval_usage"].search(content):
            self.result.add_issue(
                Issue(
                    severity=Severity.BLOCKING,
                    category=Category.SECURITY,
                    file=str(file),
                    line=None,
                    title="Unsafe eval() Usage",
                    description="Use of eval() detected - potential code injection",
                    suggestion="Use ast.literal_eval() or json.loads() instead",
                )
            )

        # Shell injection
        if self.security_patterns["shell_injection"].search(content):
            self.result.add_issue(
                Issue(
                    severity=Severity.BLOCKING,
                    category=Category.SECURITY,
                    file=str(file),
                    line=None,
                    title="Shell Injection Risk",
                    description="subprocess call with shell=True detected",
                    suggestion="Use shell=False and pass command as list",
                    code_example='subprocess.run(["ls", "-la"], shell=False)',
                )
            )

    def _check_ha_patterns(self, file: Path, content: str, lines: list[str]) -> None:
        """Check for Home Assistant pattern violations."""
        # Blocking calls in async code
        if "async def" in content and self.security_patterns["requests_in_async"].search(
            content
        ):
            self.result.add_issue(
                Issue(
                    severity=Severity.BLOCKING,
                    category=Category.ASYNC,
                    file=str(file),
                    line=None,
                    title="Blocking I/O in Async Function",
                    description="Using requests library in async function blocks event loop",
                    suggestion="Use aiohttp for async HTTP requests",
                    code_example="""async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        return await response.json()""",
                    reference="https://developers.home-assistant.io/docs/asyncio_working_with_async",
                )
            )

        # time.sleep in async code
        if "async def" in content and self.ha_patterns["blocking_sleep"].search(content):
            self.result.add_issue(
                Issue(
                    severity=Severity.BLOCKING,
                    category=Category.ASYNC,
                    file=str(file),
                    line=None,
                    title="Blocking Sleep in Async Function",
                    description="Using time.sleep() in async function blocks event loop",
                    suggestion="Use asyncio.sleep() instead",
                    code_example="await asyncio.sleep(seconds)",
                )
            )

    def _check_ast_patterns(self, file: Path, tree: ast.AST, lines: list[str]) -> None:
        """Check patterns using AST analysis."""
        for node in ast.walk(tree):
            # Check for missing type hints
            if isinstance(node, ast.FunctionDef):
                if node.returns is None and not node.name.startswith("_"):
                    self.result.add_issue(
                        Issue(
                            severity=Severity.WARNING,
                            category=Category.QUALITY,
                            file=str(file),
                            line=node.lineno,
                            title="Missing Return Type Hint",
                            description=f"Function '{node.name}' has no return type hint",
                            suggestion="Add type hints to all public functions",
                        )
                    )

            # Check for broad exception catching
            if isinstance(node, ast.ExceptHandler):
                if node.type is None or (
                    isinstance(node.type, ast.Name) and node.type.id == "Exception"
                ):
                    self.result.add_issue(
                        Issue(
                            severity=Severity.WARNING,
                            category=Category.QUALITY,
                            file=str(file),
                            line=node.lineno,
                            title="Broad Exception Catching",
                            description="Catching generic Exception or all exceptions",
                            suggestion="Catch specific exceptions when possible",
                        )
                    )

    def _review_manifest(self, file: Path) -> None:
        """Review manifest.json for completeness."""
        try:
            manifest = json.loads(file.read_text())

            required_fields = [
                "domain",
                "name",
                "version",
                "codeowners",
                "documentation",
                "iot_class",
                "integration_type",
            ]

            for field in required_fields:
                if field not in manifest:
                    self.result.add_issue(
                        Issue(
                            severity=Severity.BLOCKING,
                            category=Category.QUALITY,
                            file=str(file),
                            line=None,
                            title=f"Missing Required Field: {field}",
                            description=f"manifest.json must include '{field}'",
                            reference="https://developers.home-assistant.io/docs/creating_integration_manifest",
                        )
                    )

            # Check for config_flow
            if not manifest.get("config_flow", False):
                self.result.add_issue(
                    Issue(
                        severity=Severity.WARNING,
                        category=Category.PATTERN,
                        file=str(file),
                        line=None,
                        title="Config Flow Not Enabled",
                        description="New integrations should use config flow",
                        suggestion="Set 'config_flow: true' and implement config_flow.py",
                    )
                )

        except json.JSONDecodeError as e:
            self.result.add_issue(
                Issue(
                    severity=Severity.BLOCKING,
                    category=Category.QUALITY,
                    file=str(file),
                    line=None,
                    title="Invalid JSON",
                    description=f"manifest.json has invalid JSON: {e}",
                )
            )

    def _review_strings(self, file: Path) -> None:
        """Review strings.json for completeness."""
        try:
            json.loads(file.read_text())
            self.result.positives.append("✅ strings.json is valid JSON")
        except json.JSONDecodeError as e:
            self.result.add_issue(
                Issue(
                    severity=Severity.BLOCKING,
                    category=Category.QUALITY,
                    file=str(file),
                    line=None,
                    title="Invalid JSON",
                    description=f"strings.json has invalid JSON: {e}",
                )
            )

    def _run_linter(self) -> None:
        """Run Ruff linter and capture results."""
        try:
            result = subprocess.run(
                ["ruff", "check", "custom_components/", "--quiet"],
                capture_output=True,
                text=True,
                cwd=self.root_path,
            )

            if result.returncode == 0:
                self.result.positives.append("✅ Ruff linter passes with no errors")
            else:
                self.result.add_issue(
                    Issue(
                        severity=Severity.WARNING,
                        category=Category.QUALITY,
                        file="multiple",
                        line=None,
                        title="Linting Errors",
                        description="Ruff linter found issues",
                        suggestion="Run: ruff check custom_components/ --fix",
                    )
                )
        except FileNotFoundError:
            print("Warning: Ruff not found, skipping lint check", file=sys.stderr)

    def _run_type_checker(self) -> None:
        """Run mypy type checker and capture results."""
        try:
            result = subprocess.run(
                ["mypy", "custom_components/"],
                capture_output=True,
                text=True,
                cwd=self.root_path,
            )

            if result.returncode == 0:
                self.result.positives.append("✅ Type checking passes with no errors")
            else:
                # Count errors
                error_count = len(
                    [line for line in result.stdout.split("\n") if "error:" in line]
                )
                if error_count > 0:
                    self.result.add_issue(
                        Issue(
                            severity=Severity.WARNING,
                            category=Category.QUALITY,
                            file="multiple",
                            line=None,
                            title=f"Type Check Errors ({error_count})",
                            description="mypy found type checking issues",
                            suggestion="Run: mypy custom_components/",
                        )
                    )
        except FileNotFoundError:
            print("Warning: mypy not found, skipping type check", file=sys.stderr)

    def _check_test_coverage(self) -> None:
        """Check test coverage."""
        try:
            result = subprocess.run(
                [
                    "pytest",
                    "tests/",
                    "--cov=custom_components",
                    "--cov-report=json",
                    "--quiet",
                ],
                capture_output=True,
                text=True,
                cwd=self.root_path,
            )

            # Try to read coverage report
            coverage_file = self.root_path / "coverage.json"
            if coverage_file.exists():
                coverage_data = json.loads(coverage_file.read_text())
                self.result.coverage_percent = coverage_data["totals"]["percent_covered"]

                if self.result.coverage_percent >= 80:
                    self.result.positives.append(
                        f"✅ Excellent test coverage: {self.result.coverage_percent:.1f}%"
                    )
                elif self.result.coverage_percent >= 60:
                    self.result.add_issue(
                        Issue(
                            severity=Severity.WARNING,
                            category=Category.TESTING,
                            file="tests/",
                            line=None,
                            title="Test Coverage Below Target",
                            description=f"Coverage is {self.result.coverage_percent:.1f}%, target is 80%",
                            suggestion="Add tests for uncovered code paths",
                        )
                    )
                else:
                    self.result.add_issue(
                        Issue(
                            severity=Severity.BLOCKING,
                            category=Category.TESTING,
                            file="tests/",
                            line=None,
                            title="Insufficient Test Coverage",
                            description=f"Coverage is {self.result.coverage_percent:.1f}%, minimum is 60%",
                            suggestion="Add comprehensive tests for new functionality",
                        )
                    )

        except Exception as e:
            print(f"Warning: Could not check test coverage: {e}", file=sys.stderr)

    def _assess_quality_tier(self) -> None:
        """Assess the integration quality tier."""
        # Simple heuristic based on common requirements
        has_config_flow = (self.root_path / "custom_components").glob("*/config_flow.py")
        has_tests = (self.root_path / "tests").exists()

        if self.result.has_blocking_issues():
            self.result.quality_tier = "Below Bronze"
        elif not has_tests or self.result.coverage_percent < 60:
            self.result.quality_tier = "Bronze (needs testing)"
        elif self.result.coverage_percent >= 80 and len(self.result.warnings) == 0:
            self.result.quality_tier = "Gold"
        elif self.result.coverage_percent >= 60:
            self.result.quality_tier = "Silver"
        else:
            self.result.quality_tier = "Bronze"


def format_output(result: ReviewResult, format_type: str = "text") -> str:
    """Format review results for output."""
    if format_type == "json":
        return json.dumps(
            {
                "blocking": [
                    {
                        "severity": i.severity.value,
                        "category": i.category.value,
                        "file": i.file,
                        "line": i.line,
                        "title": i.title,
                        "description": i.description,
                    }
                    for i in result.blocking
                ],
                "warnings": [
                    {
                        "severity": i.severity.value,
                        "category": i.category.value,
                        "file": i.file,
                        "line": i.line,
                        "title": i.title,
                        "description": i.description,
                    }
                    for i in result.warnings
                ],
                "nitpicks": [
                    {
                        "severity": i.severity.value,
                        "category": i.category.value,
                        "file": i.file,
                        "line": i.line,
                        "title": i.title,
                        "description": i.description,
                    }
                    for i in result.nitpicks
                ],
                "quality_tier": result.quality_tier,
                "coverage": result.coverage_percent,
            },
            indent=2,
        )

    # Text format
    output = []
    output.append("=" * 80)
    output.append("🤖 AUTOMATED CODE REVIEW")
    output.append("=" * 80)
    output.append("")

    # Overall assessment
    if result.has_blocking_issues():
        output.append("**Overall**: 🚫 CHANGES REQUESTED")
    elif len(result.warnings) > 0:
        output.append("**Overall**: ⚠️  COMMENTS")
    else:
        output.append("**Overall**: ✅ APPROVED")

    output.append(f"**Quality Tier**: {result.quality_tier}")
    output.append(f"**Files Reviewed**: {result.files_reviewed}")
    output.append(f"**Coverage**: {result.coverage_percent:.1f}%")
    output.append("")

    # Blocking issues
    if result.blocking:
        output.append(f"🚫 BLOCKING ISSUES ({len(result.blocking)})")
        output.append("-" * 80)
        for i, issue in enumerate(result.blocking, 1):
            output.append(f"\n{i}. **{issue.title}**")
            output.append(f"   File: {issue.file}")
            if issue.line:
                output.append(f"   Line: {issue.line}")
            output.append(f"   Category: {issue.category.value}")
            output.append(f"   {issue.description}")
            if issue.suggestion:
                output.append(f"   Suggestion: {issue.suggestion}")
            if issue.code_example:
                output.append(f"   Example:\n   {issue.code_example}")
        output.append("")

    # Warnings
    if result.warnings:
        output.append(f"⚠️  RECOMMENDED CHANGES ({len(result.warnings)})")
        output.append("-" * 80)
        for i, issue in enumerate(result.warnings, 1):
            output.append(f"\n{i}. **{issue.title}**")
            output.append(f"   File: {issue.file}")
            if issue.line:
                output.append(f"   Line: {issue.line}")
            output.append(f"   {issue.description}")
            if issue.suggestion:
                output.append(f"   Suggestion: {issue.suggestion}")
        output.append("")

    # Nitpicks
    if result.nitpicks:
        output.append(f"💡 NITPICKS ({len(result.nitpicks)})")
        output.append("-" * 80)
        for i, issue in enumerate(result.nitpicks, 1):
            output.append(f"{i}. {issue.title} - {issue.file}")
        output.append("")

    # Positives
    if result.positives:
        output.append("✅ WHAT'S WORKING WELL")
        output.append("-" * 80)
        for positive in result.positives:
            output.append(f"  {positive}")
        output.append("")

    # Summary
    output.append("=" * 80)
    output.append("SUMMARY")
    output.append("=" * 80)
    output.append(f"Total Issues: {result.total_issues()}")
    output.append(f"  Blocking: {len(result.blocking)}")
    output.append(f"  Warnings: {len(result.warnings)}")
    output.append(f"  Nitpicks: {len(result.nitpicks)}")
    output.append("")

    if result.has_blocking_issues():
        output.append("❌ REVIEW FAILED - Blocking issues must be resolved")
        output.append("")
    elif len(result.warnings) > 0:
        output.append("⚠️  REVIEW PASSED WITH WARNINGS")
        output.append("")
    else:
        output.append("✅ REVIEW PASSED")
        output.append("")

    return "\n".join(output)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated code review for Home Assistant integrations"
    )
    parser.add_argument(
        "--files",
        nargs="*",
        help="Specific files to review (default: all Python files in custom_components/)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Review all files, not just changed files",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format",
    )

    args = parser.parse_args()

    # Determine root path
    root_path = Path.cwd()
    if not (root_path / "custom_components").exists():
        print("Error: custom_components/ directory not found", file=sys.stderr)
        print("Run this script from the repository root", file=sys.stderr)
        return 1

    # Determine files to review
    if args.files:
        files = [Path(f) for f in args.files]
    else:
        files = list((root_path / "custom_components").rglob("*.py"))
        manifest_files = list((root_path / "custom_components").rglob("manifest.json"))
        strings_files = list((root_path / "custom_components").rglob("strings.json"))
        files.extend(manifest_files)
        files.extend(strings_files)

    # Run review
    reviewer = CodeReviewer(root_path)
    result = reviewer.review_files(files)

    # Output results
    output_format = "json" if args.json else "text"
    print(format_output(result, output_format))

    # Return exit code
    return 1 if result.has_blocking_issues() else 0


if __name__ == "__main__":
    sys.exit(main())
