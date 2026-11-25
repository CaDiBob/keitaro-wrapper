from datetime import datetime

from pydantic import BaseModel, Field

from app.streams.schemas import SStreamCreate


class SCampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    streams: list[SStreamCreate] = Field(min_length=1)


class SCampaign(BaseModel):
    id: int
    name: str
    alias: str
    url: str


class SCampaignShort(BaseModel):
    id: int
    name: str
    alias: str


class SCreatedCampaign(BaseModel):
    id: int
    keitaro_id: int
    name: str
    alias: str
    url: str
    created_at: datetime
