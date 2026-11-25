import time

from httpx import AsyncClient, HTTPError

from app.config import settings
from app.logger import logger
from app.exceptions import (
    KeitaroRequestException,
    KeitaroNotFoundException,
)
from app.keitaro_schemas import (
    SKeitaroItem,
    SKeitaroStream,
    SKeitaroCampaign,
    SKeitaroStreamCreate,
    SKeitaroStreamUpdate,
    SKeitaroCampaignCreate,
)


class HttpClient:
    BASE_URL = settings.BASE_URL

    def __init__(self):
        self.http_client = AsyncClient(
            base_url=self.BASE_URL,
            headers={"Api-Key": settings.API_KEY},
            timeout=20,
        )

    async def request(self, method, path, data=None, params=None):
        started = time.monotonic()
        try:
            response = await self.http_client.request(
                method,
                path,
                json=data,
                params=params,
            )
        except HTTPError as error:
            logger.error("Keitaro %s %s failed: %r", method, path, error)
            raise KeitaroRequestException
        elapsed = round((time.monotonic() - started) * 1000)
        if response.is_error:
            logger.warning(
                "Keitaro %s %s -> %s in %s ms: %s",
                method,
                path,
                response.status_code,
                elapsed,
                response.text[:300],
            )
        else:
            logger.info(
                "Keitaro %s %s -> %s in %s ms",
                method,
                path,
                response.status_code,
                elapsed,
            )
        if response.status_code == 404:
            raise KeitaroNotFoundException
        if response.is_error:
            raise KeitaroRequestException
        return response.json()


class KeitaroClient:

    def __init__(self):
        self.__http_client = None

    @property
    def http_client(self) -> HttpClient:
        if self.__http_client is None:
            self.__http_client = HttpClient()
        return self.__http_client

    async def get_items(self, path, params=None) -> list[SKeitaroItem]:
        items = await self.http_client.request("GET", path, params=params)
        return [SKeitaroItem(**item) for item in items]

    async def get_offers(self) -> list[SKeitaroItem]:
        return await self.get_items("admin_api/v1/offers")

    async def get_domains(self) -> list[SKeitaroItem]:
        return await self.get_items("admin_api/v1/domains")

    async def get_groups(self) -> list[SKeitaroItem]:
        return await self.get_items(
            "admin_api/v1/groups",
            params={"type": "campaigns"},
        )

    async def get_traffic_sources(self) -> list[SKeitaroItem]:
        return await self.get_items("admin_api/v1/traffic_sources")

    async def get_campaigns(self) -> list[SKeitaroCampaign]:
        campaigns = await self.http_client.request(
            "GET",
            "admin_api/v1/campaigns",
        )
        return [SKeitaroCampaign(**campaign) for campaign in campaigns]

    async def get_campaign(self, campaign_id: int) -> SKeitaroCampaign:
        campaign = await self.http_client.request(
            "GET",
            f"admin_api/v1/campaigns/{campaign_id}",
        )
        return SKeitaroCampaign(**campaign)

    async def create_campaign(
        self,
        data: SKeitaroCampaignCreate,
    ) -> SKeitaroCampaign:
        campaign = await self.http_client.request(
            "POST",
            "admin_api/v1/campaigns",
            data=data.model_dump(),
        )
        return SKeitaroCampaign(**campaign)

    async def get_streams(self, campaign_id: int) -> list[SKeitaroStream]:
        streams = await self.http_client.request(
            "GET",
            f"admin_api/v1/campaigns/{campaign_id}/streams",
        )
        return [SKeitaroStream(**stream) for stream in streams]

    async def create_stream(
        self,
        data: SKeitaroStreamCreate,
    ) -> SKeitaroStream:
        stream = await self.http_client.request(
            "POST",
            "admin_api/v1/streams",
            data=data.model_dump(by_alias=True, exclude_none=True),
        )
        return SKeitaroStream(**stream)

    async def update_stream(
        self,
        stream_id: int,
        data: SKeitaroStreamUpdate,
    ) -> SKeitaroStream:
        stream = await self.http_client.request(
            "PUT",
            f"admin_api/v1/streams/{stream_id}",
            data=data.model_dump(),
        )
        return SKeitaroStream(**stream)


keitaro_client = KeitaroClient()
