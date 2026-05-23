from uuid import UUID

from pydantic import BaseModel


class MarketItemCreate(BaseModel):
    title: str
    source_type: str
    source_url: str | None = None
    related_company_id: UUID | None = None
    related_product_category: str | None = None
    market_segment: str | None = None
    content: str | None = None
    tags: str | None = None
    importance: str | None = None


class MarketItemUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    tags: str | None = None
    importance: str | None = None
    ai_summary: str | None = None
    ai_opportunity_analysis: str | None = None


class MarketItemOut(BaseModel):
    id: UUID
    title: str
    source_type: str

    model_config = {"from_attributes": True}
