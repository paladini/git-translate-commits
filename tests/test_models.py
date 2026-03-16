"""Tests for the data models."""

import pytest

from git_translate_commits.models import CommitInfo, RewriteReport


class TestCommitInfo:
    def test_full_message_with_body(self):
        commit = CommitInfo(
            hash="abc123",
            subject="feat: add login",
            body="Detailed description here",
            author_name="User",
            author_email="user@example.com",
            author_date="2024-01-01",
            committer_name="User",
            committer_email="user@example.com",
            committer_date="2024-01-01",
            branch="main",
        )
        assert commit.full_message == "feat: add login\n\nDetailed description here"

    def test_full_message_without_body(self):
        commit = CommitInfo(
            hash="abc123",
            subject="feat: add login",
            body="",
            author_name="User",
            author_email="user@example.com",
            author_date="2024-01-01",
            committer_name="User",
            committer_email="user@example.com",
            committer_date="2024-01-01",
            branch="main",
        )
        assert commit.full_message == "feat: add login"


class TestRewriteReport:
    def test_estimated_cost(self):
        report = RewriteReport(
            target_language="en",
            branches_processed=["main"],
            total_commits_scanned=100,
            already_in_target_language=50,
            translated_count=50,
            skipped_neutral=0,
            estimated_tokens=1_000_000,
        )
        # input: 1M * 0.15 / 1M = 0.15
        # output: 0.5M * 0.60 / 1M = 0.30
        cost = report.estimated_cost_usd
        assert cost == pytest.approx(0.45, abs=0.01)
