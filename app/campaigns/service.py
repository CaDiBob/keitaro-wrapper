import string
import secrets

from app.config import settings
from app.logger import logger
from app.http_client import keitaro_client
from app.exceptions import (
    OfferNotFoundException,
    KeitaroNotConfiguredException,
)
from app.keitaro_schemas import (
    SKeitaroItem,
    SKeitaroCampaign,
    SKeitaroCampaignCreate,
)
from app.streams.service import create_stream
from app.campaigns.schemas import SCampaignCreate


def find_id(items: list[SKeitaroItem], name: str) -> int:
    for item in items:
        if item.name == name:
            return item.id
    if not name and items:
        return items[0].id
    raise KeitaroNotConfiguredException


def make_alias() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))


def get_url(campaign: SKeitaroCampaign) -> str:
    return campaign.domain.rstrip("/") + "/" + campaign.alias


async def create_campaign(data: SCampaignCreate) -> SKeitaroCampaign:
    offers = await keitaro_client.get_offers()
    offer_ids = {offer.id for offer in offers}
    for stream in data.streams:
        if not offer_ids.issuperset(stream.offer_ids):
            raise OfferNotFoundException
    domains = await keitaro_client.get_domains()
    groups = await keitaro_client.get_groups()
    sources = await keitaro_client.get_traffic_sources()

    campaign = await keitaro_client.create_campaign(SKeitaroCampaignCreate(
        name=data.name,
        alias=make_alias(),
        domain_id=find_id(domains, settings.DOMAIN_NAME),
        group_id=find_id(groups, settings.GROUP_NAME),
        traffic_source_id=find_id(sources, settings.SOURCE_NAME),
    ))
    logger.info("Campaign %s created: %s", campaign.id, campaign.name)
    for position, stream in enumerate(data.streams, start=1):
        await create_stream(campaign.id, position, stream)
    return campaign
