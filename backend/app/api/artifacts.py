from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db_models import Artifact, Message, Session
from app.models.schemas import ArtifactCreate, ArtifactResponse
from app.rag.artifact import generate_artifact
from app.rag.ship30 import generate_ship30


router = APIRouter(
    prefix="/api/artifacts",
    tags=["Artifacts"],
)


@router.post(
    "",
    response_model=ArtifactResponse,
)
async def create_artifact(
    request: ArtifactCreate,
    db: AsyncSession = Depends(get_db),
):
    # Check session exists
    result = await db.execute(
        select(Session).where(
            Session.id == request.session_id
        )
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    # Save user's artifact request
    user_message = Message(
        session_id=request.session_id,
        role="user",
        content=request.prompt,
    )

    db.add(user_message)

    await db.commit()

    # Generate artifact using RAG + selected LLM
    result = await generate_artifact(
        request=request.prompt,
        db=db,
        provider=request.provider,
        artifact_type=request.artifact_type,
    )

    # Save assistant message
    assistant_message = Message(
        session_id=request.session_id,
        role="assistant",
        content=result["content"],
        sources=result["sources"],
    )

    db.add(assistant_message)

    await db.commit()

    await db.refresh(assistant_message)

    # Save generated artifact
    artifact = Artifact(
        message_id=assistant_message.id,
        artifact_type=request.artifact_type,
        content=result["content"],
    )

    db.add(artifact)

    await db.commit()

    await db.refresh(artifact)

    return ArtifactResponse(
        artifact_id=artifact.id,
        message_id=assistant_message.id,
        artifact_type=artifact.artifact_type,
        content=artifact.content,
        sources=result["sources"],
    )
@router.post("/ship30", response_model=ArtifactResponse)
async def create_ship30(
    request: ArtifactCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(Session.id == request.session_id)
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    user_message = Message(
        session_id=request.session_id,
        role="user",
        content=request.prompt,
    )

    db.add(user_message)
    await db.commit()

    result = await generate_ship30(
        request=request.prompt,
        db=db,
        provider=request.provider,
    )

    assistant_message = Message(
        session_id=request.session_id,
        role="assistant",
        content=result["content"],
        sources=result["sources"],
    )

    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)

    artifact = Artifact(
        message_id=assistant_message.id,
        artifact_type="markdown",
        content=result["content"],
    )

    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)

    return ArtifactResponse(
        artifact_id=artifact.id,
        message_id=assistant_message.id,
        artifact_type="markdown",
        content=artifact.content,
        sources=result["sources"],
    )