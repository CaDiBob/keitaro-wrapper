from pydantic import BaseModel, Field


class SKeitaroItem(BaseModel):
    id: int
    name: str


class SKeitaroCampaign(BaseModel):
    id: int
    name: str
    alias: str
    domain: str = ""


class SKeitaroCampaignCreate(BaseModel):
    name: str
    alias: str
    domain_id: int
    group_id: int
    traffic_source_id: int
    type: str = "position"
    state: str = "active"
    cost_type: str = "CPC"
    cost_auto: bool = True


class SKeitaroFilter(BaseModel):
    name: str
    mode: str
    payload: list[str]


class SKeitaroStreamOffer(BaseModel):
    offer_id: int
    share: int
    state: str = "active"


class SKeitaroStream(BaseModel):
    id: int
    campaign_id: int
    name: str
    position: int
    kind: str = Field(alias="schema")
    offers: list[SKeitaroStreamOffer] = []


class SKeitaroStreamCreate(BaseModel):
    campaign_id: int
    name: str
    position: int
    kind: str = Field(serialization_alias="schema")
    type: str = "regular"
    state: str = "active"
    collect_clicks: bool = True
    action_type: str | None = None
    action_payload: str | None = None
    filters: list[SKeitaroFilter] = []
    offers: list[SKeitaroStreamOffer] = []


class SKeitaroStreamUpdate(BaseModel):
    offers: list[SKeitaroStreamOffer]
