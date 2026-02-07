# Documentation Audit Tool

## Overview

The documentation audit tool (`scripts/audit_documentation.py`) is an automated system that ensures all documentation in this repository accurately reflects the actual code implementation. This tool is part of our autonomous documentation maintenance system.

## Purpose

The audit tool performs comprehensive checks to:

1. **Verify Version Consistency** - Ensures Python, Home Assistant, and package versions in documentation match actual installed versions
2. **Check File References** - Validates that all file and directory references in documentation actually exist
3. **Validate Code Examples** - Checks that Python code examples in documentation are syntactically correct
4. **Verify Manifest Integrity** - Ensures manifest.json files are valid and consistent
5. **Cross-Reference Documentation** - Identifies inconsistencies across different documentation sources
6. **Audit Skills References** - Verifies that skills directory structure matches documentation

## Usage

### Basic Usage

```bash
# Run the audit
python scripts/audit_documentation.py

# Run with verbose output
python scripts/audit_documentation.py --verbose

# Or use the Makefile target
make audit-docs
```

### Output

The tool generates a comprehensive report showing:

- **Files Checked**: Number of documentation files analyzed
- **Checks Performed**: Number of different audit checks run
- **Issues Found**: Total count of issues by severity:
  - ❌ **Errors**: Critical issues that must be fixed (e.g., version mismatches)
  - ⚠️ **Warnings**: Issues that should be reviewed (e.g., possibly incorrect file references)
  - ℹ️ **Info**: Informational notices (e.g., suggestions for improvement)

### Example Output

```
================================================================================
DOCUMENTATION AUDIT REPORT
================================================================================

Files Checked: 58
Checks Performed: 6
Issues Found: 93
  - Errors: 0
  - Warnings: 87
  - Info: 6

--------------------------------------------------------------------------------
ISSUES DETAILS
--------------------------------------------------------------------------------

❌ [ERROR] version_mismatch
   File: README.md
   Line: 9
   Issue: Python version mismatch: documented as 3.14.2, actual is 3.12.3
   Fix: Update to Python 3.12.3
```

## Audit Checks

### 1. Python Version References

**What it checks:**
- Scans all `.md` files for Python version references (e.g., "Python 3.12.3")
- Compares documented versions against the actual Python version

**Why it matters:**
- Incorrect version numbers mislead developers about requirements
- Can cause setup failures if users install wrong Python version

**How to fix:**
```bash
# Find all instances
grep -r "Python X.Y.Z" . --include="*.md"

# Update to match actual version
python --version  # Check actual version
```

### 2. Package Version References

**What it checks:**
- Finds package version specifications (e.g., `homeassistant==2026.2.0`)
- Compares against actually installed package versions

**Why it matters:**
- Ensures dependencies documentation is accurate
- Prevents version conflicts during installation

**How to fix:**
```bash
# Check installed version
pip show homeassistant

# Update documentation to match
```

### 3. File and Directory References

**What it checks:**
- Locates file references in backticks (e.g., `` `config_flow.py` ``)
- Verifies markdown links point to existing files
- Checks directory references in structured lists

**Why it matters:**
- Broken links frustrate users trying to navigate documentation
- Missing file references indicate outdated documentation

**Common false positives:**
- Placeholder examples (e.g., `your_integration/`)
- Optional files not committed (e.g., `venv/`)
- External references (e.g., `~/.claude/skills/`)

**How to fix:**
```bash
# For legitimate issues:
# 1. Create the referenced file if it should exist
# 2. Update the path if the file moved
# 3. Remove the reference if the file was intentionally removed
```

### 4. Manifest Consistency

**What it checks:**
- Validates all `manifest.json` files for JSON syntax errors
- Ensures `domain` field matches directory name
- Verifies required fields are present (`domain`, `name`, `version`, `codeowners`)

**Why it matters:**
- Invalid manifest prevents integration from loading
- Domain mismatch causes runtime errors

**How to fix:**
```bash
# Validate JSON syntax
cat custom_components/your_integration/manifest.json | python -m json.tool

# Ensure domain matches directory
cd custom_components/
# Domain in manifest should match folder name
```

### 5. Code Example Validity

**What it checks:**
- Extracts Python code blocks from markdown (` ```python ... ``` `)
- Parses code using Python's AST parser
- Reports syntax errors

**Why it matters:**
- Invalid code examples confuse developers
- Copy-pasted code with syntax errors wastes time

**Common false positives:**
- Intentionally incomplete examples with `...`
- Pseudo-code or placeholders

**How to fix:**
```python
# Test the code example
python -c "import ast; ast.parse('''
# your code here
''')"
```

### 6. Skills References

**What it checks:**
- Lists actual skills in `resources/skills/`
- Compares against documentation references
- Identifies skills mentioned in docs that don't exist or vice versa

**Why it matters:**
- Ensures installation instructions are accurate
- Helps users understand available skills

**How to fix:**
```bash
# List actual skills
ls -1 resources/skills/

# Update documentation to match
```

## Integration with Workflow

### Pre-Commit Hook (Optional)

To run the audit automatically before commits:

```yaml
# Add to .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: audit-docs
        name: Audit Documentation
        entry: python scripts/audit_documentation.py
        language: system
        pass_filenames: false
        always_run: true
```

### CI/CD Integration

Add to `.github/workflows/ci.yml`:

```yaml
- name: Audit Documentation
  run: |
    python scripts/audit_documentation.py
  continue-on-error: true  # Don't fail CI on warnings
```

### Regular Maintenance

Recommended schedule:
- **Before releases**: Run full audit
- **After code changes**: Check affected documentation
- **Weekly/Monthly**: Run comprehensive audit

```bash
# Add to your maintenance checklist
make audit-docs
```

## Interpreting Results

### When to Act

**Errors (❌)**: Fix immediately
- Version mismatches
- Invalid JSON in manifests
- Critical file references

**Warnings (⚠️)**: Review and fix if legitimate
- File references (check for false positives)
- Code syntax errors (check for intentional placeholders)

**Info (ℹ️)**: Consider improvements
- Documentation completeness
- Consistency suggestions

### Common Issues

#### False Positives

**Placeholder paths:**
```markdown
# These are intentionally generic
custom_components/your_integration/
~/.claude/skills/
```

**Optional directories:**
```markdown
# These may not exist in the repo
venv/  # Gitignored
.pytest_cache/  # Generated at runtime
```

**Fix:** These are expected and can be ignored.

#### Real Issues

**Renamed files:**
```markdown
# Old reference
See `coordinator.py` for details

# File was renamed to data_coordinator.py
```

**Fix:** Update documentation to reference new filename.

**Version drift:**
```markdown
# Documentation says one version
# But system has different version
```

**Fix:** Update all version references to match reality.

## Extending the Audit Tool

### Adding New Checks

To add a new audit check:

1. Create a new method in the `DocumentationAuditor` class:

```python
def check_your_new_check(self) -> None:
    """Check for your new validation."""
    if self.verbose:
        print("  Checking your new validation...")
    
    self.report.checks_performed += 1
    
    # Your validation logic here
    # Use self.report.add_issue() to report problems
```

2. Call it from the `audit()` method:

```python
def audit(self) -> AuditReport:
    """Run all audit checks."""
    # ... existing checks ...
    self.check_your_new_check()
    return self.report
```

### Issue Severity Guidelines

- **error**: Must be fixed before release, blocks functionality
- **warning**: Should be reviewed and likely fixed, may confuse users
- **info**: Optional improvements, suggestions for better documentation

## Maintenance

The audit tool itself should be maintained:

1. **Update patterns** as documentation conventions change
2. **Add checks** when new common errors are discovered
3. **Refine heuristics** to reduce false positives
4. **Test thoroughly** against the repository

## Related Documentation

- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [.github/agents/documentation-curator.agent.md](../.github/agents/documentation-curator.agent.md) - Documentation curator agent definition
- [REFERENCE_GUIDE.md](../REFERENCE_GUIDE.md) - Complete reference guide

## Support

If you encounter issues with the audit tool:

1. Check if it's a false positive (see "Interpreting Results")
2. Review the specific check documentation above
3. Open an issue if you believe the tool has a bug
4. Suggest improvements via pull request

---

**Last Updated:** 2026-02-07
**Audit Tool Version:** 1.0.0
