import asyncio

from app.llm.ollama import OllamaProvider


async def main():
    provider = OllamaProvider()

    system_prompt = "You are a helpful assistant."

    user_prompt = "Explain product onboarding in 3 short sentences."

    print()
    print("=" * 60)
    print("OLLAMA STREAM")
    print("=" * 60)
    print()

    async for token in provider.generate_stream(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    ):
        print(token, end="", flush=True)

    print()
    print()
    print("=" * 60)
    print("STREAM COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())