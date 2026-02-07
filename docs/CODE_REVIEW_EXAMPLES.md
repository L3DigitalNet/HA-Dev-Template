# Code Review Assistant Usage Examples

This document provides examples of how to use the automated code review assistant.

## Running Locally

### Basic Review

Review all files in custom_components/:

```bash
python scripts/code_review.py
```

### Review Specific Files

```bash
# Single file
python scripts/code_review.py --files custom_components/my_integration/sensor.py

# Multiple files
python scripts/code_review.py --files \
    custom_components/my_integration/__init__.py \
    custom_components/my_integration/config_flow.py \
    custom_components/my_integration/coordinator.py
```

### JSON Output

Get machine-readable output:

```bash
python scripts/code_review.py --json > review_results.json
```

## Integration with Make

```bash
# Run code review
make code-review

# Get JSON output
make code-review-json
```

## Pull Request Integration

The code review runs automatically on all pull requests. You'll see a comment like this:

```markdown
## 🤖 Automated Code Review

**Overall**: 🚫 CHANGES REQUESTED

**Quality Tier**: Silver
**Test Coverage**: 75.3%

### 🚫 Blocking Issues (1)

1. **Hardcoded Credential**
   - File: `custom_components/my_integration/api.py` (line 15)
   - Category: security
   - Hardcoded API key, password, or secret detected
   - **Suggestion**: Store credentials in config entry data
   - **Example**: `api_key = entry.data[CONF_API_KEY]`

### ⚠️ Recommended Changes (2)

1. **Missing Type Hint** - `coordinator.py` (line 45)
   - Function 'fetch_data' has no return type hint
   - **Suggestion**: Add type hints to all public functions

2. **Test Coverage Below Target** - `tests/`
   - Coverage is 75.3%, target is 80%
   - **Suggestion**: Add tests for uncovered code paths

---

### 📊 Summary

- **Total Issues**: 3
- **Blocking**: 1
- **Warnings**: 2
- **Nitpicks**: 0

*This is an automated first-pass review. Human review is still required.*
*Review performed by: Code Review Assistant*
```

## Understanding Issue Severity

### 🚫 Blocking Issues

These MUST be fixed before merge:
- Security vulnerabilities
- Blocking I/O in async functions
- Hardcoded credentials
- SQL injection risks
- Critical bugs

**Action**: PR will be marked as "Changes Requested"

### ⚠️ Recommended Changes

These SHOULD be addressed:
- Missing error handling
- Code duplication
- Missing type hints
- Suboptimal patterns
- Test coverage gaps

**Action**: PR will have comments posted

### 💡 Nitpicks

Optional improvements:
- Style suggestions
- Variable naming
- Minor optimizations

**Action**: Listed in collapsed section

## Common Security Issues Detected

### 1. Hardcoded Credentials

❌ **Bad:**
```python
API_KEY = "sk-1234567890abcdef"
PASSWORD = "mysecretpassword"
```

✅ **Good:**
```python
api_key = entry.data[CONF_API_KEY]
password = entry.data[CONF_PASSWORD]
```

### 2. Blocking I/O in Async

❌ **Bad:**
```python
async def fetch_data(self):
    response = requests.get(url)  # Blocks event loop!
    return response.json()
```

✅ **Good:**
```python
async def fetch_data(self):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### 3. SQL Injection

❌ **Bad:**
```python
query = f"SELECT * FROM users WHERE id = '{user_id}'"
cursor.execute(query)
```

✅ **Good:**
```python
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

### 4. Unsafe Eval

❌ **Bad:**
```python
result = eval(user_input)  # Code injection!
```

✅ **Good:**
```python
import ast
result = ast.literal_eval(user_input)  # Safe for literals
# or
import json
result = json.loads(user_input)  # Safe for JSON
```

### 5. Command Injection

❌ **Bad:**
```python
subprocess.run(f"ls {user_input}", shell=True)  # Injection risk!
```

✅ **Good:**
```python
subprocess.run(["ls", user_input], shell=False)
```

## Home Assistant Patterns Checked

### DataUpdateCoordinator

✅ **Detected patterns:**
- Using DataUpdateCoordinator for polling
- Proper error handling (UpdateFailed, ConfigEntryAuthFailed)
- Reasonable update intervals

### Config Flow

✅ **Detected patterns:**
- Config flow exists (no YAML)
- Proper error handling
- Unique ID set

### Entities

✅ **Detected patterns:**
- All entities have unique_id
- Using CoordinatorEntity
- Proper availability handling
- Device grouping

### Async Requirements

✅ **Detected patterns:**
- No blocking I/O in async functions
- Using aiohttp instead of requests
- Proper use of async_add_executor_job

## Customizing the Review

### Adding Custom Patterns

Edit `scripts/code_review.py` to add your own patterns:

```python
# In CodeReviewer.__init__()
self.security_patterns = {
    "my_pattern": re.compile(r"PATTERN_REGEX"),
    # ...
}
```

### Adjusting Severity

Change severity levels in the script:

```python
# Make a check less strict
self.result.add_issue(
    Issue(
        severity=Severity.WARNING,  # Changed from BLOCKING
        # ...
    )
)
```

### Adding New Checks

Add new check methods:

```python
def _check_my_pattern(self, file: Path, content: str) -> None:
    """Check for my custom pattern."""
    if "my_pattern" in content:
        self.result.add_issue(
            Issue(
                severity=Severity.WARNING,
                category=Category.QUALITY,
                file=str(file),
                line=None,
                title="My Custom Check",
                description="Description of the issue",
                suggestion="How to fix it",
            )
        )
```

## Troubleshooting

### Review Not Running

1. Check workflow is enabled:
   ```bash
   gh workflow list
   ```

2. Check workflow syntax:
   ```bash
   yamllint .github/workflows/code-review.yml
   ```

3. Check permissions in workflow file

### False Positives

Add inline comments to explain why patterns are safe:

```python
# nosec - This is safe because...
API_KEY = get_api_key_from_config()
```

Or update patterns in the script to be more specific.

### Missing Dependencies

Install required tools:

```bash
pip install ruff mypy pytest pytest-cov aiohttp homeassistant
```

## Best Practices

1. **Run locally before pushing**: Catch issues early
2. **Fix blocking issues first**: They prevent merging
3. **Consider warnings**: Usually correct
4. **Explain disagreements**: Add comments if you disagree
5. **Update patterns**: Add project-specific checks

## Resources

- [Agent Specification](../resources/agents/code-review-assistant.md)
- [Automation Guide](../.github/AUTOMATION_GUIDE.md#automated-code-review)
- [Security Best Practices](../docs/SECURITY_BEST_PRACTICES.md)
- [Quality Checklist](../docs/QUALITY_CHECKLIST.md)
