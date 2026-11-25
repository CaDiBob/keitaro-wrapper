from app.dao.base import BaseDAO
from app.campaigns.models import Campaign


class CampaignDAO(BaseDAO):
    model = Campaign
