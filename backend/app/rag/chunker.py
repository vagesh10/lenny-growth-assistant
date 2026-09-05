import re

from transformers import AutoTokenizer


TIMESTAMP_PATTERN = re.compile(r"\((\d{2}:\d{2}:\d{2})\):")

TOKENIZER = AutoTokenizer.from_pretrained(
    "sentence-transformers/all-MiniLM-L6-v2"
)


def parse_timestamped_segments(transcript: str):
    matches = list(TIMESTAMP_PATTERN.finditer(transcript))

    segments = []

    for index, match in enumerate(matches):
        timestamp = match.group(1)

        start = match.end()

        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(transcript)
        )

        text = transcript[start:end].strip()

        if text:
            segments.append(
                {
                    "timestamp": timestamp,
                    "text": text,
                }
            )

    return segments


def chunk_segments(
    segments,
    chunk_size=500,
    overlap=100,
):
    """
    Create 500-token chunks with 100-token overlap.

    Tokenization is performed incrementally so we never pass an
    oversized sequence to the embedding model's tokenizer.
    """

    chunks = []

    current_token_ids = []
    current_timestamp = None

    for segment in segments:

        segment_token_ids = TOKENIZER.encode(
            segment["text"],
            add_special_tokens=False,
        )

        if not current_token_ids:
            current_timestamp = segment["timestamp"]

        current_token_ids.extend(segment_token_ids)

        while len(current_token_ids) >= chunk_size:

            chunk_token_ids = current_token_ids[:chunk_size]

            chunk_text = TOKENIZER.decode(
                chunk_token_ids,
                skip_special_tokens=True,
            )

            chunks.append(
                {
                    "timestamp": current_timestamp,
                    "content": chunk_text.strip(),
                }
            )

            # Keep the last 100 tokens as overlap.
            current_token_ids = current_token_ids[
                chunk_size - overlap:
            ]

            current_timestamp = segment["timestamp"]

    if current_token_ids:
        chunk_text = TOKENIZER.decode(
            current_token_ids,
            skip_special_tokens=True,
        )

        if chunk_text.strip():
            chunks.append(
                {
                    "timestamp": current_timestamp,
                    "content": chunk_text.strip(),
                }
            )

    return chunks