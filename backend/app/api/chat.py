import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db_models import Message, Session
from app.models.schemas import ChatRequest, ChatResponse
from app.rag.service import answer_question, answer_question_stream


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    # Check that the session exists
    result = await db.execute(
        select(Session).where(Session.id == request.session_id)
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    # Save the user's message
    user_message = Message(
        session_id=request.session_id,
        role="user",
        content=request.message,
    )

    db.add(user_message)
    await db.commit()

    # Generate grounded answer with conversation context
    rag_result = await answer_question(
        request.message,
        db,
        request.provider,
        request.session_id,
    )

    # Save assistant response
    assistant_message = Message(
        session_id=request.session_id,
        role="assistant",
        content=rag_result["answer"],
        sources=rag_result["sources"],
    )

    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)

    return ChatResponse(
        message_id=assistant_message.id,
        answer=rag_result["answer"],
        sources=rag_result["sources"],
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    # Check that the session exists
    result = await db.execute(
        select(Session).where(Session.id == request.session_id)
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    # Save the user's message
    user_message = Message(
        session_id=request.session_id,
        role="user",
        content=request.message,
    )

    db.add(user_message)
    await db.commit()

    async def event_generator():
        full_answer = ""
        sources = []

        # Stream the answer from the RAG service
        # Pass session_id so follow-up questions have conversation context
        async for event in answer_question_stream(
            request.message,
            db,
            request.provider,
            request.session_id,
        ):
            # Send generated token to frontend
            if event["token"]:
                full_answer += event["token"]

                yield (
                    f"data: {json.dumps({'token': event['token']})}\n\n"
                )

            # Only save the assistant message when generation is finished
            if event["done"]:
                sources = event["sources"]
                final_answer = event.get("answer", full_answer)

                assistant_message = Message(
                    session_id=request.session_id,
                    role="assistant",
                    content=final_answer,
                    sources=sources,
                )

                db.add(assistant_message)
                await db.commit()
                await db.refresh(assistant_message)

                # Send final response metadata
                yield f"data: {json.dumps({
                    'done': True,
                    'sources': sources,
                    'message_id': str(assistant_message.id),
                })}\n\n"

                # Tell frontend the stream is completely finished
                yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )