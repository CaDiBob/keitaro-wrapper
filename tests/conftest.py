import os
import re

os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5433")
os.environ.setdefault("DB_USER", "keitaro")
os.environ.setdefault("DB_PASS", "keitaro")
os.environ.setdefault("DB_NAME", "keitaro_wrapper")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base
from app.http_client import KeitaroClient
from app.exceptions import (
    KeitaroRequestException,
    KeitaroNotFoundException,
)


class FakeKeitaro:

    def __init__(self):
        self.offers = [{"id": i, "name": f"Offer {i}"} for i in (1, 2, 3, 4)]
        self.campaigns = {}
        self.streams = {}
        self.fail_streams = False
        self.last_id = 100

    def next_id(self):
        self.last_id += 1
        return self.last_id

    async def request(self, method, path, data=None, params=None):
        path = path.removeprefix("admin_api/v1")
        if path == "/offers":
            return self.offers
        if path == "/domains":
            return [{"id": 10, "name": "kt.test"}]
        if path == "/groups":
            return [
                {"id": 20, "name": "OTHER"},
                {"id": 21, "name": "FORTESTS"},
            ]
        if path == "/traffic_sources":
            return [{"id": 30, "name": "FORTESTS"}]
        if path == "/campaigns" and method == "GET":
            return list(self.campaigns.values())
        if path == "/campaigns" and method == "POST":
            campaign = {
                **data,
                "id": self.next_id(),
                "domain": "https://kt.test/",
            }
            self.campaigns[campaign["id"]] = campaign
            return campaign
        if path == "/streams" and method == "POST":
            if self.fail_streams:
                raise KeitaroRequestException
            stream = {
                "filters": [],
                "offers": [],
                "action_payload": None,
                **data,
                "id": self.next_id(),
            }
            self.streams[stream["id"]] = stream
            return stream
        if match := re.fullmatch(r"/campaigns/(\d+)/streams", path):
            return [
                stream for stream in self.streams.values()
                if stream["campaign_id"] == int(match[1])
            ]
        if match := re.fullmatch(r"/campaigns/(\d+)", path):
            campaign_id = int(match[1])
            if campaign_id not in self.campaigns:
                raise KeitaroNotFoundException
            if method == "DELETE":
                return self.campaigns.pop(campaign_id)
            return self.campaigns[campaign_id]
        if match := re.fullmatch(r"/streams/(\d+)", path):
            self.streams[int(match[1])].update(data)
            return self.streams[int(match[1])]
        raise KeitaroNotFoundException


@pytest.fixture
def keitaro(monkeypatch):
    fake = FakeKeitaro()
    monkeypatch.setattr(KeitaroClient, "http_client", fake)
    return fake


@pytest.fixture
def client(keitaro, monkeypatch, tmp_path):
    db_file = tmp_path / "test.db"
    Base.metadata.create_all(create_engine(f"sqlite:///{db_file}"))
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_file}",
        poolclass=NullPool,
    )
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr("app.dao.base.async_session_maker", session_maker)
    monkeypatch.setattr("app.streams.dao.async_session_maker", session_maker)
    return TestClient(app)
