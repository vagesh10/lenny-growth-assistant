import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    title: str = "New Chat"


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    sources: list[dict] | None
    created_at: datetime


class ChatRequest(BaseModel):
    session_id: uuid.UUID
    message: str
    provider: Literal["ollama", "openai"] | None = None


class ChatResponse(BaseModel):
    message_id: uuid.UUID
    answer: str
    sources: list[dict]

class CitationAnswerItem(BaseModel):
    text: str
    source_ids: list[str]


class StructuredAnswer(BaseModel):
    answer: list[CitationAnswerItem]


class ArtifactCreate(BaseModel):
    session_id: uuid.UUID
    prompt: str
    artifact_type: Literal["markdown", "html", "css"] = "markdown"
    provider: Literal["ollama", "openai"] | None = None


class ArtifactResponse(BaseModel):
    artifact_id: uuid.UUID
    message_id: uuid.UUID
    artifact_type: str
    content: str
    sources: list[dict]