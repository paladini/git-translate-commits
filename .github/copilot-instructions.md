# Copilot Instructions

## Project Overview

**git-translate-commits** is a Python CLI tool that translates git commit messages to a target language. It supports offline translation (Argos Translate) and LLM-based translation (via litellm).

- **Language**: Python 3.10+
- **CLI Framework**: Typer + Rich
- **Package Manager**: setuptools (pyproject.toml)
- **Test Framework**: pytest

## Mandatory Practices

### Changelog

Every change **must** include an update to `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format:

- Add entries under an `## [Unreleased]` section (or a new version section if releasing).
- Use the appropriate subsection: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
- Be concise but descriptive. Reference issue numbers when applicable.

### Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes to CLI interface or public API.
- **MINOR**: New features, new CLI flags, new translation engines.
- **PATCH**: Bug fixes, performance improvements, documentation updates.

When bumping a version, update it in **all** of these locations:

1. `pyproject.toml` (`version` field)
2. `CHANGELOG.md` (new version section + link at the bottom)

### Documentation

When making changes, **always** update the relevant documentation:

- `README.md` — If adding/changing CLI flags, features, or installation steps.
- `CHANGELOG.md` — **Always**, for every change (see above).
- `docs/index.html` — If the change affects user-facing documentation on the website.
- Docstrings — If modifying public functions or classes.

### Code Style

- Follow existing code conventions and patterns.
- Use type hints for all function signatures.
- Do not add or remove comments/docstrings unless the change requires it.
- Keep imports at the top of the file, grouped by stdlib → third-party → local.

### Testing

- Add or update tests in `tests/` for any behavioral change.
- Run `pytest` before committing to ensure nothing is broken.
- Do not delete or weaken existing tests without explicit direction.

### Commits

- Use [Conventional Commits](https://www.conventionalcommits.org/) format: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, etc.
- Keep commits focused and atomic.
