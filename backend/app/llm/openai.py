from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.config import settings
from app.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key
        )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0,
        )

        return response.choices[0].message.content or ""

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0,
            stream=True,
        )

        async for chunk in stream:
            token = chunk.choices[0].delta.content

            if token:
                yield token