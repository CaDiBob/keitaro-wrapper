from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session_maker
from app.dao.base import BaseDAO
from app.exceptions import StreamNotFoundException
from app.streams.dto import StreamData
from app.streams.models import Stream, StreamOffer


class StreamDAO(BaseDAO):
    model = Stream

    @classmethod
    async def find_by_campaign(cls, campaign_id: int) -> list[Stream]:
        async with async_session_maker() as session:
            query = (
                select(Stream)
                .filter_by(campaign_id=campaign_id)
                .options(selectinload(Stream.offers))
                .order_by(Stream.position)
            )
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def find_with_offers(cls, stream_id: int) -> Stream:
        async with async_session_maker() as session:
            stream = await session.get(
                Stream,
                stream_id,
                options=[selectinload(Stream.offers)],
            )
            if stream is None:
                raise StreamNotFoundException
            return stream

    @classmethod
    async def change(cls, stream_id: int, action, *args) -> Stream:
        async with async_session_maker.begin() as session:
            stream = await session.get(
                Stream,
                stream_id,
                options=[selectinload(Stream.offers)],
            )
            if stream is None:
                raise StreamNotFoundException
            action(stream, *args)
        return stream

    @classmethod
    async def sync(
        cls,
        campaign_id: int,
        streams_data: list[StreamData],
    ) -> list[Stream]:
        async with async_session_maker.begin() as session:
            query = (
                select(Stream)
                .filter_by(campaign_id=campaign_id)
                .options(selectinload(Stream.offers))
            )
            result = await session.execute(query)
            streams = {s.keitaro_id: s for s in result.scalars()}

            for data in streams_data:
                stream = streams.pop(data.keitaro_id, None)
                if stream is None:
                    stream = Stream(
                        keitaro_id=data.keitaro_id,
                        campaign_id=campaign_id,
                        offers=[],
                    )
                    session.add(stream)
                stream.name = data.name
                stream.position = data.position
                stream.has_offers = data.has_offers

                keitaro_offers = {o.offer_id: o for o in data.offers}
                for offer in list(stream.offers):
                    keitaro_offer = keitaro_offers.pop(offer.offer_id, None)
                    if keitaro_offer is None and offer.is_new:
                        stream.offers.remove(offer)
                        continue
                    offer.is_new = False
                    if keitaro_offer is None:
                        offer.share = 0
                        offer.keitaro_share = None
                        offer.removed = True
                        offer.pinned = False
                    else:
                        offer.share = keitaro_offer.share
                        offer.keitaro_share = keitaro_offer.share
                        offer.removed = False
                for keitaro_offer in keitaro_offers.values():
                    stream.offers.append(StreamOffer(
                        offer_id=keitaro_offer.offer_id,
                        name=keitaro_offer.name,
                        share=keitaro_offer.share,
                        keitaro_share=keitaro_offer.share,
                    ))

            for stream in streams.values():
                await session.delete(stream)
        return await cls.find_by_campaign(campaign_id)
