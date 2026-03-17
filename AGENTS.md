# Agent Instructions

This file provides instructions for AI coding agents (Copilot, Cascade, Cursor, Cline, etc.) working on this project.

## Critical Rules

1. **Always update `CHANGELOG.md`** — Every change, no matter how small, must be documented in the changelog following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

2. **Always update documentation** — If your change affects user-facing behavior, update `README.md`, `docs/index.html`, and any other relevant docs.

3. **Follow Semantic Versioning** — Bump the version in `pyproject.toml` when preparing a release:
   - **PATCH** (1.0.x): Bug fixes
   - **MINOR** (1.x.0): New features
   - **MAJOR** (x.0.0): Breaking changes

4. **Run tests** — Run `pytest` before committing. Add tests for new features and bug fixes.

5. **Use Conventional Commits** — Format: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`.

## Project Structure

```
src/git_translate_commits/
├── cli.py            # CLI entry point (Typer app)
├── pipeline.py       # Main orchestration logic
├── rewriter.py       # Git history rewriting (filter-repo / filter-branch)
├── translator.py     # Translation engines (local + LLM)
├── language_detector.py  # Language detection
├── reporter.py       # Rich console output and reports
├── models.py         # Data models (dataclasses)
└── py.typed          # PEP 561 marker
```

## Version Locations

When bumping the version, update **all** of these:

- `pyproject.toml` → `version = "x.y.z"`
- `CHANGELOG.md` → New section `## [x.y.z] - YYYY-MM-DD` + link at the bottom

## Tech Stack

- **Python** 3.10+
- **CLI**: Typer + Rich
- **Translation**: Argos Translate (offline), litellm (LLM)
- **Git**: GitPython, git-filter-repo, git-filter-branch
- **Testing**: pytest, pytest-mock
