from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db_models import Message, Session
from app.models.schemas import SessionCreate, SessionResponse


router = APIRouter(
    prefix="/api/sessions",
    tags=["Sessions"],
)


@router.post("", response_model=SessionResponse)
async def create_session(
    request: SessionCreate,
    db: AsyncSession = Depends(get_db),
):
    session = Session(title=request.title)

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return session


@router.get("/{session_id}")
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    message_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )

    messages = message_result.scalars().all()

    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "sources": message.sources,
                "created_at": message.created_at,
            }
            for message in messages
        ],
    }