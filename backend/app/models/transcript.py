import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    episode_title: Mapped[str] = mapped_column(String(255))
    guest_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    timestamp: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    topic: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    chunk_index: Mapped[int] = mapped_column(Integer)

    content: Mapped[str] = mapped_column(Text)

    embedding: Mapped[list[float]] = mapped_column(
        Vector(384)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )