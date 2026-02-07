# Code Review Assistant - Quick Reference

## 🚀 Quick Commands

```bash
# Run code review locally
python scripts/code_review.py

# Review specific files
python scripts/code_review.py --files custom_components/my_integration/*.py

# Get JSON output
python scripts/code_review.py --json

# Via Make
make code-review
make code-review-json
```

## 🎯 Severity Levels

| Icon | Severity | Action | Merging |
|------|----------|--------|---------|
| 🚫 | **Blocking** | MUST fix | ❌ Blocked |
| ⚠️ | **Warning** | SHOULD fix | ✅ Allowed |
| 💡 | **Nitpick** | Optional | ✅ Allowed |

## 🔒 Security Checks

✅ **Detected:**
- Hardcoded credentials (API keys, passwords, tokens)
- SQL injection patterns (string formatting in queries)
- Command injection (shell=True in subprocess)
- Unsafe eval() usage
- Blocking I/O in async functions (requests library)
- time.sleep() in async functions

## 📊 Quality Checks

✅ **Detected:**
- Missing type hints on functions
- Broad exception catching
- Missing unique_id on entities
- Config flow not enabled
- Missing manifest.json fields
- Invalid JSON in strings.json

## 🧪 Coverage Thresholds

| Coverage | Severity | Status |
|----------|----------|--------|
| ≥ 80% | ✅ Pass | Excellent |
| 60-79% | ⚠️ Warning | Acceptable |
| < 60% | 🚫 Blocking | Insufficient |

## 🏆 Quality Tiers

| Tier | Requirements | Status |
|------|--------------|--------|
| Bronze | Config flow, tests, manifest | Minimum |
| Silver | Error handling, availability | Recommended |
| Gold | Full async, 80% coverage, types | Professional |
| Platinum | Best practices, performance | Excellence |

## 🐛 Common Issues & Fixes

### Hardcoded Credentials
```python
# ❌ Bad
API_KEY = "sk-1234567890"

# ✅ Good
api_key = entry.data[CONF_API_KEY]
```

### Blocking I/O
```python
# ❌ Bad
async def fetch():
    return requests.get(url).json()

# ✅ Good
async def fetch():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### SQL Injection
```python
# ❌ Bad
query = f"SELECT * FROM users WHERE id = '{user_id}'"

# ✅ Good
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

### Missing Type Hints
```python
# ❌ Bad
def fetch_data(device_id):
    return get_data(device_id)

# ✅ Good
def fetch_data(device_id: str) -> dict[str, Any]:
    return get_data(device_id)
```

## 📝 On Pull Requests

The review runs automatically and posts:

1. **Overall Status**: ✅ / ⚠️ / 🚫
2. **Quality Tier**: Bronze / Silver / Gold / Platinum
3. **Coverage**: Percentage
4. **Issues**: Categorized by severity
5. **Suggestions**: With code examples

## 🔧 Customization

Edit `scripts/code_review.py`:

```python
# Add custom security pattern
self.security_patterns["my_pattern"] = re.compile(r"REGEX")

# Add custom check
def _check_my_pattern(self, file: Path, content: str) -> None:
    # Your check logic
    pass
```

## 📚 Full Documentation

- [CODE_REVIEW_EXAMPLES.md](../docs/CODE_REVIEW_EXAMPLES.md) - Detailed examples
- [code-review-assistant.md](code-review-assistant.md) - Agent specification
- [AUTOMATION_GUIDE.md](../../.github/AUTOMATION_GUIDE.md) - CI/CD integration
- [SECURITY_BEST_PRACTICES.md](../docs/SECURITY_BEST_PRACTICES.md) - Security patterns

## 💡 Tips

1. ✅ Run locally before pushing
2. ✅ Fix blocking issues first
3. ✅ Consider warnings carefully
4. ✅ Read suggested fixes
5. ✅ Ask if unclear

## 🆘 Troubleshooting

**Issue**: Review not running
```bash
gh workflow list
gh run list --workflow=code-review.yml
```

**Issue**: False positives
- Add comments explaining why code is safe
- Update patterns in code_review.py
- Use `# noqa` sparingly

**Issue**: Missing dependencies
```bash
pip install ruff mypy pytest pytest-cov aiohttp
```

---

**Remember**: The automated review catches common issues. Human review is still required for architecture, business logic, and UX decisions.
