import json
from collections.abc import AsyncIterator

import httpx

from app.config import settings
from app.llm.base import LLMProvider


class OllamaProvider(LLMProvider):

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        payload = {
            "model": settings.ollama_model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": 0,
            },
        }

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json=payload,
            )

        response.raise_for_status()

        data = response.json()

        return data.get("response", "").strip()

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncIterator[str]:

        payload = {
            "model": settings.ollama_model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": True,
            "options": {
                "temperature": 0,
            },
        }

        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{settings.ollama_base_url}/api/generate",
                json=payload,
            ) as response:

                response.raise_for_status()

                async for line in response.aiter_lines():

                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    token = data.get("response", "")

                    if token:
                        yield token

                    if data.get("done", False):
                        break