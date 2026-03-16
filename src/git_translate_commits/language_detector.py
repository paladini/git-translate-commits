# SPDX-FileCopyrightText: 2026 Fernando Paladini
# SPDX-License-Identifier: GPL-3.0-or-later

"""Module for detecting the language of commit messages."""

from __future__ import annotations

import re

from langdetect import detect, LangDetectException


CONVENTIONAL_PREFIXES = re.compile(
    r"^(feat|fix|chore|docs|refactor|test|ci|build|perf|style|revert|merge)(\(.+?\))?[!]?:\s*",
    re.IGNORECASE,
)

TRAILER_PATTERN = re.compile(
    r"^(Co-authored-by|Signed-off-by|Reviewed-by|Acked-by|Tested-by|Reported-by|Fixes|Closes|Refs):\s",
    re.IGNORECASE | re.MULTILINE,
)

ISSUE_REF_PATTERN = re.compile(r"(#\d+|[A-Z]+-\d+)")

VERSION_PATTERN = re.compile(r"^(v?\d+\.\d+(\.\d+)?|bump|release|merge|revert)\b", re.IGNORECASE)


def strip_non_translatable(message: str) -> str:
    """Remove conventional commit prefixes, trailers, and issue refs to get translatable text."""
    text = CONVENTIONAL_PREFIXES.sub("", message)
    text = TRAILER_PATTERN.sub("", text)
    text = ISSUE_REF_PATTERN.sub("", text)
    return text.strip()


def is_neutral_message(message: str) -> bool:
    """Check if a message is too short or purely technical to need translation."""
    cleaned = strip_non_translatable(message)
    words = cleaned.split()
    if len(words) < 3:
        return True
    if VERSION_PATTERN.match(cleaned):
        return True
    return False


def detect_language(message: str) -> str | None:
    """Detect the language of a commit message.

    Returns the ISO 639-1 language code (e.g. 'en', 'pt', 'es') or None if detection fails.
    """
    cleaned = strip_non_translatable(message)
    if not cleaned or len(cleaned.split()) < 2:
        return None

    try:
        return detect(cleaned)
    except LangDetectException:
        return None


def needs_translation(message: str, target_lang: str, skip_already_translated: bool = True) -> bool:
    """Determine if a commit message needs translation.

    Args:
        message: The commit message to check.
        target_lang: Target language code (e.g. 'en', 'pt').
        skip_already_translated: If True, skip messages already in target language.

    Returns:
        True if the message should be translated.
    """
    if is_neutral_message(message):
        return False

    if not skip_already_translated:
        return True

    detected = detect_language(message)
    if detected is None:
        return False

    target_base = target_lang.split("-")[0].lower()
    detected_base = detected.split("-")[0].lower()

    return detected_base != target_base
