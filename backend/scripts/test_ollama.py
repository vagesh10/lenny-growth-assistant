import asyncio

from app.llm.ollama import OllamaProvider


async def main():

    provider = OllamaProvider()

    answer = await provider.generate(
        system_prompt="You are a helpful assistant.",
        user_prompt="Explain product onboarding in 2 sentences.",
    )

    print()
    print("=" * 60)
    print("OLLAMA RESPONSE")
    print("=" * 60)
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())