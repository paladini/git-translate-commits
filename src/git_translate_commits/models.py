# SPDX-FileCopyrightText: 2026 Fernando Paladini
# SPDX-License-Identifier: GPL-3.0-or-later

"""Data models used across the application."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENAI_COMPATIBLE = "openai-compatible"


@dataclass
class CommitInfo:
    """Represents a git commit with its metadata."""

    hash: str
    subject: str
    body: str
    author_name: str
    author_email: str
    author_date: str
    committer_name: str
    committer_email: str
    committer_date: str
    branch: str

    @property
    def full_message(self) -> str:
        if self.body:
            return f"{self.subject}\n\n{self.body}"
        return self.subject


@dataclass
class TranslationResult:
    """Result of translating a single commit message."""

    original_hash: str
    original_message: str
    translated_message: str
    detected_language: str
    was_translated: bool
    skip_reason: str | None = None


@dataclass
class RewriteReport:
    """Final report of the rewrite operation."""

    target_language: str
    branches_processed: list[str]
    total_commits_scanned: int
    already_in_target_language: int
    translated_count: int
    skipped_neutral: int
    translations: list[TranslationResult] = field(default_factory=list)
    backup_branch: str | None = None
    estimated_tokens: int = 0
    elapsed_seconds: float = 0.0

    @property
    def estimated_cost_usd(self) -> float:
        input_cost = (self.estimated_tokens * 0.15) / 1_000_000
        output_cost = (self.estimated_tokens * 0.5 * 0.60) / 1_000_000
        return input_cost + output_cost


@dataclass
class Config:
    """Runtime configuration assembled from CLI flags + env vars."""

    lang: str
    engine: str = "local"
    all_branches: bool = False
    branches: list[str] = field(default_factory=list)
    author: str | None = None
    since: str | None = None
    until: str | None = None
    dry_run: bool = False
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: str | None = None
    api_base_url: str | None = None
    batch_size: int = 20
    skip_already_translated: bool = True
    backup: bool = True
    verbose: bool = False
    preserve_conventional: bool = True
    force: bool = False
    repo_path: str = "."
