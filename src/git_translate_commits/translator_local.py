# SPDX-FileCopyrightText: 2026 Fernando Paladini
# SPDX-License-Identifier: GPL-3.0-or-later

"""Local translation backend using Argos Translate (offline, no API key needed)."""

from __future__ import annotations

import re

from .language_detector import CONVENTIONAL_PREFIXES, TRAILER_PATTERN
from .translator_base import BaseTranslator, get_language_name


# Argos Translate uses ISO 639-1 codes. Map our codes to theirs.
ARGOS_LANG_MAP = {
    "pt-BR": "pt",
    "pt-PT": "pt",
    "zh-TW": "zh",
}


def _to_argos_code(lang: str) -> str:
    """Convert our language code to an Argos Translate compatible code."""
    return ARGOS_LANG_MAP.get(lang, lang.split("-")[0].lower())


def _ensure_package_installed(from_code: str, to_code: str) -> None:
    """Download and install the Argos Translate package for the given language pair if missing."""
    import argostranslate.package
    import argostranslate.translate

    installed = argostranslate.translate.get_installed_languages()
    installed_codes = {lang.code for lang in installed}

    if from_code in installed_codes and to_code in installed_codes:
        # Check if the actual translation pair exists
        from_lang = next((l for l in installed if l.code == from_code), None)
        if from_lang:
            translations = from_lang.get_translation(
                next((l for l in installed if l.code == to_code), None)
            )
            if translations:
                return

    # Need to download
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()
    pkg = next(
        (
            p
            for p in available
            if p.from_code == from_code and p.to_code == to_code
        ),
        None,
    )
    if pkg is None:
        raise RuntimeError(
            f"No Argos Translate package available for {from_code} → {to_code}. "
            f"Available pairs: {[(p.from_code, p.to_code) for p in available[:20]]}..."
        )
    pkg.install()


class LocalTranslator(BaseTranslator):
    """Translates commit messages using Argos Translate (fully offline)."""

    def __init__(
        self,
        target_lang: str,
        preserve_conventional: bool = True,
        batch_size: int = 50,
        verbose: bool = False,
    ) -> None:
        super().__init__(
            target_lang=target_lang,
            preserve_conventional=preserve_conventional,
            batch_size=batch_size,
            verbose=verbose,
        )
        self._target_code = _to_argos_code(target_lang)
        self._installed_pairs: set[tuple[str, str]] = set()

    def _get_translation_fn(self, from_code: str, to_code: str):
        """Get the argos translate function for a language pair, installing if needed."""
        import argostranslate.translate

        pair = (from_code, to_code)
        if pair not in self._installed_pairs:
            _ensure_package_installed(from_code, to_code)
            self._installed_pairs.add(pair)

        installed = argostranslate.translate.get_installed_languages()
        from_lang = next((l for l in installed if l.code == from_code), None)
        to_lang = next((l for l in installed if l.code == to_code), None)

        if from_lang is None or to_lang is None:
            raise RuntimeError(
                f"Language not found after installation: {from_code} → {to_code}"
            )

        translation = from_lang.get_translation(to_lang)
        if translation is None:
            raise RuntimeError(
                f"Translation pair not available: {from_code} → {to_code}"
            )
        return translation

    def _translate_single(self, message: str, source_lang: str | None = None) -> str:
        """Translate a single commit message, preserving structure."""
        from_code = _to_argos_code(source_lang) if source_lang else "auto"

        # If we can't determine source, try auto-detect via argos
        if from_code == "auto" or from_code == "unknown":
            from_code = self._detect_source_language(message)

        if from_code == self._target_code:
            return message

        translation_fn = self._get_translation_fn(from_code, self._target_code)

        # Extract and preserve conventional commit prefix
        prefix = ""
        text_to_translate = message
        if self.preserve_conventional:
            match = CONVENTIONAL_PREFIXES.match(message)
            if match:
                prefix = match.group(0)
                text_to_translate = message[len(prefix):]

        # Extract and preserve trailers
        lines = text_to_translate.split("\n")
        body_lines: list[str] = []
        trailer_lines: list[str] = []
        in_trailers = False

        for line in reversed(lines):
            if not in_trailers and TRAILER_PATTERN.match(line):
                in_trailers = True
                trailer_lines.insert(0, line)
            elif in_trailers and (TRAILER_PATTERN.match(line) or line.strip() == ""):
                trailer_lines.insert(0, line)
            else:
                in_trailers = False
                body_lines = lines[: len(lines) - len(trailer_lines)]
                break

        if not body_lines:
            body_lines = lines
            trailer_lines = []

        translatable_text = "\n".join(body_lines)

        # Translate the main text
        translated = translation_fn.translate(translatable_text)

        # Reassemble
        result = prefix + translated
        if trailer_lines:
            result = result.rstrip() + "\n\n" + "\n".join(trailer_lines)

        return result

    def _detect_source_language(self, message: str) -> str:
        """Detect source language using langdetect (already a dependency)."""
        from .language_detector import detect_language

        detected = detect_language(message)
        return _to_argos_code(detected) if detected else "en"

    def translate_batch(self, messages: list[str]) -> list[str]:
        """Translate a batch of messages one by one (Argos doesn't batch natively)."""
        results: list[str] = []
        for msg in messages:
            try:
                translated = self._translate_single(msg)
                results.append(translated)
            except Exception as e:
                if self.verbose:
                    print(f"  Warning: translation failed, keeping original: {e}")
                results.append(msg)
        return results

    def estimate_tokens(self, messages: list[str]) -> int:
        """Local translation has no token cost. Return 0."""
        return 0
