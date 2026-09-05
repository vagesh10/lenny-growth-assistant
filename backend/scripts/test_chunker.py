from pathlib import Path

from app.rag.parser import parse_transcript
from app.rag.chunker import (
    parse_timestamped_segments,
    chunk_segments,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

transcript_path = next(
    (
        PROJECT_ROOT
        / "data"
        / "lenny-transcripts"
        / "episodes"
    ).rglob("transcript.md")
)


episode = parse_transcript(transcript_path)

segments = parse_timestamped_segments(
    episode["transcript"]
)

chunks = chunk_segments(segments)


print("=" * 70)
print("EPISODE")
print("=" * 70)

print("Guest:", episode["guest_name"])
print("Title:", episode["episode_title"])

print()
print("Segments:", len(segments))
print("Chunks:", len(chunks))

print()
print("=" * 70)
print("FIRST 3 CHUNKS")
print("=" * 70)

for index, chunk in enumerate(chunks[:3]):

    print()
    print(f"CHUNK {index}")
    print("Timestamp:", chunk["timestamp"])
    print("Word count:", len(chunk["content"].split()))

    print()
    print(chunk["content"][:500])