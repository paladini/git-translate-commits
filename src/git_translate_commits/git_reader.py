# SPDX-FileCopyrightText: 2026 Fernando Paladini
# SPDX-License-Identifier: GPL-3.0-or-later

"""Module for reading git commit history and metadata."""

from __future__ import annotations

import subprocess
from pathlib import Path

from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError

from .models import CommitInfo


class GitReaderError(Exception):
    pass


class GitReader:
    """Reads commit history from a git repository."""

    def __init__(self, repo_path: str = ".") -> None:
        try:
            self.repo = Repo(repo_path, search_parent_directories=True)
        except (InvalidGitRepositoryError, NoSuchPathError) as e:
            raise GitReaderError(f"Not a valid git repository: {repo_path}") from e

        self.repo_path = Path(self.repo.working_dir)

    def has_uncommitted_changes(self) -> bool:
        return self.repo.is_dirty(untracked_files=True)

    def get_current_branch(self) -> str:
        try:
            return self.repo.active_branch.name
        except TypeError:
            return "HEAD"

    def get_all_local_branches(self) -> list[str]:
        return [ref.name for ref in self.repo.branches]

    def get_commits(
        self,
        branches: list[str] | None = None,
        author: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[CommitInfo]:
        """Retrieve commits from specified branches with optional filters.

        Deduplicates commits that appear in multiple branches (keeps first occurrence).
        """
        if not branches:
            branches = [self.get_current_branch()]

        seen_hashes: set[str] = set()
        commits: list[CommitInfo] = []

        for branch in branches:
            rev_args: list[str] = [branch]

            kwargs: dict = {}
            if author:
                kwargs["author"] = author
            if since:
                kwargs["since"] = since
            if until:
                kwargs["until"] = until

            try:
                for commit in self.repo.iter_commits(*rev_args, **kwargs):
                    if commit.hexsha in seen_hashes:
                        continue
                    seen_hashes.add(commit.hexsha)

                    message_lines = commit.message.strip().split("\n", 1)
                    subject = message_lines[0].strip()
                    body = message_lines[1].strip() if len(message_lines) > 1 else ""

                    commits.append(
                        CommitInfo(
                            hash=commit.hexsha,
                            subject=subject,
                            body=body,
                            author_name=commit.author.name,
                            author_email=commit.author.email,
                            author_date=str(commit.authored_datetime),
                            committer_name=commit.committer.name,
                            committer_email=commit.committer.email,
                            committer_date=str(commit.committed_datetime),
                            branch=branch,
                        )
                    )
            except Exception as e:
                raise GitReaderError(f"Failed to read commits from branch '{branch}': {e}") from e

        return commits

    def create_backup_branch(self, branch_name: str) -> str:
        """Create a backup branch pointing to the current HEAD. Returns the branch name."""
        try:
            self.repo.create_head(branch_name)
            return branch_name
        except Exception as e:
            raise GitReaderError(f"Failed to create backup branch '{branch_name}': {e}") from e

    @staticmethod
    def is_git_filter_repo_available() -> bool:
        try:
            result = subprocess.run(
                ["git", "filter-repo", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
