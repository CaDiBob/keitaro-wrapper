from fastapi import APIRouter, status

from app.http_client import keitaro_client
from app.campaigns import service
from app.campaigns.dao import CampaignDAO
from app.streams.service import fetch_streams
from app.campaigns.schemas import (
    SCampaign,
    SCampaignShort,
    SCampaignCreate,
    SCreatedCampaign,
)


router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"],
)


@router.get("")
async def get_campaigns() -> list[SCampaignShort]:
    campaigns = await keitaro_client.get_campaigns()
    return sorted(campaigns, key=lambda c: c.id, reverse=True)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_campaign(data: SCampaignCreate) -> SCampaign:
    campaign = await service.create_campaign(data)
    url = service.get_url(campaign)
    await CampaignDAO.add(
        keitaro_id=campaign.id,
        name=campaign.name,
        alias=campaign.alias,
        url=url,
    )
    await fetch_streams(campaign.id)
    return SCampaign(
        id=campaign.id,
        name=campaign.name,
        alias=campaign.alias,
        url=url,
    )


@router.get("/created")
async def get_created_campaigns() -> list[SCreatedCampaign]:
    return await CampaignDAO.find_all()


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: int) -> SCampaign:
    campaign = await keitaro_client.get_campaign(campaign_id)
    return SCampaign(
        id=campaign.id,
        name=campaign.name,
        alias=campaign.alias,
        url=service.get_url(campaign),
    )
