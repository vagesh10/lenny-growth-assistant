from pathlib import Path

import yaml


def parse_transcript(file_path: Path) -> dict:
    content = file_path.read_text(encoding="utf-8")

    if not content.startswith("---"):
        raise ValueError(f"Missing YAML frontmatter: {file_path}")

    parts = content.split("---", 2)

    if len(parts) != 3:
        raise ValueError(f"Invalid transcript format: {file_path}")

    frontmatter = yaml.safe_load(parts[1]) or {}
    transcript = parts[2].strip()

    return {
        "guest_name": frontmatter.get("guest"),
        "episode_title": frontmatter.get("title"),
        "transcript": transcript,
    }