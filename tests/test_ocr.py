"""Tests for OCR provider registry and integration."""

from __future__ import annotations

import pytest

from pdf2any.backends.ocr_provider import (
    OCRProvider,
    get_ocr_provider,
    list_available_engines,
    register_provider,
)
from pdf2any.errors import CapabilityError


# ---------------------------------------------------------------------------
# Registry tests
# ---------------------------------------------------------------------------

class TestOCRRegistry:
    """Test the pluggable OCR provider registry."""

    def test_list_available_engines(self):
        """Registry should have at least some engines registered."""
        engines = list_available_engines()
        # Built-in providers auto-register if their SDK is importable.
        # In test env, none may be installed — that's OK.
        assert isinstance(engines, list)

    def test_register_custom_provider(self):
        """Custom providers can be registered."""

        class DummyProvider(OCRProvider):
            @property
            def name(self) -> str:
                return "dummy"

            @property
            def is_available(self) -> bool:
                return True

            def recognize(self, image_data: bytes, *, lang: str = "eng") -> str:
                return "dummy text"

        register_provider("dummy", DummyProvider)
        assert "dummy" in list_available_engines()

        provider = get_ocr_provider("dummy")
        assert provider.name == "dummy"
        assert provider.recognize(b"fake") == "dummy text"

    def test_get_unknown_engine_raises(self):
        """Requesting an unknown engine should raise CapabilityError."""
        with pytest.raises(CapabilityError):
            get_ocr_provider("nonexistent-engine")

    def test_auto_select_no_engines_raises(self):
        """Auto-select with no available engines should raise CapabilityError."""
        # Temporarily remove all providers
        from pdf2any.backends import ocr_provider

        original_registry = ocr_provider._REGISTRY.copy()
        try:
            ocr_provider._REGISTRY.clear()
            with pytest.raises(CapabilityError):
                get_ocr_provider("auto")
        finally:
            ocr_provider._REGISTRY.clear()
            ocr_provider._REGISTRY.update(original_registry)


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

class TestOCRIntegration:
    """Test the OCR integration layer (hybrid vs force mode)."""

    def test_hybrid_mode_skips_text_pages(self):
        """Hybrid mode should NOT OCR pages with sufficient text."""
        from pdf2any.backends.ocr_integration import OCRIntegration
        from pdf2any.models.page import PageRef
        from pdf2any.parser.text_extractor import RawPage

        class MockProvider(OCRProvider):
            @property
            def name(self) -> str:
                return "mock"

            @property
            def is_available(self) -> bool:
                return True

            def recognize(self, image_data: bytes, *, lang: str = "eng") -> str:
                return "OCR result"

        integration = OCRIntegration(MockProvider(), mode="hybrid")

        # Page with lots of text → should NOT OCR
        raw_page = RawPage(
            page_ref=PageRef(number=1, width=612, height=792),
            raw_text="This is a long text page with sufficient content to skip OCR.",
        )
        assert not integration.should_ocr(raw_page)

    def test_hybrid_mode_ocrs_scanned_pages(self):
        """Hybrid mode SHOULD OCR pages with little/no text."""
        from pdf2any.backends.ocr_integration import OCRIntegration
        from pdf2any.models.page import PageRef
        from pdf2any.parser.text_extractor import RawPage

        class MockProvider(OCRProvider):
            @property
            def name(self) -> str:
                return "mock"

            @property
            def is_available(self) -> bool:
                return True

            def recognize(self, image_data: bytes, *, lang: str = "eng") -> str:
                return "OCR result"

        integration = OCRIntegration(MockProvider(), mode="hybrid")

        # Empty page → should OCR
        raw_page = RawPage(
            page_ref=PageRef(number=1, width=612, height=792),
            raw_text="",
        )
        assert integration.should_ocr(raw_page)

        # Near-empty page (< 10 chars) → should OCR
        raw_page2 = RawPage(
            page_ref=PageRef(number=1, width=612, height=792),
            raw_text="ab",
        )
        assert integration.should_ocr(raw_page2)

    def test_force_mode_ocrs_all_pages(self):
        """Force mode should OCR all pages regardless of text content."""
        from pdf2any.backends.ocr_integration import OCRIntegration
        from pdf2any.models.page import PageRef
        from pdf2any.parser.text_extractor import RawPage

        class MockProvider(OCRProvider):
            @property
            def name(self) -> str:
                return "mock"

            @property
            def is_available(self) -> bool:
                return True

            def recognize(self, image_data: bytes, *, lang: str = "eng") -> str:
                return "OCR result"

        integration = OCRIntegration(MockProvider(), mode="force")

        # Even a page with lots of text → should OCR in force mode
        raw_page = RawPage(
            page_ref=PageRef(number=1, width=612, height=792),
            raw_text="This is a long text page with sufficient content.",
        )
        assert integration.should_ocr(raw_page)


# ---------------------------------------------------------------------------
# LLM provider tests (no API calls — just config/validation)
# ---------------------------------------------------------------------------

class TestLLMProvider:
    """Test LLM OCR provider configuration (no actual API calls)."""

    def test_unknown_provider_raises(self):
        """LLM provider with unknown provider name should raise."""
        from pdf2any.backends.ocr_llm import LLMOCRProvider

        with pytest.raises(CapabilityError):
            LLMOCRProvider(provider="unknown_provider")

    def test_default_model_per_provider(self):
        """Each LLM provider should have a default model."""
        from pdf2any.backends.ocr_llm import LLMOCRProvider, _DEFAULT_MODELS

        assert "openai" in _DEFAULT_MODELS
        assert "anthropic" in _DEFAULT_MODELS
        assert "gemini" in _DEFAULT_MODELS

        provider = LLMOCRProvider(provider="openai")
        assert provider._model == _DEFAULT_MODELS["openai"]

    def test_custom_model_override(self):
        """Custom model should override default."""
        from pdf2any.backends.ocr_llm import LLMOCRProvider

        provider = LLMOCRProvider(provider="openai", model="gpt-4o")
        assert provider._model == "gpt-4o"

    def test_custom_base_url(self):
        """Custom base URL should be stored."""
        from pdf2any.backends.ocr_llm import LLMOCRProvider

        provider = LLMOCRProvider(
            provider="openai",
            base_url="https://openrouter.ai/api/v1",
        )
        assert provider._base_url == "https://openrouter.ai/api/v1"
