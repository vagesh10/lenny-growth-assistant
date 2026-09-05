from pathlib import Path
import asyncio

from sentence_transformers import SentenceTransformer
from sqlalchemy import select, text

from app.database import AsyncSessionLocal
from app.models.transcript import TranscriptChunk
from app.rag.parser import parse_transcript
from app.rag.chunker import (
    parse_timestamped_segments,
    chunk_segments,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRANSCRIPTS_DIR = (
    PROJECT_ROOT
    / "data"
    / "lenny-transcripts"
    / "episodes"
)

BATCH_SIZE = 32


print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Embedding model loaded.")


def get_transcript_files():
    return list(
        TRANSCRIPTS_DIR.rglob("transcript.md")
    )


def build_fallback_segments(transcript: str):
    """
    Used when a transcript has no timestamp markers.
    Treat the entire transcript as one segment.
    """
    transcript = transcript.strip()

    if not transcript:
        return []

    return [
        {
            "timestamp": None,
            "text": transcript,
        }
    ]


async def episode_exists(
    db,
    episode_title,
    guest_name,
):
    result = await db.execute(
        select(TranscriptChunk.id)
        .where(
            TranscriptChunk.episode_title
            == (episode_title or "Unknown Episode"),
            TranscriptChunk.guest_name
            == guest_name,
        )
        .limit(1)
    )

    return result.scalar_one_or_none() is not None


async def ingest():

    transcript_files = get_transcript_files()

    print(
        f"Found {len(transcript_files)} transcript files."
    )

    if not transcript_files:
        print("No transcript files found.")
        return

    total_chunks = 0
    skipped_episodes = 0
    processed_episodes = 0

    async with AsyncSessionLocal() as db:

        # ------------------------------------------------
        # Process transcripts
        # ------------------------------------------------

        for file_path in transcript_files:

            try:
                episode = parse_transcript(
                    file_path
                )

                episode_title = (
                    episode["episode_title"]
                    or "Unknown Episode"
                )

                guest_name = episode["guest_name"]

                # ----------------------------------------
                # Check whether this episode is already
                # present in the database.
                # ----------------------------------------

                if await episode_exists(
                    db,
                    episode_title,
                    guest_name,
                ):
                    print()
                    print(
                        f"Skipping existing episode: "
                        f"{episode_title}"
                    )

                    skipped_episodes += 1
                    continue

                # ----------------------------------------
                # Parse timestamped segments
                # ----------------------------------------

                segments = parse_timestamped_segments(
                    episode["transcript"]
                )

                # ----------------------------------------
                # Fallback for transcripts without
                # timestamps
                # ----------------------------------------

                if not segments:
                    print(
                        "No timestamps found. "
                        "Using fallback parser."
                    )

                    segments = build_fallback_segments(
                        episode["transcript"]
                    )

                # ----------------------------------------
                # Create chunks
                # ----------------------------------------

                chunks = chunk_segments(
                    segments
                )

            except Exception as error:

                print(
                    f"Skipping {file_path}: {error}"
                )

                continue

            print()
            print("-" * 70)
            print(
                f"Guest: {guest_name}"
            )
            print(
                f"Title: {episode_title}"
            )
            print(
                f"Created {len(chunks)} chunks."
            )
            print("-" * 70)

            # -----------------------------------------
            # Generate embeddings in batches
            # -----------------------------------------

            episode_chunks = 0

            for batch_start in range(
                0,
                len(chunks),
                BATCH_SIZE
            ):

                batch = chunks[
                    batch_start:
                    batch_start + BATCH_SIZE
                ]

                texts = [
                    chunk["content"]
                    for chunk in batch
                ]

                embeddings = model.encode(
                    texts,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )

                # -------------------------------------
                # Insert chunks
                # -------------------------------------

                for index, (
                    chunk,
                    embedding
                ) in enumerate(
                    zip(batch, embeddings)
                ):

                    chunk_index = (
                        batch_start + index
                    )

                    transcript_chunk = TranscriptChunk(
                        episode_title=episode_title,

                        guest_name=guest_name,

                        timestamp=chunk["timestamp"],

                        topic=None,

                        chunk_index=chunk_index,

                        content=chunk["content"],

                        embedding=embedding.tolist(),
                    )

                    db.add(transcript_chunk)

                # -------------------------------------
                # Commit every batch
                # -------------------------------------

                await db.commit()

                episode_chunks += len(batch)
                total_chunks += len(batch)

            processed_episodes += 1

            print(
                f"Inserted this episode: "
                f"{episode_chunks}"
            )

            print(
                f"Inserted this run: "
                f"{total_chunks}"
            )

        # ---------------------------------------------
        # HNSW index
        # ---------------------------------------------

        print()
        print("Creating HNSW vector index...")

        await db.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS
                idx_transcript_chunks_embedding_hnsw
                ON transcript_chunks
                USING hnsw
                (embedding vector_cosine_ops);
                """
            )
        )

        await db.commit()

    print()
    print("=" * 70)
    print("INGESTION COMPLETE")
    print("=" * 70)

    print(
        f"Transcript files: "
        f"{len(transcript_files)}"
    )

    print(
        f"Processed episodes: "
        f"{processed_episodes}"
    )

    print(
        f"Skipped existing episodes: "
        f"{skipped_episodes}"
    )

    print(
        f"New chunks inserted: "
        f"{total_chunks}"
    )


if __name__ == "__main__":
    asyncio.run(ingest())