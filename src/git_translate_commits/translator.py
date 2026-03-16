# SPDX-FileCopyrightText: 2026 Fernando Paladini
# SPDX-License-Identifier: GPL-3.0-or-later

"""Module for translating commit messages via LLM using litellm."""

from __future__ import annotations

import json
import re
import time
from typing import Any

import litellm

from .translator_base import BaseTranslator, get_language_name


def _build_system_prompt(target_lang: str, preserve_conventional: bool) -> str:
    lang_name = get_language_name(target_lang)
    prompt = f"""You are a specialized translator for git commit messages. Translate commit messages to {lang_name}.

Rules:
1. Maintain the technical, concise tone of a commit message.
2. Preserve variable names, function names, class names, file names, and paths exactly as they appear.
3. Preserve issue/PR references like #123 or JIRA-456 exactly.
4. Preserve git trailers exactly as-is (Co-authored-by, Signed-off-by, Reviewed-by, etc.).
5. Do NOT add information that was not in the original message.
6. Preserve line breaks and formatting of the message body.
7. If the message has a subject and body separated by a blank line, maintain that structure.
8. If a message is already in {lang_name}, return it unchanged."""

    if preserve_conventional:
        prompt += """
9. Preserve Conventional Commit prefixes exactly (feat:, fix:, chore:, docs:, refactor:, test:, ci:, build:, perf:, style:, revert:). Only translate the text AFTER the prefix."""

    return prompt


def _build_batch_user_prompt(messages: list[str], target_lang: str) -> str:
    lang_name = get_language_name(target_lang)
    numbered = "\n".join(f'{i+1}. """{msg}"""' for i, msg in enumerate(messages))
    return f"""Translate the following {len(messages)} git commit messages to {lang_name}.
Return ONLY a valid JSON array of strings with the translations in the same order. No explanation, no markdown, just the JSON array.

Messages:
{numbered}"""


def _parse_llm_response(content: str, expected_count: int) -> list[str]:
    """Parse the LLM response, extracting a JSON array of translated strings."""
    content = content.strip()
    json_match = re.search(r"\[.*\]", content, re.DOTALL)
    if json_match:
        content = json_match.group(0)

    try:
        result = json.loads(content)
        if isinstance(result, list) and len(result) == expected_count:
            return [str(item) for item in result]
    except json.JSONDecodeError:
        pass

    raise ValueError(
        f"Failed to parse LLM response as JSON array of {expected_count} items. "
        f"Response: {content[:200]}..."
    )


class LLMTranslator(BaseTranslator):
    """Translates commit messages using an LLM provider via litellm."""

    def __init__(
        self,
        target_lang: str,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        api_base_url: str | None = None,
        preserve_conventional: bool = True,
        batch_size: int = 20,
        verbose: bool = False,
    ) -> None:
        super().__init__(
            target_lang=target_lang,
            preserve_conventional=preserve_conventional,
            batch_size=batch_size,
            verbose=verbose,
        )
        self.model = self._resolve_model(provider, model)
        self.api_key = api_key
        self.api_base_url = api_base_url

        if api_key:
            litellm.api_key = api_key
        if api_base_url:
            litellm.api_base = api_base_url

        litellm.drop_params = True

    @staticmethod
    def _resolve_model(provider: str, model: str) -> str:
        if provider == "anthropic" and not model.startswith("anthropic/"):
            return f"anthropic/{model}"
        if provider == "openai-compatible" and not model.startswith("openai/"):
            return f"openai/{model}"
        return model

    def translate_batch(self, messages: list[str], max_retries: int = 3) -> list[str]:
        """Translate a batch of messages. Returns translated messages in same order."""
        system_prompt = _build_system_prompt(self.target_lang, self.preserve_conventional)
        user_prompt = _build_batch_user_prompt(messages, self.target_lang)

        for attempt in range(max_retries):
            try:
                response = litellm.completion(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"} if "gpt" in self.model else None,
                )

                content = response.choices[0].message.content
                if response.usage:
                    self.total_tokens_used += response.usage.total_tokens

                # litellm json_object wraps in {"translations": [...]} sometimes
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict):
                        for key in ("translations", "messages", "result", "data"):
                            if key in parsed and isinstance(parsed[key], list):
                                content = json.dumps(parsed[key])
                                break
                except (json.JSONDecodeError, TypeError):
                    pass

                return _parse_llm_response(content, len(messages))

            except (ValueError, Exception) as e:
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    if self.verbose:
                        print(f"  Retry {attempt + 1}/{max_retries} after {wait}s: {e}")
                    time.sleep(wait)
                else:
                    raise

        return messages  # fallback: return originals

    def estimate_tokens(self, messages: list[str]) -> int:
        """Rough estimate of tokens for a list of messages (input + output)."""
        total_chars = sum(len(m) for m in messages)
        # ~4 chars per token, plus system prompt overhead per batch
        num_batches = max(1, len(messages) // self.batch_size + 1)
        system_overhead = num_batches * 300  # ~300 tokens for system prompt
        estimated_input = (total_chars // 4) + system_overhead
        estimated_output = total_chars // 4  # output is roughly same size
        return estimated_input + estimated_output


# Backward-compatible alias
Translator = LLMTranslator
