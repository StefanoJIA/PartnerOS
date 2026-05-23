from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AIOutputOut(BaseModel):
    id: UUID
    task_type: str
    output_text: str | None
    user_edited_text: str | None
    status: str
    model: str | None

    model_config = {"from_attributes": True}


class AIOutputUpdate(BaseModel):
    user_edited_text: str | None = None
    status: str | None = None


class GenericAIRequest(BaseModel):
    context: dict[str, Any] = Field(default_factory=dict)
    input_object_type: str | None = None
    input_object_id: UUID | None = None
