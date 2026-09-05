from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.factory import get_llm_provider
from app.models.db_models import Message
from app.rag.prompt import build_system_prompt, build_user_prompt
from app.rag.retriever import retrieve_chunks


FALLBACK_ANSWER = (
    "I do not have sufficient information in "
    "Lenny's podcast archive to answer this."
)


def build_conversation_context(
    messages: list[Message],
    max_messages: int = 6,
) -> str:
    """
    Build recent conversation history for follow-up questions.

    Conversation history is used only to understand references
    and follow-ups. Transcript chunks remain the source of truth
    for factual claims.
    """

    recent_messages = messages[-max_messages:]

    if not recent_messages:
        return "No previous conversation."

    parts = []

    for message in recent_messages:
        role = (
            "User"
            if message.role == "user"
            else "Lenny Assistant"
        )

        parts.append(
            f"{role}: {message.content}"
        )

    return "\n".join(parts)


async def get_conversation_history(
    session_id: UUID,
    db: AsyncSession,
    max_messages: int = 6,
) -> list[Message]:
    """
    Retrieve recent messages from the current session.
    """

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(max_messages)
    )

    messages = list(result.scalars().all())

    messages.reverse()

    return messages


def build_retrieval_query(
    question: str,
    messages: list[Message],
) -> str:
    """
    Expand short follow-up questions with recent user context.

    Example:

    Previous:
        What does Lenny say about onboarding?

    Current:
        What about activation?

    Retrieval query:
        What does Lenny say about onboarding?
        What about activation?
    """

    if not messages:
        return question

    recent_user_messages = [
        message.content
        for message in messages
        if message.role == "user"
    ][-2:]

    if not recent_user_messages:
        return question

    return "\n".join(
        recent_user_messages + [question]
    )


def build_context(chunks: list[dict]) -> str:
    """
    Build clearly separated transcript context for the LLM.
    """

    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"""
SOURCE S{index}

Guest: {chunk["guest_name"] or "Unknown Guest"}
Timestamp: {chunk["timestamp"] or "Not available"}
Episode: {chunk["episode_title"]}

Transcript:
{chunk["content"]}

END SOURCE S{index}
"""
        )

    return "\n".join(context_parts)


def build_sources(chunks: list[dict]) -> list[dict]:
    """
    Convert retrieved chunks into API-safe source metadata.
    """

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


def build_grounded_system_prompt(
    transcript_context: str,
    conversation_context: str,
) -> str:
    """
    Combine transcript evidence with recent conversation context.

    Transcript context is the only source allowed for factual
    claims. Conversation history is only used to understand
    references such as "that", "it", or "what about activation?".
    """

    base_prompt = build_system_prompt(
        transcript_context
    )

    return f"""
{base_prompt}

RECENT CONVERSATION:

{conversation_context}

FOLLOW-UP CONTEXT RULES:

- Use the recent conversation only to resolve references in the
  current question, such as "what about activation?", "what about
  that?", or "tell me more".
- The recent conversation is NOT a source of factual evidence.
- Never use the conversation itself as evidence in the answer.
- Never say that the user asked a question, that the assistant
  answered a question, or that something was mentioned in the
  conversation as evidence.
- Do not treat previous assistant responses as authoritative.
- Do not repeat factual claims from previous assistant messages
  unless they are supported by the retrieved transcript sources.
- Always ground factual claims in the retrieved transcript
  sources.
- If the retrieved transcript sources do not contain enough
  information to answer the current question, use the fallback
  response instead of guessing.
"""


def build_grounded_user_prompt(
    question: str,
    conversation_context: str,
) -> str:
    """
    Build a user prompt that makes the current question explicit
    while preserving recent conversation context.
    """

    base_prompt = build_user_prompt(question)

    return f"""
{base_prompt}

The recent conversation is included below to help understand
follow-up references.

RECENT CONVERSATION:

{conversation_context}

Answer the CURRENT USER QUESTION, not an earlier question.
"""


def parse_structured_answer(
    raw_answer: str,
    chunks: list[dict],
) -> str:
    """
    Clean the LLM response.

    Sources are returned separately by the API, so they are not
    appended to the answer text.
    """

    answer = raw_answer.strip()

    if not answer:
        return FALLBACK_ANSWER

    if answer == FALLBACK_ANSWER:
        return FALLBACK_ANSWER

    return answer


async def answer_question(
    question: str,
    db: AsyncSession,
    provider: str | None = None,
    session_id: UUID | None = None,
):
    """
    Generate a complete grounded answer with session context.
    """

    conversation_context = "No previous conversation."
    retrieval_query = question

    if session_id:
        history = await get_conversation_history(
            session_id,
            db,
            max_messages=6,
        )

        conversation_context = build_conversation_context(
            history
        )

        retrieval_query = build_retrieval_query(
            question,
            history,
        )

    chunks = await retrieve_chunks(
        retrieval_query,
        db,
        top_k=10,
        similarity_threshold=0.50,
    )

    if not chunks:
        return {
            "answer": FALLBACK_ANSWER,
            "sources": [],
        }

    context = build_context(chunks)

    system_prompt = build_grounded_system_prompt(
        transcript_context=context,
        conversation_context=conversation_context,
    )

    user_prompt = build_grounded_user_prompt(
        question=question,
        conversation_context=conversation_context,
    )

    llm = get_llm_provider(provider)

    raw_answer = await llm.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    answer = parse_structured_answer(
        raw_answer,
        chunks,
    )

    return {
        "answer": answer,
        "sources": build_sources(chunks),
    }


async def answer_question_stream(
    question: str,
    db: AsyncSession,
    provider: str | None = None,
    session_id: UUID | None = None,
) -> AsyncIterator[dict]:
    """
    Generate a grounded answer using streaming and recent
    session context.

    Tokens are streamed immediately. The final answer is
    returned separately with trusted source metadata.
    """

    conversation_context = "No previous conversation."
    retrieval_query = question

    if session_id:
        history = await get_conversation_history(
            session_id,
            db,
            max_messages=6,
        )

        conversation_context = build_conversation_context(
            history
        )

        retrieval_query = build_retrieval_query(
            question,
            history,
        )

    chunks = await retrieve_chunks(
        retrieval_query,
        db,
        top_k=5,
        similarity_threshold=0.50,
    )

    if not chunks:
        yield {
            "token": FALLBACK_ANSWER,
            "sources": [],
            "done": True,
            "answer": FALLBACK_ANSWER,
        }
        return

    context = build_context(chunks)

    system_prompt = build_grounded_system_prompt(
        transcript_context=context,
        conversation_context=conversation_context,
    )

    user_prompt = build_grounded_user_prompt(
        question=question,
        conversation_context=conversation_context,
    )

    llm = get_llm_provider(provider)

    sources = build_sources(chunks)

    full_answer = ""

    async for token in llm.generate_stream(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    ):
        full_answer += token

        yield {
            "token": token,
            "sources": sources,
            "done": False,
        }

    formatted_answer = parse_structured_answer(
        full_answer,
        chunks,
    )

    yield {
        "token": "",
        "sources": sources,
        "done": True,
        "answer": formatted_answer,
    }