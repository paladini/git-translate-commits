# git-translate-commits

[![PyPI](https://img.shields.io/pypi/v/git-translate-commits)](https://pypi.org/project/git-translate-commits/)
[![Python](https://img.shields.io/pypi/pyversions/git-translate-commits)](https://pypi.org/project/git-translate-commits/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Tests](https://github.com/paladini/git-translate-commits/actions/workflows/tests.yml/badge.svg)](https://github.com/paladini/git-translate-commits/actions/workflows/tests.yml)

Translate git commit messages to a target language. Runs **100% offline** by default using [Argos Translate](https://github.com/argosopentech/argos-translate) -- no API key, no cost. Optionally use LLM APIs for higher-quality contextual translation.

## Why?

With LLM-powered coding assistants generating commits in mixed languages, repositories end up with inconsistent commit histories. This tool normalizes all commit messages to your preferred language in a single command.

## Installation

The recommended way to install CLI tools is with [pipx](https://pipx.pypa.io/) (isolated environment) or [uv](https://docs.astral.sh/uv/):

```bash
# Recommended: pipx (isolated install)
pipx install git-translate-commits

# Or: uv
uv tool install git-translate-commits

# Or: plain pip
pip install git-translate-commits
```

For LLM-based translation (optional):

```bash
pipx install "git-translate-commits[llm]"
# or: pip install "git-translate-commits[llm]"
```

For best rewrite performance, also install [git-filter-repo](https://github.com/newren/git-filter-repo):

```bash
pip install git-filter-repo
```

## Quick Start

```bash
# Preview changes (offline, no API key needed)
git-translate-commits --lang en --dry-run

# Translate all commits on current branch to English (offline)
git-translate-commits --lang en

# Translate all branches to Brazilian Portuguese
git-translate-commits --lang pt-BR --all-branches

# Use LLM for higher quality (requires API key)
export OPENAI_API_KEY="sk-..."
git-translate-commits --lang en --engine llm
```

## Translation Engines

### Local (default) -- `--engine local`

Uses [Argos Translate](https://github.com/argosopentech/argos-translate), an offline neural machine translation engine based on OpenNMT. Language packs (~50MB each) are downloaded automatically on first use.

- **No API key required**
- **No cost**
- **Fully offline** after first download
- Good quality for common language pairs

### LLM -- `--engine llm`

Uses LLM APIs (OpenAI, Anthropic, or any OpenAI-compatible provider) for contextual translation via [litellm](https://github.com/BerriAI/litellm). Requires `pip install "git-translate-commits[llm]"`.

- **Higher quality** contextual translations
- **Batch processing** to minimize API calls and cost
- A 1,000-commit repo costs ~$0.05 with `gpt-4o-mini`

## Usage

```
git-translate-commits [OPTIONS]
```

### Required

| Option | Description |
|--------|-------------|
| `--lang`, `-l` | Target language code (`en`, `pt-BR`, `es`, `fr`, `de`, `ja`, ...) |

### Engine

| Option | Default | Description |
|--------|---------|-------------|
| `--engine`, `-e` | `local` | Translation engine: `local` (offline) or `llm` (API-based) |

### Filtering

| Option | Description |
|--------|-------------|
| `--all-branches` | Process all local branches |
| `--branch`, `-b` | Specific branch(es) to process (repeatable) |
| `--author` | Filter commits by author email |
| `--since` | Only commits after this date |
| `--until` | Only commits before this date |

### LLM Configuration (only with `--engine llm`)

| Option | Default | Description |
|--------|---------|-------------|
| `--provider`, `-p` | `openai` | LLM provider (`openai`, `anthropic`, `openai-compatible`) |
| `--model`, `-m` | `gpt-4o-mini` | Model to use |
| `--api-key` | env var | API key (prefer `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` env vars) |
| `--api-base-url` | — | Base URL for OpenAI-compatible providers |
| `--batch-size` | `20` | Messages per LLM request |

### Behavior

| Option | Default | Description |
|--------|---------|-------------|
| `--dry-run`, `-n` | `false` | Preview changes without modifying anything |
| `--skip-already-translated` | `true` | Skip messages already in target language |
| `--backup` | `true` | Create backup branch before rewriting |
| `--preserve-conventional` | `true` | Preserve Conventional Commit prefixes |
| `--force`, `-f` | `false` | Skip confirmation prompt |
| `--verbose`, `-v` | `false` | Show detailed logs |

### Environment Variables

```bash
# Engine and language
export GIT_TRANSLATE_ENGINE="local"   # or "llm"
export GIT_TRANSLATE_LANG="en"

# LLM-only settings
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GIT_TRANSLATE_PROVIDER="openai"
export GIT_TRANSLATE_MODEL="gpt-4o-mini"
```

## Examples

```bash
# Offline translation (default) — no API key needed
git-translate-commits --lang en

# Translate commits by a specific author
git-translate-commits --lang en --author "dev@example.com"

# Translate commits from the last year
git-translate-commits --lang en --since "2025-01-01"

# Use LLM engine for better contextual quality
git-translate-commits --lang en --engine llm

# Use Anthropic Claude via LLM engine
git-translate-commits --lang en --engine llm --provider anthropic --model claude-sonnet-4-20250514

# Use a local OpenAI-compatible server (e.g. Ollama) via LLM engine
git-translate-commits --lang en --engine llm \
  --provider openai-compatible \
  --api-base-url http://localhost:11434/v1 \
  --model llama3

# Skip confirmation and backup
git-translate-commits --lang en --force --no-backup
```

## What Gets Preserved

- **File contents** — no code is touched
- **Author/committer** — name, email, timestamps
- **Conventional Commit prefixes** — `feat:`, `fix:`, `chore:`, etc.
- **Issue references** — `#123`, `JIRA-456`
- **Git trailers** — `Co-authored-by`, `Signed-off-by`, etc.

## ⚠️ Important Notes

- **Commit hashes will change.** This is unavoidable since the message is part of the SHA hash. Coordinate with your team before force-pushing.
- A **backup branch** is created automatically before any changes (disable with `--no-backup`).
- A **log file** (`.git-translate-log.json`) is written with the full mapping of changes.
- **Local engine is free**. LLM engine costs ~$0.05 per 1,000 commits with `gpt-4o-mini`.

## Contributing

Contributions are welcome! Please read the [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

- [Report a Bug](https://github.com/paladini/git-translate-commits/issues/new?template=bug_report.md)
- [Request a Feature](https://github.com/paladini/git-translate-commits/issues/new?template=feature_request.md)

## Development

```bash
git clone https://github.com/paladini/git-translate-commits.git
cd git-translate-commits
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full development guidelines.

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE) -- see the [LICENSE](LICENSE) file for details.

## Author

Created and maintained by [Fernando Paladini](https://github.com/paladini).
