from app.config import settings
from app.llm.base import LLMProvider
from app.llm.ollama import OllamaProvider
from app.llm.openai import OpenAIProvider


def get_llm_provider(provider: str | None = None) -> LLMProvider:
    selected_provider = provider or settings.default_llm_provider

    if selected_provider == "ollama":
        return OllamaProvider()

    if selected_provider == "openai":
        return OpenAIProvider()

    raise ValueError(
        f"Unsupported LLM provider: {selected_provider}"
    )