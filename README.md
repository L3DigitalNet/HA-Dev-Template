# Home Assistant Integration Development Template

A complete, production-ready template repository for developing Home Assistant custom integrations. Includes development environment setup, testing framework, code quality tools, and example integration structure.

## Features

- ✅ **Python 3.14.2** - Latest Python with full async support
- ✅ **Home Assistant 2026.2.0** - Latest HA core
- ✅ **Complete Testing Suite** - pytest with HA custom component support
- ✅ **Code Quality Tools** - Ruff (linter/formatter), mypy (type checker)
- ✅ **Automated Code Review** - Pre-reviews PRs for security, quality, and patterns
- ✅ **Pre-commit Hooks** - Automated code quality checks
- ✅ **VS Code Integration** - Optimized settings + debug configurations
- ✅ **Complete Example Integration** - Working implementation with coordinator, config flow, entities
- ✅ **Comprehensive Documentation** - 7 implementation guides in `/docs/`
- ✅ **CI/CD Workflows** - GitHub Actions for automated testing
- ✅ **Verification Script** - Automated environment validation

## Quick Start

### 1. Clone and Setup

```bash
# Clone this repository
git clone <your-repo-url>
cd ha-template

# The virtual environment and all dependencies are already installed!
# Just activate the virtual environment
source venv/bin/activate
```

### 2. Verify Installation

```bash
# Run the verification script
python scripts/verify_environment.py
```

You should see: `✓ All checks passed!`

### 3. Start Developing

```bash
# Run tests
pytest tests/ -v

# Lint and format code
ruff check custom_components/ --fix
ruff format custom_components/

# Type check
mypy custom_components/

# Run all quality checks (via pre-commit)
pre-commit run --all-files
```

## Repository Structure

```
ha-template/
├── custom_components/          # Home Assistant integrations
│   └── example_integration/    # Complete working example integration
│       ├── __init__.py         # Integration entry point (setup/unload)
│       ├── api.py              # Mock API client
│       ├── config_flow.py      # UI configuration flow
│       ├── coordinator.py      # DataUpdateCoordinator
│       ├── entity.py           # Base entity class
│       ├── sensor.py           # Sensor platform
│       ├── const.py            # Constants
│       ├── manifest.json       # Integration metadata
│       ├── strings.json        # UI strings
│       └── README.md           # Integration documentation
│
├── tests/                      # Complete test suite
│   ├── conftest.py             # Shared fixtures and mocks
│   ├── test_init.py            # Setup/unload tests
│   ├── test_config_flow.py     # Config flow tests
│   ├── test_coordinator.py     # Coordinator tests
│   ├── test_sensor.py          # Sensor platform tests
│   └── README.md               # Testing guide
│
├── docs/                       # Implementation guides
│   ├── README.md               # Documentation index
│   ├── QUALITY_CHECKLIST.md    # Bronze → Platinum tier tracking
│   ├── HACS_INTEGRATION.md     # Publishing to HACS
│   ├── SECURITY_BEST_PRACTICES.md  # Credential & API security
│   ├── MIGRATION_GUIDE.md      # Config entry migrations
│   ├── PERFORMANCE.md          # Optimization patterns
│   └── LOCALIZATION.md         # Multi-language support
│
├── .github/                    # GitHub configuration
│   ├── workflows/
│   │   └── ci.yml              # CI/CD pipeline (lint, test, type-check)
│   ├── ISSUE_TEMPLATE/         # Issue templates
│   ├── pull_request_template.md
│   ├── AUTOMATION_GUIDE.md
│   ├── copilot-instructions.md
│   └── dependabot.yml
│
├── .vscode/                    # VS Code configuration
│   ├── settings.json           # Editor settings
│   ├── launch.json             # Debug configurations (7 scenarios)
│   ├── tasks.json              # Task definitions
│   └── codex-instructions.md   # Codex/Copilot guidance
│
├── scripts/                    # Utility scripts
│   └── verify_environment.py  # Environment verification
│
├── resources/                  # Development resources
│   ├── agents/                 # HA integration development agents
│   │   └── ha-integration-agent/
│   ├── skills/                 # Claude Code skills
│   └── ha-dev-environment-requirements.md
│
├── venv/                       # Python virtual environment (gitignored)
│
├── pyproject.toml              # Python project configuration
├── mypy.ini                    # Type checker configuration
├── Makefile                    # Development commands
├── .pre-commit-config.yaml     # Pre-commit hooks
├── .gitignore                  # Git ignore rules
├── CLAUDE.md                   # AI assistant instructions
├── REFERENCE_GUIDE.md          # Development reference
├── CONTRIBUTING.md             # Contribution guidelines
├── CHANGELOG.md                # Version history
└── README.md                   # This file
```

## Development Workflow

### Creating a New Integration

1. **Copy the Example**:
   ```bash
   cp -r custom_components/example_integration custom_components/your_integration
   ```

2. **Update Metadata**:
   - Edit `manifest.json` with your integration details
   - Update `const.py` with your domain name
   - Modify `strings.json` for your config flow

3. **Implement Features**:
   - Add config flow (`config_flow.py`)
   - Create coordinator (`coordinator.py`)
   - Add entity platforms (`sensor.py`, `switch.py`, etc.)

4. **Write Tests**:
   ```bash
   # Create test files
   touch tests/test_config_flow.py
   touch tests/test_init.py

   # Run tests
   pytest tests/ -v --cov=custom_components.your_integration
   ```

5. **Quality Checks**:
   ```bash
   # Lint and format
   ruff check . --fix
   ruff format .

   # Type check
   mypy custom_components/your_integration/

   # Run pre-commit
   pre-commit run --all-files
   ```

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=custom_components --cov-report=html

# Specific test file
pytest tests/test_config_flow.py -v

# Specific test
pytest tests/test_config_flow.py::test_user_flow_success -v
```

### Code Quality

```bash
# Lint and auto-fix
ruff check . --fix

# Format code
ruff format .

# Type check
mypy custom_components/

# Run automated code review
python scripts/code_review.py

# All quality checks
pre-commit run --all-files
```

### Code Review

This template includes an automated code review assistant that pre-reviews pull requests:

```bash
# Run locally on your changes
python scripts/code_review.py

# Review specific files
python scripts/code_review.py --files custom_components/my_integration/*.py

# Get JSON output
python scripts/code_review.py --json
```

**On Pull Requests:**
- 🔒 Detects security vulnerabilities
- 📊 Enforces HA quality standards
- 🧪 Checks test coverage
- 📚 Validates documentation
- ✅ Posts detailed review comments

See [.github/AUTOMATION_GUIDE.md](.github/AUTOMATION_GUIDE.md#automated-code-review) for full details.

## Integration Quality Scale

This template helps you achieve Home Assistant integration quality tiers:

- **Bronze** (Minimum for custom integrations):
  - ✅ Config flow UI setup
  - ✅ Automated setup tests
  - ✅ Basic coding standards

- **Silver** (Reliability):
  - Error handling
  - Entity availability management
  - Troubleshooting docs

- **Gold** (Feature Complete):
  - Full async codebase
  - Comprehensive test coverage
  - Complete type annotations

- **Platinum** (Excellence):
  - Best practices throughout
  - Clear code comments
  - Optimal performance

## Resources

### Documentation

**Implementation Guides:**
- [📚 docs/](docs/) - Complete implementation guide directory
  - [Quality Checklist](docs/QUALITY_CHECKLIST.md) - Track Bronze → Platinum progress
  - [HACS Integration](docs/HACS_INTEGRATION.md) - Publishing to HACS
  - [Security Best Practices](docs/SECURITY_BEST_PRACTICES.md) - Credential & API handling
  - [Migration Guide](docs/MIGRATION_GUIDE.md) - Config entry version migrations
  - [Performance](docs/PERFORMANCE.md) - Optimization patterns
  - [Localization](docs/LOCALIZATION.md) - Multi-language support

**Environment & Setup:**
- [ha-dev-environment-requirements.md](ha-dev-environment-requirements.md) - Complete environment setup guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [CHANGELOG.md](CHANGELOG.md) - Version history

**Official HA Documentation:**
- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/)

### Skills and Agents

This repository includes Claude Code skills for HA development:

```bash
# Install skills (project-level, recommended)
cp -r resources/skills/ha-skills ~/.claude/skills/
```

Available skills:
- `ha-integration-scaffold` - Generate integration structure
- `ha-config-flow` - Config flow implementation
- `ha-coordinator` - DataUpdateCoordinator patterns
- `ha-entity-platforms` - Entity platform creation
- `ha-testing` - Test writing guidance
- `ha-debugging` - Troubleshooting assistance

## Environment Details

### Installed Packages

**Core:**
- homeassistant==2026.2.0
- aiohttp==3.13.3
- voluptuous==0.15.2

**Testing:**
- pytest==9.0.0
- pytest-asyncio==1.3.0
- pytest-homeassistant-custom-component==0.13.313
- pytest-cov==7.0.0

**Code Quality:**
- ruff==0.15.0
- mypy==1.19.1
- pre-commit==4.5.1

### Python Version

- Python 3.14.2 (meets HA 2025.2+ requirement for Python 3.13+)

## Troubleshooting

### Virtual Environment Not Activated

```bash
source venv/bin/activate
```

### Import Errors

```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r <(pip freeze)
```

### Pre-commit Hooks Failing

```bash
# Reinstall hooks
pre-commit clean
pre-commit install
pre-commit run --all-files
```

### Test Failures

```bash
# Ensure you're in the virtual environment
source venv/bin/activate

# Reinstall test dependencies
pip install pytest pytest-homeassistant-custom-component pytest-asyncio
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup instructions
- Code quality standards
- Testing requirements
- Pull request process

This is a template repository. Fork it to create your own HA integration projects!

## License

[Your License Here]

## Support

- [Home Assistant Community](https://community.home-assistant.io/)
- [HA Developer Docs](https://developers.home-assistant.io/)
- [GitHub Issues](https://github.com/yourusername/ha-template/issues)
