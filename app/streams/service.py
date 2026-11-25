from app.logger import logger
from app.http_client import keitaro_client
from app.exceptions import (
    LastOfferException,
    OfferNotInStreamException,
    StreamHasNoOffersException,
    OfferAlreadyInStreamException,
)
from app.keitaro_schemas import (
    SKeitaroFilter,
    SKeitaroStream,
    SKeitaroStreamOffer,
    SKeitaroStreamCreate,
    SKeitaroStreamUpdate,
)
from app.streams.dao import StreamDAO
from app.streams.dto import StreamData, OfferShare
from app.streams.shares import rebalance, split_evenly
from app.streams.models import Stream, StreamOffer
from app.streams.schemas import SStreamCreate


async def create_stream(
    campaign_id: int,
    position: int,
    data: SStreamCreate,
) -> SKeitaroStream:
    stream = SKeitaroStreamCreate(
        campaign_id=campaign_id,
        name=data.name,
        position=position,
        kind="redirect" if data.redirect_url else "landings",
    )
    if data.countries:
        stream.filters = [
            SKeitaroFilter(
                name="country",
                mode="accept",
                payload=data.countries,
            ),
        ]
    if data.redirect_url:
        stream.action_type = "http"
        stream.action_payload = data.redirect_url
    else:
        shares = split_evenly(len(data.offer_ids))
        stream.offers = [
            SKeitaroStreamOffer(offer_id=offer_id, share=share)
            for offer_id, share in zip(data.offer_ids, shares)
        ]
    created = await keitaro_client.create_stream(stream)
    logger.info(
        "Stream %s created in campaign %s: %s",
        created.id,
        campaign_id,
        created.name,
    )
    return created


async def fetch_streams(campaign_id: int) -> list[Stream]:
    keitaro_streams = await keitaro_client.get_streams(campaign_id)
    offers = await keitaro_client.get_offers()
    names = {offer.id: offer.name for offer in offers}
    streams = await StreamDAO.sync(campaign_id, [
        StreamData(
            keitaro_id=stream.id,
            name=stream.name,
            position=stream.position,
            has_offers=stream.kind == "landings",
            offers=[
                OfferShare(
                    offer_id=offer.offer_id,
                    name=names.get(offer.offer_id, str(offer.offer_id)),
                    share=offer.share,
                )
                for offer in stream.offers
            ],
        )
        for stream in keitaro_streams
    ])
    logger.info(
        "Campaign %s: %s streams fetched from Keitaro",
        campaign_id,
        len(streams),
    )
    return streams


def find_offer(stream: Stream, offer_id: int) -> StreamOffer | None:
    for offer in stream.offers:
        if offer.offer_id == offer_id:
            return offer
    return None


def add_offer(stream: Stream, offer_id: int, name: str) -> None:
    if not stream.has_offers:
        raise StreamHasNoOffersException
    offer = find_offer(stream, offer_id)
    if offer is None:
        stream.offers.append(StreamOffer(
            offer_id=offer_id,
            name=name,
            share=0,
            keitaro_share=None,
            pinned=False,
            removed=False,
            is_new=True,
        ))
    elif offer.removed:
        offer.removed = False
    else:
        raise OfferAlreadyInStreamException
    rebalance(stream.offers)
    logger.info("Stream %s: offer %s added", stream.id, offer_id)


def remove_offer(stream: Stream, offer_id: int) -> None:
    offer = find_offer(stream, offer_id)
    if offer is None or offer.removed:
        raise OfferNotInStreamException
    if len([o for o in stream.offers if not o.removed]) == 1:
        raise LastOfferException
    if offer.is_new:
        stream.offers.remove(offer)
    else:
        offer.removed = True
        offer.pinned = False
    rebalance(stream.offers)
    logger.info("Stream %s: offer %s removed", stream.id, offer_id)


def restore_offer(stream: Stream, offer_id: int) -> None:
    offer = find_offer(stream, offer_id)
    if offer is None or not offer.removed:
        raise OfferNotInStreamException
    offer.removed = False
    rebalance(stream.offers)
    logger.info("Stream %s: offer %s brought back", stream.id, offer_id)


def pin_offer(stream: Stream, offer_id: int, pinned: bool) -> None:
    offer = find_offer(stream, offer_id)
    if offer is None or offer.removed:
        raise OfferNotInStreamException
    offer.pinned = pinned
    logger.info(
        "Stream %s: offer %s %s",
        stream.id,
        offer_id,
        "pinned" if pinned else "unpinned",
    )


def cancel_changes(stream: Stream) -> None:
    for offer in list(stream.offers):
        if offer.is_new:
            stream.offers.remove(offer)
            continue
        offer.removed = offer.keitaro_share is None
        offer.share = offer.keitaro_share or 0
        if offer.removed:
            offer.pinned = False
    logger.info("Stream %s: unpublished changes cancelled", stream.id)


def mark_pushed(stream: Stream) -> None:
    for offer in stream.offers:
        offer.keitaro_share = None if offer.removed else offer.share
        offer.is_new = False


async def push_stream(stream_id: int) -> Stream:
    stream = await StreamDAO.find_with_offers(stream_id)
    offers = [
        SKeitaroStreamOffer(offer_id=offer.offer_id, share=offer.share)
        for offer in stream.offers
        if not offer.removed
    ]
    await keitaro_client.update_stream(
        stream.keitaro_id,
        SKeitaroStreamUpdate(offers=offers),
    )
    logger.info(
        "Stream %s pushed to Keitaro: %s",
        stream_id,
        {offer.offer_id: offer.share for offer in offers},
    )
    return await StreamDAO.change(stream_id, mark_pushed)
