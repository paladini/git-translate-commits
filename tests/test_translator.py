"""Tests for the translator module."""

import json
import pytest
from unittest.mock import MagicMock, patch

from git_translate_commits.translator import (
    LLMTranslator,
    Translator,
    _build_batch_user_prompt,
    _build_system_prompt,
    _parse_llm_response,
)
from git_translate_commits.translator_base import get_language_name


class TestGetLanguageName:
    def test_known_language(self):
        assert get_language_name("en") == "English"
        assert get_language_name("pt-BR") == "Brazilian Portuguese"

    def test_unknown_language(self):
        assert get_language_name("xx") == "xx"


class TestBuildSystemPrompt:
    def test_includes_language_name(self):
        prompt = _build_system_prompt("en", preserve_conventional=True)
        assert "English" in prompt

    def test_includes_conventional_commit_rule(self):
        prompt = _build_system_prompt("en", preserve_conventional=True)
        assert "Conventional Commit" in prompt

    def test_excludes_conventional_commit_rule_when_disabled(self):
        prompt = _build_system_prompt("en", preserve_conventional=False)
        assert "Conventional Commit" not in prompt


class TestBuildBatchUserPrompt:
    def test_includes_all_messages(self):
        messages = ["msg one", "msg two", "msg three"]
        prompt = _build_batch_user_prompt(messages, "en")
        assert "msg one" in prompt
        assert "msg two" in prompt
        assert "msg three" in prompt
        assert "3 git commit messages" in prompt

    def test_numbers_messages(self):
        messages = ["first", "second"]
        prompt = _build_batch_user_prompt(messages, "en")
        assert '1. """first"""' in prompt
        assert '2. """second"""' in prompt


class TestParseLlmResponse:
    def test_valid_json_array(self):
        response = '["translated one", "translated two"]'
        result = _parse_llm_response(response, 2)
        assert result == ["translated one", "translated two"]

    def test_json_with_markdown_wrapping(self):
        response = '```json\n["translated one", "translated two"]\n```'
        result = _parse_llm_response(response, 2)
        assert result == ["translated one", "translated two"]

    def test_wrong_count_raises(self):
        response = '["only one"]'
        with pytest.raises(ValueError):
            _parse_llm_response(response, 2)

    def test_invalid_json_raises(self):
        response = "not json at all"
        with pytest.raises(ValueError):
            _parse_llm_response(response, 1)


class TestTranslator:
    @patch("git_translate_commits.translator.litellm")
    def test_translate_batch_success(self, mock_litellm):
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='["Add login", "Fix bug"]'))
        ]
        mock_response.usage = MagicMock(total_tokens=100)
        mock_litellm.completion.return_value = mock_response

        translator = Translator(target_lang="en", provider="openai", model="gpt-4o-mini")
        result = translator.translate_batch(["Adiciona login", "Corrige bug"])

        assert result == ["Add login", "Fix bug"]
        assert translator.total_tokens_used == 100

    @patch("git_translate_commits.translator.litellm")
    def test_translate_batch_retries_on_failure(self, mock_litellm):
        mock_litellm.completion.side_effect = [
            Exception("rate limited"),
            MagicMock(
                choices=[MagicMock(message=MagicMock(content='["Add login"]'))],
                usage=MagicMock(total_tokens=50),
            ),
        ]

        translator = Translator(target_lang="en", provider="openai", model="gpt-4o-mini")
        result = translator.translate_batch(["Adiciona login"])

        assert result == ["Add login"]
        assert mock_litellm.completion.call_count == 2

    def test_estimate_tokens(self):
        translator = Translator(target_lang="en", provider="openai", model="gpt-4o-mini")
        messages = ["Short message"] * 10
        tokens = translator.estimate_tokens(messages)
        assert tokens > 0
