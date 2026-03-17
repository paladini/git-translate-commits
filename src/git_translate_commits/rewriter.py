# SPDX-FileCopyrightText: 2026 Fernando Paladini
# SPDX-License-Identifier: GPL-3.0-or-later

"""Module for rewriting git commit messages using git filter-repo or git filter-branch."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .models import TranslationResult


class RewriterError(Exception):
    pass


class GitRewriter:
    """Rewrites commit messages in a git repository."""

    def __init__(self, repo_path: str, verbose: bool = False) -> None:
        self.repo_path = Path(repo_path).resolve()
        self.verbose = verbose
        self._use_filter_repo = self._check_filter_repo()

    @staticmethod
    def _check_filter_repo() -> bool:
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

    def rewrite(self, translations: list[TranslationResult]) -> None:
        """Apply translated messages to the repository history."""
        message_map = {}
        for t in translations:
            if t.was_translated and t.translated_message != t.original_message:
                message_map[t.original_hash] = t.translated_message

        if not message_map:
            return

        if self._use_filter_repo:
            self._rewrite_with_filter_repo(message_map)
        else:
            self._rewrite_with_filter_branch(message_map)

    def _rewrite_with_filter_repo(self, message_map: dict[str, str]) -> None:
        """Rewrite using git-filter-repo with a commit callback."""
        map_file = self.repo_path / ".git" / "rewrite-map.json"
        map_file.write_text(json.dumps(message_map, ensure_ascii=False))

        try:
            # --commit-callback receives a `commit` object with .original_id
            # (original hex SHA as bytes) and .message (bytes).
            callback = (
                "import json\n"
                f"with open('{map_file}') as _f: _map = json.load(_f)\n"
                "oid = commit.original_id.decode('ascii') if commit.original_id else ''\n"
                "if oid in _map:\n"
                "    commit.message = _map[oid].encode('utf-8')\n"
            )

            cmd = [
                "git",
                "filter-repo",
                "--force",
                "--commit-callback",
                callback,
            ]

            if self.verbose:
                print(f"  Running: {' '.join(cmd[:4])} ...")

            result = subprocess.run(
                cmd,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                raise RewriterError(
                    f"git filter-repo failed (exit {result.returncode}):\n{result.stderr}"
                )
        finally:
            map_file.unlink(missing_ok=True)

    def _rewrite_with_filter_branch(self, message_map: dict[str, str]) -> None:
        """Rewrite using git filter-branch with --msg-filter."""
        # Write the message map to a temporary JSON file
        map_file = self.repo_path / ".git" / "rewrite-map.json"
        map_file.write_text(json.dumps(message_map, ensure_ascii=False, indent=2))

        # Build a msg-filter script that reads the map and replaces messages
        msg_filter = (
            f'python3 -c "\n'
            f"import sys, json, hashlib\n"
            f"msg = sys.stdin.read()\n"
            f"map_file = '{map_file}'\n"
            f"with open(map_file) as f:\n"
            f"    m = json.load(f)\n"
            f"commit_hash = '$GIT_COMMIT'\n"
            f"if commit_hash in m:\n"
            f"    sys.stdout.write(m[commit_hash])\n"
            f"else:\n"
            f"    sys.stdout.write(msg)\n"
            f'"'
        )

        # Get all branch refs to rewrite
        cmd = [
            "git",
            "filter-branch",
            "-f",
            "--msg-filter",
            msg_filter,
            "--",
            "--all",
        ]

        if self.verbose:
            print(f"  Running git filter-branch on {len(message_map)} commits...")

        result = subprocess.run(
            cmd,
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
            timeout=600,
        )

        # Clean up
        map_file.unlink(missing_ok=True)

        # filter-branch may return 0 even with warnings; check stderr for actual errors
        if result.returncode != 0 and "fatal" in result.stderr.lower():
            raise RewriterError(
                f"git filter-branch failed (exit {result.returncode}):\n{result.stderr}"
            )

        # Clean up filter-branch backup refs
        cleanup = subprocess.run(
            ["git", "for-each-ref", "--format=%(refname)", "refs/original/"],
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
        )
        for ref in cleanup.stdout.strip().split("\n"):
            if ref:
                subprocess.run(
                    ["git", "update-ref", "-d", ref],
                    cwd=str(self.repo_path),
                    capture_output=True,
                )

    def write_log(self, translations: list[TranslationResult], log_path: str | None = None) -> str:
        """Write a JSON log mapping original hashes to new messages."""
        if log_path is None:
            log_path = str(self.repo_path / ".git-translate-log.json")

        log_data = {
            "rewrites": [
                {
                    "original_hash": t.original_hash,
                    "original_message": t.original_message,
                    "translated_message": t.translated_message,
                    "detected_language": t.detected_language,
                    "was_translated": t.was_translated,
                }
                for t in translations
                if t.was_translated
            ]
        }

        Path(log_path).write_text(json.dumps(log_data, ensure_ascii=False, indent=2))
        return log_path
