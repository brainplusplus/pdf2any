"""Tests for the FormatRegistry."""

from __future__ import annotations

import pytest

from pdf2any.registry import FormatRegistry, create_default_registry


class TestFormatRegistry:
    """Tests for the registry."""

    def test_register_and_get(self):
        registry = FormatRegistry()
        registry.register_output("test", object, binary=False, description="Test format")
        info = registry.get("test")
        assert info.name == "test"
        assert info.binary is False

    def test_get_unknown_raises(self):
        registry = FormatRegistry()
        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_is_registered(self):
        registry = FormatRegistry()
        registry.register_output("test", object)
        assert registry.is_registered("test")
        assert not registry.is_registered("nope")

    def test_is_binary(self):
        registry = FormatRegistry()
        registry.register_output("txt", object, binary=False)
        registry.register_output("png", object, binary=True)
        assert registry.is_binary("txt") is False
        assert registry.is_binary("png") is True

    def test_list_outputs(self):
        registry = FormatRegistry()
        registry.register_output("b", object)
        registry.register_output("a", object)
        registry.register_output("c", object)
        names = registry.output_names()
        assert names == ["a", "b", "c"]

    def test_register_input(self):
        registry = FormatRegistry()
        registry.register_input("pdf")
        assert "pdf" in registry.list_inputs()


class TestDefaultRegistry:
    """Tests for the default registry with all built-in formats."""

    def test_default_registry_has_all_formats(self):
        registry = create_default_registry()
        names = registry.output_names()
        expected = {"markdown", "html", "prosemirror", "json", "txt", "docx", "png", "jpg"}
        assert set(names) == expected

    def test_binary_formats(self):
        registry = create_default_registry()
        assert registry.is_binary("docx")
        assert registry.is_binary("png")
        assert registry.is_binary("jpg")

    def test_text_formats_not_binary(self):
        registry = create_default_registry()
        for fmt in ("markdown", "html", "prosemirror", "json", "txt"):
            assert not registry.is_binary(fmt), f"{fmt} should not be binary"

    def test_default_registry_has_pdf_input(self):
        registry = create_default_registry()
        assert "pdf" in registry.list_inputs()
