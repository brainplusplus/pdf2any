"""LLM-based vision OCR provider — multi-provider support.

Supported providers:
    - openai:    GPT-4o, GPT-4o-mini, o4-mini, etc.
                 Also covers OpenAI-compatible APIs (OpenRouter, Groq, vLLM, Ollama)
    - anthropic: Claude Sonnet 4, Claude Opus 4, etc.
    - gemini:    Gemini 2.5 Pro, Gemini 2.5 Flash, etc.

Requirements:
    pip install pdf2any[ocr-llm]

Environment variables:
    OPENAI_API_KEY       — for openai provider
    ANTHROPIC_API_KEY    — for anthropic provider
    GOOGLE_API_KEY       — for gemini provider (or GEMINI_API_KEY)

Usage:
    # OpenAI
    pdf2any scan.pdf -t markdown --ocr --ocr-engine llm --ocr-provider openai --ocr-model gpt-4o

    # Anthropic
    pdf2any scan.pdf -t markdown --ocr --ocr-engine llm --ocr-provider anthropic --ocr-model claude-sonnet-4-20250514

    # Gemini
    pdf2any scan.pdf -t markdown --ocr --ocr-engine llm --ocr-provider gemini --ocr-model gemini-2.5-flash

    # Custom endpoint (OpenAI-compatible: OpenRouter, Groq, Ollama)
    pdf2any scan.pdf -t markdown --ocr-force --ocr-engine llm --ocr-provider openai \
        --ocr-model qwen2-vl-72b --ocr-base-url https://openrouter.ai/api/v1
"""

from __future__ import annotations

import base64
import io
import os
import time
from typing import Any

from pdf2any.backends.ocr_provider import OCRProvider, register_provider
from pdf2any.errors import CapabilityError
from pdf2any.logging_config import get_logger

logger = get_logger("ocr.llm")

# Default models per provider
_DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-20250514",
    "gemini": "gemini-2.5-flash",
}

# Default base URLs per provider (None = use SDK default)
_DEFAULT_BASE_URLS: dict[str, str | None] = {
    "openai": None,  # https://api.openai.com/v1
    "anthropic": None,  # https://api.anthropic.com
    "gemini": None,  # https://generativelanguage.googleapis.com
}

# Env var names for API keys
_API_KEY_ENVVARS: dict[str, list[str]] = {
    "openai": ["OPENAI_API_KEY"],
    "anthropic": ["ANTHROPIC_API_KEY"],
    "gemini": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
}

# Prompt template — same for all providers
_OCR_PROMPT = """\
You are a high-accuracy OCR engine. Extract ALL text from this document page image.

Rules:
- Output ONLY the extracted text. No commentary, no markdown code fences.
- Preserve reading order (top to bottom, left to right).
- Preserve paragraph breaks (blank line between paragraphs).
- Preserve list structure (- or 1. prefixes).
- Preserve table structure using markdown table syntax (| col1 | col2 |).
- Preserve heading hierarchy (# for H1, ## for H2, etc.).
- If the image contains no text, output nothing.
- Language hint: {lang}
"""


class LLMOCRProvider(OCRProvider):
    """LLM-based vision OCR supporting OpenAI, Anthropic, and Gemini.

    Args:
        provider: 'openai', 'anthropic', or 'gemini'.
        model: Model name (e.g. 'gpt-4o'). Falls back to provider default.
        base_url: Custom API base URL (OpenAI-compatible endpoints).
        api_key: API key. Falls back to environment variable.
        concurrency: Number of parallel API calls (default: 1).
        max_retries: Max retry attempts on API failure (default: 3).
    """

    def __init__(self, **kwargs: Any) -> None:
        self._provider: str = kwargs.get("provider", "openai")
        self._model: str = kwargs.get("model") or _DEFAULT_MODELS.get(
            self._provider, ""
        )
        self._base_url: str | None = kwargs.get("base_url") or _DEFAULT_BASE_URLS.get(
            self._provider
        )
        self._api_key: str | None = kwargs.get("api_key")
        self._concurrency: int = int(kwargs.get("concurrency", 1))
        self._max_retries: int = int(kwargs.get("max_retries", 3))

        if self._provider not in _DEFAULT_MODELS:
            raise CapabilityError(
                f"Unknown LLM provider '{self._provider}'. "
                f"Supported: {', '.join(_DEFAULT_MODELS.keys())}"
            )

    @property
    def name(self) -> str:
        return "llm"

    @property
    def is_available(self) -> bool:
        """Check if the provider SDK is importable AND API key is set."""
        try:
            self._import_sdk()
        except ImportError:
            return False

        return bool(self._resolve_api_key())

    def _import_sdk(self) -> Any:
        """Import the appropriate SDK for the configured provider."""
        if self._provider == "openai":
            import openai  # type: ignore[import-untyped]
            return openai
        elif self._provider == "anthropic":
            import anthropic  # type: ignore[import-untyped]
            return anthropic
        elif self._provider == "gemini":
            import google.generativeai as genai  # type: ignore[import-untyped]
            return genai
        raise CapabilityError(f"Unknown provider: {self._provider}")

    def _resolve_api_key(self) -> str | None:
        """Resolve API key from constructor or environment."""
        if self._api_key:
            return self._api_key

        for envvar in _API_KEY_ENVVARS.get(self._provider, []):
            val = os.environ.get(envvar)
            if val:
                return val
        return None

    def recognize(self, image_data: bytes, *, lang: str = "eng") -> str:
        """Run LLM vision OCR on a PNG image.

        Args:
            image_data: PNG image bytes.
            lang: Language hint for the prompt.

        Returns:
            Recognized text string.
        """
        if not self.is_available:
            raise CapabilityError(
                f"LLM OCR ({self._provider}) is not available. "
                f"Install SDK and set API key: "
                f"{_API_KEY_ENVVARS[self._provider][0]}"
            )

        prompt = _OCR_PROMPT.format(lang=lang)
        b64_image = base64.b64encode(image_data).decode("utf-8")

        last_error: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                text = self._call_api(b64_image, prompt)
                logger.debug(
                    "LLM OCR (%s/%s): %d chars (attempt %d)",
                    self._provider,
                    self._model,
                    len(text),
                    attempt,
                )
                return text.strip()
            except Exception as e:
                last_error = e
                if attempt < self._max_retries:
                    wait = 2**attempt  # 2s, 4s, 8s
                    logger.warning(
                        "LLM OCR attempt %d failed: %s — retrying in %ds",
                        attempt,
                        e,
                        wait,
                    )
                    time.sleep(wait)

        raise CapabilityError(
            f"LLM OCR failed after {self._max_retries} attempts: {last_error}"
        ) from last_error

    def _call_api(self, b64_image: str, prompt: str) -> str:
        """Call the appropriate LLM API with the image and prompt."""
        if self._provider == "openai":
            return self._call_openai(b64_image, prompt)
        elif self._provider == "anthropic":
            return self._call_anthropic(b64_image, prompt)
        elif self._provider == "gemini":
            return self._call_gemini(b64_image, prompt)
        raise CapabilityError(f"Unknown provider: {self._provider}")

    # -----------------------------------------------------------------------
    # OpenAI (also covers OpenAI-compatible: OpenRouter, Groq, Ollama, vLLM)
    # -----------------------------------------------------------------------
    def _call_openai(self, b64_image: str, prompt: str) -> str:
        import openai  # type: ignore[import-untyped]

        api_key = self._resolve_api_key()
        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if self._base_url:
            client_kwargs["base_url"] = self._base_url
        else:
            # Check env var for base URL (OpenAI_BASE_URL)
            env_base = os.environ.get("OPENAI_BASE_URL")
            if env_base:
                client_kwargs["base_url"] = env_base

        client = openai.OpenAI(**client_kwargs)

        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_image}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=4096,
            temperature=0,
        )

        return response.choices[0].message.content or ""

    # -----------------------------------------------------------------------
    # Anthropic (Claude)
    # -----------------------------------------------------------------------
    def _call_anthropic(self, b64_image: str, prompt: str) -> str:
        import anthropic  # type: ignore[import-untyped]

        api_key = self._resolve_api_key()
        client_kwargs: dict[str, Any] = {"api_key": api_key}
        if self._base_url:
            client_kwargs["base_url"] = self._base_url

        client = anthropic.Anthropic(**client_kwargs)

        response = client.messages.create(
            model=self._model,
            max_tokens=4096,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": b64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )

        # Extract text from response
        return "".join(
            block.text
            for block in response.content
            if hasattr(block, "text")
        )

    # -----------------------------------------------------------------------
    # Google Gemini
    # -----------------------------------------------------------------------
    def _call_gemini(self, b64_image: str, prompt: str) -> str:
        import google.generativeai as genai  # type: ignore[import-untyped]
        from PIL import Image  # type: ignore[import-untyped]

        api_key = self._resolve_api_key()
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(self._model)

        # Gemini accepts PIL Image or dict with inline_data
        image = Image.open(io.BytesIO(base64.b64decode(b64_image)))

        response = model.generate_content(
            [prompt, image],
            generation_config={
                "temperature": 0,
                "max_output_tokens": 4096,
            },
        )

        return response.text or ""


register_provider("llm", LLMOCRProvider)
