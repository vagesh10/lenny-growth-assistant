from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class LLMProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        pass

    @abstractmethod
    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncIterator[str]:
        pass