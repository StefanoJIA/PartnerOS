from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    body: str


class NoteUpdate(BaseModel):
    body: str


class NoteOut(BaseModel):
    id: UUID
    object_type: str
    object_id: UUID
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TagCreate(BaseModel):
    name: str
    color: str | None = None


class TagOut(BaseModel):
    id: UUID
    name: str
    color: str | None = None

    model_config = {"from_attributes": True}


class ObjectTagOut(BaseModel):
    """Tag attachment row for an object."""

    object_tag_id: UUID
    tag: TagOut


class ObjectTagBody(BaseModel):
    tag_id: UUID


class ActivityOut(BaseModel):
    id: UUID
    object_type: str
    object_id: UUID
    action: str
    diff: dict | None = None
    actor_id: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FileAttachBody(BaseModel):
    object_type: str = Field(..., description="Also set via URL path when attaching after upload")
    object_id: UUID
    purpose: str | None = None


class FileOut(BaseModel):
    id: UUID
    original_filename: str
    mime: str | None
    size: int

    model_config = {"from_attributes": True}


class FileAttachmentOut(BaseModel):
    id: UUID
    file_id: UUID
    purpose: str | None
    file: FileOut

    model_config = {"from_attributes": True}


class InteractionFilterParams(BaseModel):
    channel: str | None = None
    interaction_type: str | None = None
