import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.factory import get_llm_provider
from app.rag.retriever import retrieve_chunks


FALLBACK_ARTIFACT = (
    "I do not have sufficient information in "
    "Lenny's podcast archive to create this artifact."
)


def build_artifact_context(chunks: list[dict]) -> str:
    parts = []

    for index, chunk in enumerate(chunks, start=1):
        parts.append(
            f"""
SOURCE S{index}

Guest: {chunk["guest_name"] or "Unknown Guest"}
Episode: {chunk["episode_title"]}
Timestamp: {chunk["timestamp"] or "Not available"}

Transcript:
{chunk["content"]}

END SOURCE S{index}
"""
        )

    return "\n".join(parts)


def build_artifact_type_instructions(
    artifact_type: str,
) -> str:
    """
    Tell the model exactly what format to generate.
    """

    if artifact_type == "html":
        return """
ARTIFACT FORMAT: HTML

Return ONLY a complete HTML document.

Requirements:

- Start with <!DOCTYPE html>
- Include <html>, <head>, and <body>
- Return valid HTML only
- Do NOT use Markdown
- Do NOT wrap the response in ```html
- Do NOT include explanations before or after the HTML
- Do NOT include external scripts
- Do NOT include external resources
- Keep JavaScript minimal or avoid it entirely
"""

    if artifact_type == "css":
        return """
ARTIFACT FORMAT: CSS

Return ONLY valid CSS.

Requirements:

- Return CSS only
- Do NOT generate HTML
- Do NOT generate JavaScript
- Do NOT use Markdown
- Do NOT wrap the response in ```css
- Do NOT include explanations
- Do NOT include <style> tags
"""

    return """
ARTIFACT FORMAT: MARKDOWN

Return ONLY valid Markdown.

Requirements:

- Return Markdown only
- Do NOT wrap the response in ```markdown
- Do NOT include explanations before or after the artifact
"""


def build_artifact_system_prompt(
    context: str,
    artifact_type: str = "markdown",
) -> str:
    format_instructions = build_artifact_type_instructions(
        artifact_type
    )

    return f"""
You are Lenny Growth Assistant's artifact generation engine.

Create a practical artifact using ONLY the transcript excerpts
provided below.

STRICT GROUNDING RULES:

1. Use ONLY information supported by the transcript excerpts.

2. Do NOT use outside knowledge.

3. Do NOT invent facts, advice, examples, metrics, or strategies.

4. Do NOT invent names, companies, statistics, or quotes.

5. Keep the artifact directly related to the user's request.

6. If the transcript evidence is insufficient to create the
requested artifact, return exactly:

{FALLBACK_ARTIFACT}

{format_instructions}

30-DAY PLAN REQUIREMENTS:

If the user asks for a 30-day plan:

- The plan MUST contain exactly Day 1 through Day 30.
- Every day must be explicitly represented.
- Use headings such as "## Day 1", "## Day 2", etc.
- NEVER create Day 31 or any day after Day 30.
- NEVER use grouped ranges such as "Day 1-5".
- NEVER add a separate "Final Day" section.
- Day 30 must appear exactly once.
- Every numbered day must be between 1 and 30.
- Do not invent activities that are not supported by the transcripts.

IMPORTANT:

Do not create a Sources section inside the generated artifact.
Sources are added separately by the application.

Do not mention source IDs such as S1, S2, S3.

Keep the artifact practical, concise, and actionable.

TRANSCRIPT SOURCES:

{context}
"""


def build_artifact_user_prompt(
    request: str,
    artifact_type: str = "markdown",
) -> str:
    return f"""
Create this {artifact_type} artifact:

{request}

Return only the requested artifact.
"""


def build_sources(chunks: list[dict]) -> list[dict]:
    return [
        {
            "episode_title": chunk["episode_title"],
            "guest_name": chunk["guest_name"],
            "timestamp": chunk["timestamp"],
            "topic": chunk["topic"],
            "similarity": chunk["similarity"],
        }
        for chunk in chunks
    ]


def add_trusted_sources(
    content: str,
    chunks: list[dict],
    artifact_type: str = "markdown",
) -> str:
    """
    Add source information only to Markdown artifacts.

    HTML and CSS artifacts must remain valid in their
    respective formats, so sources are returned separately
    through the API instead.
    """

    content = content.strip()

    if not content:
        return FALLBACK_ARTIFACT

    if content == FALLBACK_ARTIFACT:
        return content

    # HTML/CSS must not have a Markdown Sources section.
    if artifact_type != "markdown":
        return content

    source_lines = []

    for chunk in chunks:
        guest = chunk["guest_name"] or "Unknown Guest"
        timestamp = chunk["timestamp"] or "Not available"

        line = f"- {guest} — {timestamp}"

        if line not in source_lines:
            source_lines.append(line)

    if source_lines:
        content += "\n\n## Sources\n\n"
        content += "\n".join(source_lines)

    return content


def is_30_day_request(request: str) -> bool:
    return bool(
        re.search(
            r"\b30[- ]day\b",
            request,
            flags=re.IGNORECASE,
        )
    )


def validate_30_day_plan(content: str) -> bool:
    """
    Validate that a 30-day plan contains exactly
    Day 1 through Day 30.

    Valid:

        ## Day 1
        ## Day 2
        ...
        ## Day 30

    Invalid:

        Day 1-5
        Day 6-10

    Invalid:

        Day 1 ... Day 29
        Final Day (Day 30)

    Invalid:

        Day 1 ... Day 30
        Day 31
    """

    day_numbers = [
        int(number)
        for number in re.findall(
            r"\bDay\s+(\d+)\b",
            content,
            flags=re.IGNORECASE,
        )
    ]

    if not day_numbers:
        return False

    # Reject Day 31, Day 32, etc.
    if any(day > 30 for day in day_numbers):
        return False

    # Exactly 30 day references.
    if len(day_numbers) != 30:
        return False

    # Every number from 1 to 30 must exist.
    if set(day_numbers) != set(range(1, 31)):
        return False

    # Every day must occur exactly once.
    for day in range(1, 31):
        if day_numbers.count(day) != 1:
            return False

    return True


def clean_generated_content(
    content: str,
    artifact_type: str,
) -> str:
    """
    Remove accidental Markdown code fences from model output.
    """

    content = content.strip()

    if artifact_type == "html":
        content = re.sub(
        r"^```(?:html)?\s*",
        "",
        content,
        flags=re.IGNORECASE,
    )

        content = re.sub(
        r"\s*```$",
        "",
        content,
    )

    elif artifact_type == "css":
        content = re.sub(
        r"^```(?:css)?\s*",
        "",
        content,
        flags=re.IGNORECASE,
    )

        content = re.sub(
        r"\s*```$",
        "",
        content,
    )
    elif artifact_type == "markdown":
        content = re.sub(
            r"^```markdown\s*",
            "",
            content,
            flags=re.IGNORECASE,
        )

        content = re.sub(
            r"\s*```$",
            "",
            content,
        )

    return content.strip()


async def generate_artifact(
    request: str,
    db: AsyncSession,
    provider: str | None = None,
    artifact_type: str = "markdown",
):
    """
    Generate a grounded artifact from transcript chunks.

    Supported artifact types:
    - markdown
    - html
    - css
    """

    if artifact_type not in {
        "markdown",
        "html",
        "css",
    }:
        artifact_type = "markdown"

    retrieval_query = (
        "product onboarding, user onboarding, onboarding flow, "
        "activation, reducing friction, customer setup, "
        "onboarding experience, product adoption"
    )

    chunks = await retrieve_chunks(
        retrieval_query,
        db,
        top_k=10,
        similarity_threshold=0.55,
    )

    if not chunks:
        return {
            "content": FALLBACK_ARTIFACT,
            "sources": [],
        }

    context = build_artifact_context(chunks)

    system_prompt = build_artifact_system_prompt(
        context=context,
        artifact_type=artifact_type,
    )

    user_prompt = build_artifact_user_prompt(
        request=request,
        artifact_type=artifact_type,
    )

    llm = get_llm_provider(provider)

    raw_content = await llm.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    raw_content = clean_generated_content(
        raw_content,
        artifact_type,
    )

    # Validate 30-day structure only for Markdown.
    if (
        artifact_type == "markdown"
        and is_30_day_request(request)
    ):
        if not validate_30_day_plan(raw_content):

            retry_prompt = f"""
The previous artifact did not satisfy the required
30-day structure.

Generate the artifact again.

STRICT REQUIREMENTS:

- Create exactly 30 individual days.
- Use exactly these headings:

## Day 1
## Day 2
## Day 3
...
## Day 30

- Every day must appear exactly once.
- Do NOT use ranges such as Day 1-5.
- Do NOT create Day 31 or any day greater than 30.
- Do NOT create a separate Final Day.
- Use ONLY information supported by the transcript sources.
- Do NOT invent unsupported strategies or facts.
- Return ONLY Markdown.
- Do NOT create a Sources section.

Previous attempt:

{raw_content}
"""

            raw_content = await llm.generate(
                system_prompt=system_prompt,
                user_prompt=retry_prompt,
            )

            raw_content = clean_generated_content(
                raw_content,
                "markdown",
            )

            # If the second attempt is still invalid,
            # fail safely instead of returning bad content.
            if not validate_30_day_plan(raw_content):
                return {
                    "content": FALLBACK_ARTIFACT,
                    "sources": build_sources(chunks),
                }

    content = add_trusted_sources(
        raw_content,
        chunks,
        artifact_type=artifact_type,
    )

    return {
        "content": content,
        "sources": build_sources(chunks),
    }