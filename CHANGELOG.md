# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-03-17

### Fixed

- Fix `AttributeError: 'GitRewriter' object has no attribute '_generate_filter_repo_callback'` when rewriting commits with `git-filter-repo` installed
- Replace broken `--message-callback` approach (which lacks access to commit hashes) with `--commit-callback` for correct hash-based message lookup
- Remove unused `_inline_callback` method and `tempfile` import

### Changed

- Contact email updated to use Gmail alias (`fnpaladini+git-translate-commits@gmail.com`)

## [1.0.0] - 2026-03-16

### Added

- Offline translation via [Argos Translate](https://github.com/argosopentech/argos-translate) (`--engine local`, default)
- LLM-based translation via [litellm](https://github.com/BerriAI/litellm) (`--engine llm`) supporting OpenAI, Anthropic, and OpenAI-compatible providers
- Automatic language detection using `langdetect`
- Conventional Commit prefix preservation (`feat:`, `fix:`, `chore:`, etc.)
- Git trailer preservation (`Co-authored-by`, `Signed-off-by`, etc.)
- Issue/PR reference preservation (`#123`, `JIRA-456`)
- Dry-run mode (`--dry-run`) with sample translations and cost estimates
- Automatic backup branch creation before rewriting
- Interactive confirmation prompt before destructive operations
- Filtering by branch, author, date range
- Batch processing for LLM translation to minimize API costs
- JSON operation log (`.git-translate-log.json`)
- Support for `git filter-branch` with `git-filter-repo` fallback detection
- CLI with comprehensive flags and environment variable support

[1.0.1]: https://github.com/paladini/git-translate-commits/releases/tag/v1.0.1
[1.0.0]: https://github.com/paladini/git-translate-commits/releases/tag/v1.0.0
