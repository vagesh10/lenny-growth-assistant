import pytest

from app.rag.retriever import retrieve_chunks


@pytest.mark.asyncio
async def test_retrieval_behaviour(db):
    # Relevant query should retrieve transcript chunks.
    results = await retrieve_chunks(
        "How can I improve product onboarding?",
        db,
        top_k=5,
        similarity_threshold=0.50,
    )

    assert len(results) > 0
    assert any(
        "onboarding" in result["content"].lower()
        for result in results
    )

    # Empty query should return immediately.
    results = await retrieve_chunks(
        "",
        db,
        top_k=5,
        similarity_threshold=0.50,
    )

    assert results == []

    # Out-of-domain query should not return strong matches.
    results = await retrieve_chunks(
        "What is the capital of France?",
        db,
        top_k=5,
        similarity_threshold=0.50,
    )

    assert results == []