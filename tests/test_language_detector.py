"""Tests for the language detection module."""

import pytest

from git_translate_commits.language_detector import (
    detect_language,
    is_neutral_message,
    needs_translation,
    strip_non_translatable,
)


class TestStripNonTranslatable:
    def test_strips_conventional_prefix(self):
        assert strip_non_translatable("feat: add user login") == "add user login"

    def test_strips_scoped_conventional_prefix(self):
        assert strip_non_translatable("fix(auth): resolve token issue") == "resolve token issue"

    def test_strips_issue_refs(self):
        assert strip_non_translatable("fix bug in login #123") == "fix bug in login"

    def test_strips_jira_refs(self):
        assert strip_non_translatable("fix JIRA-456 login bug") == "fix  login bug"

    def test_strips_trailers(self):
        msg = "fix login\n\nCo-authored-by: User <u@e.com>"
        result = strip_non_translatable(msg)
        assert "Co-authored-by" not in result

    def test_preserves_plain_message(self):
        assert strip_non_translatable("add email validation") == "add email validation"


class TestIsNeutralMessage:
    def test_short_message_is_neutral(self):
        assert is_neutral_message("WIP") is True

    def test_version_bump_is_neutral(self):
        assert is_neutral_message("v1.2.3") is True
        assert is_neutral_message("bump version to 2.0.0") is True

    def test_merge_is_neutral(self):
        assert is_neutral_message("Merge branch 'main'") is True

    def test_normal_message_is_not_neutral(self):
        assert is_neutral_message("Adiciona validação de e-mail no formulário") is False

    def test_conventional_with_short_body_is_neutral(self):
        assert is_neutral_message("feat: WIP") is True


class TestDetectLanguage:
    def test_detects_portuguese(self):
        lang = detect_language("Adiciona validação de e-mail no formulário de cadastro")
        assert lang == "pt"

    def test_detects_english(self):
        lang = detect_language("Add email validation to the registration form")
        assert lang == "en"

    def test_returns_none_for_short_message(self):
        lang = detect_language("WIP")
        assert lang is None

    def test_returns_none_for_empty(self):
        lang = detect_language("")
        assert lang is None


class TestNeedsTranslation:
    def test_portuguese_needs_english_translation(self):
        assert needs_translation(
            "Adiciona validação de e-mail no formulário de cadastro", "en"
        ) is True

    def test_english_does_not_need_english_translation(self):
        assert needs_translation(
            "Add email validation to the registration form", "en"
        ) is False

    def test_neutral_message_does_not_need_translation(self):
        assert needs_translation("v1.2.3", "en") is False

    def test_skip_already_translated_false(self):
        result = needs_translation(
            "Add email validation to the registration form",
            "en",
            skip_already_translated=False,
        )
        assert result is True
