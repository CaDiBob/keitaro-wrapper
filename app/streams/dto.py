from dataclasses import dataclass, field


@dataclass
class OfferShare:
    offer_id: int
    name: str
    share: int


@dataclass
class StreamData:
    keitaro_id: int
    name: str
    position: int
    has_offers: bool
    offers: list[OfferShare] = field(default_factory=list)
