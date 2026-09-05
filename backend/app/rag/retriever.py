from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transcript import TranscriptChunk


embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


async def retrieve_chunks(
    query: str,
    db: AsyncSession,
    top_k: int = 5,
    similarity_threshold: float = 0.50,
):
    # Return immediately for an empty query.
    # This avoids unnecessary embedding generation and database calls.
    if not query.strip():
        return []

    # Convert the user's query into an embedding.
    query_embedding = embedding_model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    # Calculate cosine distance between the query
    # and every transcript chunk.
    distance = TranscriptChunk.embedding.cosine_distance(
        query_embedding
    )

    # Retrieve the closest 10 chunks first.
    result = await db.execute(
        select(
            TranscriptChunk,
            distance.label("distance"),
        )
        .order_by(distance)
        .limit(10)
    )

    rows = result.all()

    # Extract meaningful words from the query.
    # Words shorter than 4 characters are ignored.
    query_words = {
        word.lower()
        for word in query.split()
        if len(word) >= 4
    }

    candidates = []

    for chunk, distance_value in rows:
        # Cosine similarity = 1 - cosine distance
        similarity = 1 - distance_value

        # Ignore weak semantic matches.
        if similarity < similarity_threshold:
            continue

        content_lower = chunk.content.lower()

        # Count how many query words appear in the transcript.
        keyword_matches = sum(
            1
            for word in query_words
            if word in content_lower
        )

        # Give a small bonus to chunks containing query keywords.
        keyword_bonus = min(
            keyword_matches * 0.01,
            0.05,
        )

        # Combine semantic similarity + keyword relevance.
        reranked_score = similarity + keyword_bonus

        candidates.append(
            {
                "chunk": chunk,
                "similarity": similarity,
                "reranked_score": reranked_score,
            }
        )

    # Highest reranked score first.
    candidates.sort(
        key=lambda item: item["reranked_score"],
        reverse=True,
    )

    results = []
    seen_chunks = set()

    for candidate in candidates:
        chunk = candidate["chunk"]

        # Avoid returning duplicate chunks from the same episode.
        chunk_key = (
            chunk.episode_title,
            chunk.chunk_index,
        )

        if chunk_key in seen_chunks:
            continue

        seen_chunks.add(chunk_key)

        results.append(
            {
                "id": str(chunk.id),
                "episode_title": chunk.episode_title,
                "guest_name": chunk.guest_name,
                "timestamp": chunk.timestamp,
                "topic": chunk.topic,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "similarity": round(
                    candidate["similarity"],
                    4,
                ),
            }
        )

        # Stop once we have enough results.
        if len(results) >= top_k:
            break

    return results