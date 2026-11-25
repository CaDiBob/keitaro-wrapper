import re

from pydantic import BaseModel, Field, field_validator, model_validator


class SStreamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    countries: list[str] = []
    redirect_url: str | None = None
    offer_ids: list[int] = []

    @field_validator("countries", mode="before")
    @classmethod
    def split_countries(cls, value):
        if isinstance(value, str):
            value = re.split(r"[,;\s]+", value)
        codes = [str(code).strip().upper() for code in value]
        codes = list(dict.fromkeys(code for code in codes if code))
        for code in codes:
            if not re.fullmatch(r"[A-Z]{2}", code):
                raise ValueError(f"неверный гео-код: {code}")
        return codes

    @model_validator(mode="after")
    def check_target(self):
        if bool(self.redirect_url) == bool(self.offer_ids):
            raise ValueError("укажите либо redirect_url, либо offer_ids")
        return self


class SOfferAdd(BaseModel):
    offer_id: int


class SOfferPin(BaseModel):
    pinned: bool


class SStreamOffer(BaseModel):
    offer_id: int
    name: str
    share: int
    pinned: bool
    removed: bool

    class Config:
        from_attributes = True


class SStream(BaseModel):
    id: int
    keitaro_id: int
    name: str
    position: int
    has_offers: bool
    is_dirty: bool
    offers: list[SStreamOffer]

    class Config:
        from_attributes = True
