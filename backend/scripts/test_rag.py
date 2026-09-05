import asyncio

from app.database import AsyncSessionLocal
from app.llm.factory import get_llm_provider
from app.rag.prompt import build_system_prompt, build_user_prompt
from app.rag.retriever import retrieve_chunks


async def main():
    question = "How can I improve product onboarding?"

    async with AsyncSessionLocal() as db:

        # 1. Retrieve relevant transcript chunks
        chunks = await retrieve_chunks(
            question,
            db,
            top_k=5,
            similarity_threshold=0.55,
        )

        print("\n" + "=" * 70)
        print("RETRIEVED CHUNKS")
        print("=" * 70)

        for i, chunk in enumerate(chunks, start=1):
            print(f"\nSOURCE S{i}")
            print("Guest:", chunk["guest_name"])
            print("Episode:", chunk["episode_title"])
            print("Timestamp:", chunk["timestamp"])
            print("Similarity:", chunk["similarity"])
            print("Content:")
            print(chunk["content"][:500])

        # 2. Build context exactly like the RAG service
        context_parts = []

        for i, chunk in enumerate(chunks, start=1):
            context_parts.append(
                f"""
SOURCE S{i}

Guest: {chunk["guest_name"] or "Unknown Guest"}
Timestamp: {chunk["timestamp"] or "Not available"}
Episode: {chunk["episode_title"]}

Transcript:
{chunk["content"]}

END SOURCE S{i}
"""
            )

        context = "\n".join(context_parts)

        # 3. Build prompts
        system_prompt = build_system_prompt(context)
        user_prompt = build_user_prompt(question)

        # 4. Call Ollama directly
        llm = get_llm_provider("ollama")

        raw_answer = await llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        # 5. IMPORTANT: print raw Ollama response
        print("\n" + "=" * 70)
        print("RAW OLLAMA RESPONSE")
        print("=" * 70)

        print(raw_answer)

        print("\n" + "=" * 70)
        print("END RAW RESPONSE")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())