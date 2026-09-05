import asyncio

from app.llm.openai import OpenAIProvider


async def main():
    provider = OpenAIProvider()

    response = await provider.generate(
        system_prompt="You are a helpful assistant.",
        user_prompt="Say hello in one short sentence.",
    )

    print("OPENAI RESPONSE:")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())