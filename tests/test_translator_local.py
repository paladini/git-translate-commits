"""Tests for the local translator module."""

import pytest

from git_translate_commits.translator_local import (
    LocalTranslator,
    _to_argos_code,
)
from git_translate_commits.translator_base import BaseTranslator


class TestArgosCodeMapping:
    def test_maps_pt_br(self):
        assert _to_argos_code("pt-BR") == "pt"

    def test_maps_zh_tw(self):
        assert _to_argos_code("zh-TW") == "zh"

    def test_passes_simple_code(self):
        assert _to_argos_code("en") == "en"
        assert _to_argos_code("fr") == "fr"

    def test_strips_region(self):
        assert _to_argos_code("es-MX") == "es"


class TestLocalTranslatorInterface:
    def test_inherits_base_translator(self):
        assert issubclass(LocalTranslator, BaseTranslator)

    def test_estimate_tokens_is_zero(self):
        translator = LocalTranslator(target_lang="en")
        assert translator.estimate_tokens(["any message"]) == 0

    def test_default_batch_size(self):
        translator = LocalTranslator(target_lang="en")
        assert translator.batch_size == 50
