import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.factory import get_llm_provider
from app.rag.retriever import retrieve_chunks


FALLBACK_SHIP30 = (
    "I do not have sufficient information in "
    "Lenny's podcast archive to create this Ship 30 plan."
)


def build_ship30_context(chunks: list[dict]) -> str:
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


def build_ship30_system_prompt(context: str) -> str:
    return f"""
You are the Ship 30 growth planning engine for Lenny Growth Assistant.

Your job is to create a practical 30-day growth plan using the
transcript evidence provided below.

GROUNDING RULES:

- Use only ideas supported by the transcript sources.
- Do not invent facts, statistics, quotes, companies, people,
  or unsupported strategies.
- You may turn supported ideas into practical actions.
- Do not claim that Lenny or a guest said something unless the
  transcript supports it.
- Keep each day short and actionable.
- Do not discuss the generation process.

OUTPUT FORMAT:

You MUST produce exactly 30 sections.

Each section MUST use this exact heading format:

## Day 1

Then one or two short bullet points.

Then:

## Day 2

Then one or two short bullet points.

Continue sequentially through:

## Day 30

IMPORTANT:

- Day numbers must be sequential from 1 to 30.
- Every number from 1 through 30 must appear exactly once.
- Never combine days.
- Never write "Days 1-5".
- Never write "Day 1-5".
- Never create Day 31.
- Never create "Final Day".
- Never use ### headings.
- Never use code fences.
- Do not add a title before Day 1.
- Do not add a Sources section.
- Do not mention source IDs.
- Return Markdown only.

Each day should contain a small practical growth action
derived from the supplied transcript evidence.

If the evidence is limited, reuse supported themes in different
practical ways rather than inventing new facts.

Do NOT return the fallback merely because the transcripts do not
describe thirty separate activities. You should derive thirty
practical actions from the supported ideas.

TRANSCRIPT SOURCES:

{context}
"""


def validate_ship30(content: str) -> bool:
    # Reject grouped ranges such as "Days 1-5"
    if re.search(
        r"\bDays?\s+\d+\s*[-–]\s*\d+\b",
        content,
        flags=re.IGNORECASE,
    ):
        return False

    # Reject "Final Day"
    if re.search(
        r"\bFinal\s+Day\b",
        content,
        flags=re.IGNORECASE,
    ):
        return False

    # Require exactly 30 Markdown headings: ## Day N
    headings = re.findall(
        r"^##\s+Day\s+(\d+)\s*$",
        content,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    if len(headings) != 30:
        return False

    day_numbers = [int(number) for number in headings]

    # Require exactly Day 1 through Day 30.
    if set(day_numbers) != set(range(1, 31)):
        return False

    # Every day must appear exactly once.
    for day in range(1, 31):
        if day_numbers.count(day) != 1:
            return False

    return True


def clean_ship30(content: str) -> str:
    content = content.strip()

    # Remove Markdown code fences if the model adds them.
    content = re.sub(
        r"^```(?:markdown)?\s*",
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


async def generate_ship30(
    request: str,
    db: AsyncSession,
    provider: str | None = None,
):
    """
    Generate a grounded 30-day growth plan.

    Retrieval is intentionally broad because Ship 30 is a
    synthesis task rather than a single-question retrieval task.
    """

    retrieval_query = (
        "growth product growth onboarding activation retention "
        "customer acquisition product strategy experimentation "
        "user growth product-led growth teams startups"
    )

    chunks = await retrieve_chunks(
        retrieval_query,
        db,
        top_k=10,
        similarity_threshold=0.50,
    )

    if not chunks:
        return {
            "content": FALLBACK_SHIP30,
            "sources": [],
        }

    context = build_ship30_context(chunks)

    system_prompt = build_ship30_system_prompt(context)

    user_prompt = f"""
Create a 30-day Ship 30 growth plan for this request:

{request}

Remember:

- Exactly 30 sections.
- Start with ## Day 1.
- End with ## Day 30.
- One or two short bullet points per day.
- Never group days.
- Markdown only.
"""

    llm = get_llm_provider(provider)

    content = await llm.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    content = clean_ship30(content)

    # Retry once if the model fails the required structure.
    if not validate_ship30(content):
        retry_prompt = f"""
Generate the Ship 30 plan again.

The previous output was invalid.

Previous output:

{content}

STRICT REQUIREMENTS:

## Day 1
- One short practical action.

## Day 2
- One short practical action.

Continue exactly like this through:

## Day 30
- One short practical action.

Rules:

- Exactly 30 headings.
- Exactly one heading for every day 1 through 30.
- No missing days.
- No duplicate days.
- No grouped ranges.
- No Day 31.
- No Final Day.
- No title.
- No Sources section.
- No code fences.
- Markdown only.
- Use only ideas supported by the supplied transcript context.
"""

        content = await llm.generate(
            system_prompt=system_prompt,
            user_prompt=retry_prompt,
        )

        content = clean_ship30(content)

    # Never return an invalid plan.
    if not validate_ship30(content):
        return {
            "content": FALLBACK_SHIP30,
            "sources": build_sources(chunks),
        }

    return {
        "content": content,
        "sources": build_sources(chunks),
    }