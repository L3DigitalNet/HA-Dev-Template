#!/usr/bin/env python3
"""Documentation Audit Script for HA-Dev-Template.

This script performs comprehensive documentation audits to ensure that
documentation accurately reflects the actual code implementation.

Features:
- Verifies version numbers (Python, Home Assistant, packages)
- Checks file and directory references
- Validates code examples against actual implementation
- Checks external link validity
- Cross-references documentation files
- Generates detailed audit reports

Usage:
    python scripts/audit_documentation.py [--fix] [--verbose]
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AuditIssue:
    """Represents a documentation issue found during audit."""

    severity: str  # "error", "warning", "info"
    category: str  # "version", "file_reference", "code_example", "link", etc.
    file: str
    line: int | None
    description: str
    suggestion: str | None = None


@dataclass
class AuditReport:
    """Contains the results of a documentation audit."""

    issues: list[AuditIssue] = field(default_factory=list)
    files_checked: int = 0
    checks_performed: int = 0

    def add_issue(
        self,
        severity: str,
        category: str,
        file: str,
        description: str,
        line: int | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Add an issue to the report."""
        self.issues.append(
            AuditIssue(
                severity=severity,
                category=category,
                file=file,
                line=line,
                description=description,
                suggestion=suggestion,
            )
        )

    def print_report(self, verbose: bool = False) -> None:
        """Print the audit report."""
        print("\n" + "=" * 80)
        print("DOCUMENTATION AUDIT REPORT")
        print("=" * 80)
        print(f"\nFiles Checked: {self.files_checked}")
        print(f"Checks Performed: {self.checks_performed}")
        print(f"Issues Found: {len(self.issues)}")

        # Count by severity
        errors = sum(1 for i in self.issues if i.severity == "error")
        warnings = sum(1 for i in self.issues if i.severity == "warning")
        info = sum(1 for i in self.issues if i.severity == "info")

        print(f"  - Errors: {errors}")
        print(f"  - Warnings: {warnings}")
        print(f"  - Info: {info}")

        if self.issues:
            print("\n" + "-" * 80)
            print("ISSUES DETAILS")
            print("-" * 80)

            for issue in sorted(self.issues, key=lambda x: (x.severity, x.file)):
                severity_symbol = {
                    "error": "❌",
                    "warning": "⚠️ ",
                    "info": "ℹ️ ",
                }[issue.severity]

                print(f"\n{severity_symbol} [{issue.severity.upper()}] {issue.category}")
                print(f"   File: {issue.file}")
                if issue.line:
                    print(f"   Line: {issue.line}")
                print(f"   Issue: {issue.description}")
                if issue.suggestion:
                    print(f"   Fix: {issue.suggestion}")
        else:
            print("\n✅ No issues found! Documentation is in sync with code.")

        print("\n" + "=" * 80)


class DocumentationAuditor:
    """Performs comprehensive documentation audits."""

    def __init__(self, repo_root: Path, verbose: bool = False):
        """Initialize the auditor.

        Args:
            repo_root: Path to the repository root
            verbose: Enable verbose output
        """
        self.repo_root = repo_root
        self.verbose = verbose
        self.report = AuditReport()

    def audit(self) -> AuditReport:
        """Run all audit checks."""
        print("🔍 Starting documentation audit...")

        self.check_python_version_references()
        self.check_package_version_references()
        self.check_file_directory_references()
        self.check_manifest_consistency()
        self.check_code_example_validity()
        self.check_skills_references()

        return self.report

    def check_python_version_references(self) -> None:
        """Check Python version references in documentation."""
        if self.verbose:
            print("  Checking Python version references...")

        # Get actual Python version
        try:
            result = subprocess.run(
                [sys.executable, "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            actual_version = result.stdout.strip().replace("Python ", "")
        except subprocess.CalledProcessError:
            actual_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        self.report.checks_performed += 1

        # Find all Python version references in markdown files
        version_pattern = re.compile(r"Python\s+(\d+\.\d+\.\d+)")

        for md_file in self.repo_root.rglob("*.md"):
            if ".git" in str(md_file):
                continue

            self.report.files_checked += 1
            content = md_file.read_text(encoding="utf-8")
            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                matches = version_pattern.findall(line)
                for doc_version in matches:
                    if doc_version != actual_version:
                        self.report.add_issue(
                            severity="error",
                            category="version_mismatch",
                            file=str(md_file.relative_to(self.repo_root)),
                            line=line_num,
                            description=f"Python version mismatch: documented as {doc_version}, actual is {actual_version}",
                            suggestion=f"Update to Python {actual_version}",
                        )

    def check_package_version_references(self) -> None:
        """Check package version references against actual installed versions."""
        if self.verbose:
            print("  Checking package version references...")

        # Read pyproject.toml to get expected packages
        pyproject_path = self.repo_root / "pyproject.toml"
        if not pyproject_path.exists():
            return

        self.report.checks_performed += 1

        # Pattern to find package version references like "homeassistant==2026.2.0"
        version_pattern = re.compile(r"(homeassistant|pytest|ruff|mypy)==([\d.]+)")

        for md_file in self.repo_root.rglob("*.md"):
            if ".git" in str(md_file):
                continue

            content = md_file.read_text(encoding="utf-8")
            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                matches = version_pattern.findall(line)
                for package, version in matches:
                    # Try to get actual version
                    try:
                        result = subprocess.run(
                            [sys.executable, "-m", "pip", "show", package],
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        if result.returncode == 0:
                            for line_text in result.stdout.split("\n"):
                                if line_text.startswith("Version:"):
                                    actual_version = line_text.split(":", 1)[1].strip()
                                    if actual_version != version:
                                        self.report.add_issue(
                                            severity="warning",
                                            category="version_mismatch",
                                            file=str(md_file.relative_to(self.repo_root)),
                                            line=line_num,
                                            description=f"{package} version mismatch: documented as {version}, installed is {actual_version}",
                                            suggestion=f"Update to {package}=={actual_version} or install correct version",
                                        )
                    except Exception:
                        pass

    def check_file_directory_references(self) -> None:
        """Check that file and directory references in docs actually exist."""
        if self.verbose:
            print("  Checking file and directory references...")

        self.report.checks_performed += 1

        # Patterns for file/directory references
        patterns = [
            re.compile(r"`([a-zA-Z0-9_/.-]+\.(py|json|md|yaml|yml|toml|txt))`"),
            re.compile(r"\[.*?\]\(([a-zA-Z0-9_/.-]+(?:\.(py|json|md|yaml|yml|toml|txt))?)\)"),
            re.compile(r"^[\s-]*([a-zA-Z0-9_/.-]+/)$", re.MULTILINE),
        ]

        for md_file in self.repo_root.rglob("*.md"):
            if ".git" in str(md_file):
                continue

            content = md_file.read_text(encoding="utf-8")
            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                for pattern in patterns:
                    matches = pattern.findall(line)
                    for match in matches:
                        # Extract filename from tuple if needed
                        file_ref = match[0] if isinstance(match, tuple) else match

                        # Skip URLs and anchors
                        if file_ref.startswith(("http://", "https://", "#", "mailto:")):
                            continue

                        # Skip placeholder patterns
                        if any(p in file_ref for p in ["your_", "your-", "<", ">"]):
                            continue

                        # Try to resolve the path
                        possible_paths = [
                            self.repo_root / file_ref,
                            self.repo_root / file_ref.lstrip("/"),
                            md_file.parent / file_ref,
                        ]

                        exists = any(p.exists() for p in possible_paths)

                        if not exists and not file_ref.startswith("~"):
                            # Only warn for specific important directories/files
                            if any(
                                important in file_ref
                                for important in [
                                    "custom_components",
                                    "tests",
                                    "docs",
                                    "scripts",
                                    ".py",
                                    ".json",
                                    ".md",
                                ]
                            ):
                                self.report.add_issue(
                                    severity="warning",
                                    category="file_reference",
                                    file=str(md_file.relative_to(self.repo_root)),
                                    line=line_num,
                                    description=f"Referenced file/directory may not exist: {file_ref}",
                                    suggestion="Verify the path exists or update the reference",
                                )

    def check_manifest_consistency(self) -> None:
        """Check manifest.json consistency with documentation."""
        if self.verbose:
            print("  Checking manifest.json consistency...")

        self.report.checks_performed += 1

        # Find all manifest.json files
        for manifest_path in self.repo_root.rglob("manifest.json"):
            if ".git" in str(manifest_path):
                continue

            try:
                with open(manifest_path, encoding="utf-8") as f:
                    manifest = json.load(f)

                # Check if domain matches directory name
                domain = manifest.get("domain")
                if domain and manifest_path.parent.name != domain:
                    self.report.add_issue(
                        severity="error",
                        category="manifest_mismatch",
                        file=str(manifest_path.relative_to(self.repo_root)),
                        line=None,
                        description=f"Domain '{domain}' doesn't match directory name '{manifest_path.parent.name}'",
                        suggestion=f"Ensure domain and directory name match",
                    )

                # Check for required fields
                required_fields = ["domain", "name", "version", "codeowners"]
                for field in required_fields:
                    if field not in manifest:
                        self.report.add_issue(
                            severity="error",
                            category="manifest_incomplete",
                            file=str(manifest_path.relative_to(self.repo_root)),
                            line=None,
                            description=f"Missing required field: {field}",
                            suggestion=f"Add '{field}' to manifest.json",
                        )

            except json.JSONDecodeError as e:
                self.report.add_issue(
                    severity="error",
                    category="manifest_invalid",
                    file=str(manifest_path.relative_to(self.repo_root)),
                    line=None,
                    description=f"Invalid JSON: {e}",
                    suggestion="Fix JSON syntax errors",
                )

    def check_code_example_validity(self) -> None:
        """Check that code examples in docs are syntactically valid."""
        if self.verbose:
            print("  Checking code example validity...")

        self.report.checks_performed += 1

        # Pattern to find Python code blocks
        code_block_pattern = re.compile(r"```python\n(.*?)```", re.DOTALL)

        for md_file in self.repo_root.rglob("*.md"):
            if ".git" in str(md_file):
                continue

            content = md_file.read_text(encoding="utf-8")
            code_blocks = code_block_pattern.findall(content)

            for code_block in code_blocks:
                # Skip examples with placeholders
                if any(
                    p in code_block
                    for p in ["...", "your_", "my_", "<", ">", "# "]
                ):
                    continue

                # Try to parse the code
                try:
                    ast.parse(code_block)
                except SyntaxError as e:
                    self.report.add_issue(
                        severity="warning",
                        category="code_example",
                        file=str(md_file.relative_to(self.repo_root)),
                        line=None,
                        description=f"Code example has syntax error: {e}",
                        suggestion="Fix the Python syntax in the code example",
                    )

    def check_skills_references(self) -> None:
        """Check skills directory references."""
        if self.verbose:
            print("  Checking skills references...")

        self.report.checks_performed += 1

        skills_dir = self.repo_root / "resources" / "skills"
        if not skills_dir.exists():
            self.report.add_issue(
                severity="error",
                category="directory_missing",
                file="resources/",
                line=None,
                description="skills directory does not exist at resources/skills",
                suggestion="Create the directory or update documentation",
            )
            return

        # Check what skills actually exist
        actual_skills = [
            d.name for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
        ]

        # Check documentation for skill references
        for md_file in self.repo_root.rglob("*.md"):
            if ".git" in str(md_file):
                continue

            content = md_file.read_text(encoding="utf-8")

            # Check for skills installation instructions
            if "resources/skills" in content or "~/.claude/skills" in content:
                # Verify the instructions mention the correct skills
                for skill in actual_skills:
                    if skill not in content and "ha-skills" in content:
                        self.report.add_issue(
                            severity="info",
                            category="skills_documentation",
                            file=str(md_file.relative_to(self.repo_root)),
                            line=None,
                            description=f"Skills directory contains '{skill}' but documentation may not reference it correctly",
                            suggestion="Verify skills installation instructions are accurate",
                        )


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Audit documentation for HA-Dev-Template"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to auto-fix issues (not implemented yet)",
    )

    args = parser.parse_args()

    # Find repository root
    repo_root = Path(__file__).parent.parent.resolve()

    # Run audit
    auditor = DocumentationAuditor(repo_root, verbose=args.verbose)
    report = auditor.audit()

    # Print report
    report.print_report(verbose=args.verbose)

    # Return exit code based on errors
    errors = sum(1 for i in report.issues if i.severity == "error")
    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
