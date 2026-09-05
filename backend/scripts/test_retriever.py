import asyncio

from app.database import AsyncSessionLocal
from app.rag.retriever import retrieve_chunks


async def main():

    question = "How can I improve product onboarding?"

    async with AsyncSessionLocal() as db:

        results = await retrieve_chunks(
            question,
            db,
            top_k=5
        )

    print()
    print("=" * 70)
    print("QUESTION")
    print("=" * 70)
    print(question)

    print()
    print("=" * 70)
    print("RETRIEVED CHUNKS")
    print("=" * 70)

    if not results:
        print("No relevant information found.")
        return

    for index, result in enumerate(results, start=1):

        print()
        print(f"RESULT {index}")
        print("-" * 70)

        print("Guest:", result["guest_name"])
        print("Episode:", result["episode_title"])
        print("Similarity:", result["similarity"])
        print("Chunk:", result["chunk_index"])

        print()
        print(result["content"][:1000])


if __name__ == "__main__":
    asyncio.run(main())