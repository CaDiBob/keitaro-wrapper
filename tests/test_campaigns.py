import pytest


def create(
    client,
    name="camp",
    geo="au, mx",
    offer_id=1,
    redirect_url="https://google.com",
):
    data = {
        "name": name,
        "streams": [
            {"name": "Flow 1", "countries": geo, "redirect_url": redirect_url},
            {"name": "Flow 2", "offer_ids": [offer_id]},
        ],
    }
    return client.post("/campaigns", json=data)


def test_create_campaign(client, keitaro):
    response = create(client)
    assert response.status_code == 201, response.text
    campaign = response.json()

    created = keitaro.campaigns[campaign["id"]]
    assert created["type"] == "position"
    assert created["domain_id"] == 10
    assert created["group_id"] == 21
    assert created["traffic_source_id"] == 30
    assert campaign["url"] == f"https://kt.test/{created['alias']}"

    geo_stream, offer_stream = keitaro.streams.values()
    assert geo_stream["schema"] == "redirect"
    assert geo_stream["action_payload"] == "https://google.com"
    assert geo_stream["filters"] == [
        {"name": "country", "mode": "accept", "payload": ["AU", "MX"]},
    ]
    assert offer_stream["schema"] == "landings"
    assert offer_stream["offers"] == [
        {"offer_id": 1, "share": 100, "state": "active"},
    ]

    saved = client.get("/campaigns/created").json()
    assert saved[0]["keitaro_id"] == campaign["id"]


def test_create_campaign_fetches_streams(client):
    campaign = create(client).json()
    streams = client.get(f"/campaigns/{campaign['id']}/streams").json()
    assert [stream["has_offers"] for stream in streams] == [False, True]
    assert streams[0]["offers"] == []
    assert streams[1]["is_dirty"] is False
    assert streams[1]["offers"] == [{
        "offer_id": 1,
        "name": "Offer 1",
        "share": 100,
        "pinned": False,
        "removed": False,
    }]


def test_create_campaign_custom_redirect(client, keitaro):
    create(client, redirect_url="https://example.com")
    geo_stream = list(keitaro.streams.values())[0]
    assert geo_stream["action_payload"] == "https://example.com"


def test_create_campaign_any_streams(client, keitaro):
    data = {
        "name": "camp",
        "streams": [
            {"name": "A", "offer_ids": [1, 2, 3]},
            {"name": "B", "countries": ["RO"], "offer_ids": [4]},
            {"name": "C", "redirect_url": "https://example.com"},
        ],
    }
    assert client.post("/campaigns", json=data).status_code == 201
    first, second, third = keitaro.streams.values()
    assert [offer["share"] for offer in first["offers"]] == [34, 33, 33]
    assert second["filters"][0]["payload"] == ["RO"]
    assert [first["position"], second["position"], third["position"]] == [
        1, 2, 3,
    ]
    assert third["filters"] == []


@pytest.mark.parametrize("stream", [
    {"name": "A"},
    {"name": "A", "redirect_url": "https://example.com", "offer_ids": [1]},
])
def test_create_campaign_bad_stream(client, keitaro, stream):
    data = {"name": "camp", "streams": [stream]}
    assert client.post("/campaigns", json=data).status_code == 422
    assert keitaro.campaigns == {}


def test_create_campaign_without_streams(client, keitaro):
    data = {"name": "camp", "streams": []}
    assert client.post("/campaigns", json=data).status_code == 422
    assert keitaro.campaigns == {}


@pytest.mark.parametrize("geo", ["AUS", "A1", "RU, usa"])
def test_create_campaign_bad_geo(client, keitaro, geo):
    assert create(client, geo=geo).status_code == 422
    assert keitaro.campaigns == {}


def test_create_campaign_unknown_offer(client, keitaro):
    assert create(client, offer_id=999).status_code == 404
    assert keitaro.campaigns == {}


def test_create_campaign_stream_failure(client, keitaro):
    keitaro.fail_streams = True
    assert create(client).status_code == 502
    assert len(keitaro.campaigns) == 1
    assert client.get("/campaigns/created").json() == []


def test_get_campaigns(client):
    first = create(client, name="first").json()
    second = create(client, name="second").json()
    campaigns = client.get("/campaigns").json()
    assert [c["id"] for c in campaigns] == [second["id"], first["id"]]


def test_get_campaign(client):
    campaign = create(client).json()
    assert client.get(f"/campaigns/{campaign['id']}").json() == campaign


def test_get_unknown_campaign(client):
    assert client.get("/campaigns/999").status_code == 404


def test_get_offers(client):
    offers = client.get("/offers").json()
    assert offers[0] == {"id": 1, "name": "Offer 1"}
    assert len(offers) == 4
