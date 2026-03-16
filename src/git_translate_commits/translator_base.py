# SPDX-FileCopyrightText: 2026 Fernando Paladini
# SPDX-License-Identifier: GPL-3.0-or-later

"""Base translator interface and shared logic for translate_commits."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from .models import CommitInfo, TranslationResult


LANGUAGE_NAMES = {
    "en": "English",
    "pt": "Brazilian Portuguese",
    "pt-BR": "Brazilian Portuguese",
    "pt-PT": "European Portuguese",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "ru": "Russian",
    "nl": "Dutch",
    "pl": "Polish",
    "tr": "Turkish",
    "ar": "Arabic",
    "hi": "Hindi",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
    "uk": "Ukrainian",
    "cs": "Czech",
    "ro": "Romanian",
    "hu": "Hungarian",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "ms": "Malay",
}


def get_language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)


class BaseTranslator(ABC):
    """Abstract base class for translation backends."""

    def __init__(
        self,
        target_lang: str,
        preserve_conventional: bool = True,
        batch_size: int = 20,
        verbose: bool = False,
    ) -> None:
        self.target_lang = target_lang
        self.preserve_conventional = preserve_conventional
        self.batch_size = batch_size
        self.verbose = verbose
        self.total_tokens_used = 0

    @abstractmethod
    def translate_batch(self, messages: list[str]) -> list[str]:
        """Translate a batch of messages. Returns translated messages in same order."""
        ...

    def estimate_tokens(self, messages: list[str]) -> int:
        """Rough estimate of tokens. Override in LLM backend for accurate counts."""
        total_chars = sum(len(m) for m in messages)
        return total_chars // 4

    def translate_commits(
        self,
        commits: list[CommitInfo],
        needs_translation_flags: list[bool],
        detected_languages: list[str | None],
    ) -> list[TranslationResult]:
        """Translate commit messages that need translation, batching them for efficiency."""
        results: list[TranslationResult] = []

        to_translate_indices: list[int] = []
        to_translate_messages: list[str] = []

        for i, (commit, needs_it, detected_lang) in enumerate(
            zip(commits, needs_translation_flags, detected_languages)
        ):
            if needs_it:
                to_translate_indices.append(i)
                to_translate_messages.append(commit.full_message)
            else:
                skip_reason = "already in target language"
                if detected_lang is None:
                    skip_reason = "neutral/untranslatable message"
                results.append(
                    TranslationResult(
                        original_hash=commit.hash,
                        original_message=commit.full_message,
                        translated_message=commit.full_message,
                        detected_language=detected_lang or "unknown",
                        was_translated=False,
                        skip_reason=skip_reason,
                    )
                )

        # Process in batches
        translated_messages: list[str] = []
        for batch_start in range(0, len(to_translate_messages), self.batch_size):
            batch = to_translate_messages[batch_start : batch_start + self.batch_size]
            translated_batch = self.translate_batch(batch)
            translated_messages.extend(translated_batch)

        # Build results for translated commits
        translated_results: list[TranslationResult] = []
        for idx, translated_msg in zip(to_translate_indices, translated_messages):
            commit = commits[idx]
            detected_lang = detected_languages[idx]
            translated_results.append(
                TranslationResult(
                    original_hash=commit.hash,
                    original_message=commit.full_message,
                    translated_message=translated_msg,
                    detected_language=detected_lang or "unknown",
                    was_translated=True,
                )
            )

        # Merge results in original order
        all_results: list[TranslationResult] = [None] * len(commits)  # type: ignore
        skip_idx = 0
        translate_idx = 0
        for i in range(len(commits)):
            if i in to_translate_indices:
                all_results[i] = translated_results[translate_idx]
                translate_idx += 1
            else:
                all_results[i] = results[skip_idx]
                skip_idx += 1

        return all_results
