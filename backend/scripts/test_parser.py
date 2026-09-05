from pathlib import Path

from app.rag.parser import parse_transcript


PROJECT_ROOT = Path(__file__).resolve().parents[2]

transcript_path = next(
    (PROJECT_ROOT / "data" / "lenny-transcripts" / "episodes").rglob(
        "transcript.md"
    )
)

episode = parse_transcript(transcript_path)

print("Guest:", episode["guest_name"])
print("Title:", episode["episode_title"])
print("Transcript length:", len(episode["transcript"]))
print()
print("First 500 characters:")
print(episode["transcript"][:500])