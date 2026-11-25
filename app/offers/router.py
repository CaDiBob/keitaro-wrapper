from fastapi import APIRouter

from app.http_client import keitaro_client
from app.offers.schemas import SOffer


router = APIRouter(
    prefix="/offers",
    tags=["Offers"],
)


@router.get("")
async def get_offers() -> list[SOffer]:
    return await keitaro_client.get_offers()
