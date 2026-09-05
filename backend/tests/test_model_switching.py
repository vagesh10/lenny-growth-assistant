from unittest.mock import patch

from app.llm.factory import get_llm_provider
from app.llm.ollama import OllamaProvider
from app.llm.openai import OpenAIProvider


def test_default_provider_is_ollama():
    with patch(
        "app.llm.factory.settings.default_llm_provider",
        "ollama",
    ):
        provider = get_llm_provider()

        assert isinstance(provider, OllamaProvider)


def test_ollama_provider_selection():
    provider = get_llm_provider("ollama")

    assert isinstance(provider, OllamaProvider)


def test_openai_provider_selection():
    provider = get_llm_provider("openai")

    assert isinstance(provider, OpenAIProvider)


def test_invalid_provider():
    try:
        get_llm_provider("invalid")
        assert False
    except ValueError:
        assert True