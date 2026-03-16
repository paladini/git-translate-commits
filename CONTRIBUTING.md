# Contributing to git-translate-commits

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
git clone https://github.com/paladini/git-translate-commits.git
cd git-translate-commits
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
pytest -v              # verbose
pytest -x              # stop on first failure
pytest tests/test_language_detector.py  # single file
```

## Code Style

- Python 3.10+ with type hints throughout
- Keep functions focused and small
- Follow existing patterns in the codebase
- No comments unless they explain *why*, not *what*

## Making Changes

1. **Fork** the repository
2. **Create a branch** from `main`: `git checkout -b my-feature`
3. **Make your changes** with clear, atomic commits
4. **Add tests** for new functionality
5. **Run the test suite**: `pytest`
6. **Push** your branch and open a **Pull Request**

## Pull Request Guidelines

- Keep PRs focused on a single change
- Reference any related issues (e.g. `Closes #42`)
- Ensure all tests pass
- Update documentation if behavior changes
- Use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages

## Reporting Bugs

Open an issue with:

- Steps to reproduce
- Expected vs actual behavior
- Python version, OS, and `git-translate-commits --version`
- Relevant error output

## Feature Requests

Open an issue describing:

- The problem you're trying to solve
- Your proposed solution
- Any alternatives you considered

## Adding Language Support

The local engine (Argos Translate) supports many language pairs. If you find a pair that doesn't work well:

1. Check if the Argos package exists: [available packages](https://www.argosopentech.com/argospm/index/)
2. If quality is poor, consider adding language-specific heuristics in `translator_local.py`

## License

By contributing, you agree that your contributions will be licensed under the [GPL-3.0](LICENSE) license.
