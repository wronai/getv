# Contributing to getv

Thank you for your interest in contributing to getv! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. Fork the repository
2. Clone your fork locally
3. Create a feature branch
4. Make your changes
5. Add tests
6. Run the test suite
7. Submit a pull request

## 🛠️ Development Setup

### Prerequisites

- Python 3.9 or higher
- Git

### Setup

```bash
# Clone your fork
git clone https://github.com/your-username/getv.git
cd getv

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=getv

# Run specific test file
pytest tests/test_store.py
```

## 📝 Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Keep functions focused and small
- Add docstrings to public functions and classes

## 🐛 Bug Reports

When filing bug reports:

1. Use a descriptive title
2. Include Python version and OS
3. Provide minimal reproduction example
4. Include error messages and stack traces

## ✨ Feature Requests

When requesting features:

1. Explain the use case clearly
2. Consider if it fits the project scope
3. Be open to discussion and iteration

## 📦 Pull Requests

### PR Guidelines

1. **Keep it focused** - One PR per feature/fix
2. **Add tests** - Ensure new functionality is tested
3. **Update docs** - Update README.md if needed
4. **Clean history** - Use clear commit messages
5. **Pass CI** - All tests must pass

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Documentation updated
```

## 🔧 Development Workflow

### Branch Naming

- `feature/description` - new features
- `fix/description` - bug fixes
- `docs/description` - documentation updates
- `refactor/description` - refactoring

### Commit Messages

Follow conventional commits:

```
type(scope): description

feat(api): add profile encryption support
fix(cli): resolve password masking issue
docs(readme): update installation instructions
```

## 📚 Project Structure

```
getv/
├── getv/           # Main package
│   ├── __init__.py
│   ├── store.py    # EnvStore class
│   ├── profile.py  # ProfileManager class
│   ├── security.py # Encryption/masking
│   ├── formats.py  # Export formats
│   └── __main__.py # CLI entry point
├── tests/          # Test suite
├── README.md       # Main documentation
├── CHANGELOG.md    # Version history
└── pyproject.toml  # Project configuration
```

## 🤝 Getting Help

- Create an issue for bugs or questions
- Check existing issues first
- Join discussions in pull requests

## 📄 License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for contributing! 🎉
