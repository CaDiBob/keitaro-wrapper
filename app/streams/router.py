from fastapi import APIRouter

from app.http_client import keitaro_client
from app.exceptions import OfferNotFoundException
from app.streams import service
from app.streams.dao import StreamDAO
from app.streams.schemas import SStream, SOfferAdd, SOfferPin


router = APIRouter(tags=["Streams"])


@router.get("/campaigns/{campaign_id}/streams")
async def get_streams(campaign_id: int) -> list[SStream]:
    return await StreamDAO.find_by_campaign(campaign_id)


@router.post("/campaigns/{campaign_id}/streams/fetch")
async def fetch_streams(campaign_id: int) -> list[SStream]:
    return await service.fetch_streams(campaign_id)


@router.post("/streams/{stream_id}/offers")
async def add_offer(stream_id: int, data: SOfferAdd) -> SStream:
    offers = await keitaro_client.get_offers()
    names = {offer.id: offer.name for offer in offers}
    if data.offer_id not in names:
        raise OfferNotFoundException
    return await StreamDAO.change(
        stream_id,
        service.add_offer,
        data.offer_id,
        names[data.offer_id],
    )


@router.delete("/streams/{stream_id}/offers/{offer_id}")
async def remove_offer(stream_id: int, offer_id: int) -> SStream:
    return await StreamDAO.change(stream_id, service.remove_offer, offer_id)


@router.post("/streams/{stream_id}/offers/{offer_id}/restore")
async def restore_offer(stream_id: int, offer_id: int) -> SStream:
    return await StreamDAO.change(stream_id, service.restore_offer, offer_id)


@router.patch("/streams/{stream_id}/offers/{offer_id}")
async def pin_offer(stream_id: int, offer_id: int, data: SOfferPin) -> SStream:
    return await StreamDAO.change(
        stream_id,
        service.pin_offer,
        offer_id,
        data.pinned,
    )


@router.post("/streams/{stream_id}/push")
async def push_stream(stream_id: int) -> SStream:
    return await service.push_stream(stream_id)


@router.post("/streams/{stream_id}/cancel")
async def cancel_changes(stream_id: int) -> SStream:
    return await StreamDAO.change(stream_id, service.cancel_changes)
