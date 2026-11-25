from typing import Optional

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Stream(Base):

    __tablename__ = "streams"

    id: Mapped[int] = mapped_column(primary_key=True)
    keitaro_id: Mapped[int] = mapped_column(unique=True)
    campaign_id: Mapped[int] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(String(255))
    position: Mapped[int]
    has_offers: Mapped[bool]

    offers: Mapped[list["StreamOffer"]] = relationship(
        back_populates="stream",
        cascade="all, delete-orphan",
        order_by="StreamOffer.id",
    )

    @property
    def is_dirty(self) -> bool:
        for offer in self.offers:
            if offer.removed != (offer.keitaro_share is None):
                return True
            if not offer.removed and offer.share != offer.keitaro_share:
                return True
        return False


class StreamOffer(Base):

    __tablename__ = "stream_offers"
    __table_args__ = (
        UniqueConstraint("stream_id", "offer_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    stream_id: Mapped[int] = mapped_column(
        ForeignKey("streams.id", ondelete="CASCADE"),
        index=True,
    )
    offer_id: Mapped[int]
    name: Mapped[str] = mapped_column(String(255))
    share: Mapped[int]
    keitaro_share: Mapped[Optional[int]]
    pinned: Mapped[bool] = mapped_column(default=False)
    removed: Mapped[bool] = mapped_column(default=False)
    is_new: Mapped[bool] = mapped_column(default=False)

    stream: Mapped["Stream"] = relationship(back_populates="offers")
