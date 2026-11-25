import pytest


@pytest.fixture
def campaign(client):
    data = {
        "name": "camp",
        "streams": [
            {
                "name": "Flow 1",
                "countries": ["AU"],
                "redirect_url": "https://google.com",
            },
            {"name": "Flow 2", "offer_ids": [1]},
        ],
    }
    return client.post("/campaigns", json=data).json()


@pytest.fixture
def stream(client, campaign):
    return client.get(f"/campaigns/{campaign['id']}/streams").json()[1]


def shares(stream):
    return {
        offer["offer_id"]: offer["share"]
        for offer in stream["offers"]
        if not offer["removed"]
    }


def removed(stream):
    return [o["offer_id"] for o in stream["offers"] if o["removed"]]


def keitaro_shares(keitaro, stream):
    offers = keitaro.streams[stream["keitaro_id"]]["offers"]
    return {offer["offer_id"]: offer["share"] for offer in offers}


def add(client, stream, offer_id):
    url = f"/streams/{stream['id']}/offers"
    response = client.post(url, json={"offer_id": offer_id})
    assert response.status_code == 200, response.text
    return response.json()


def remove(client, stream, offer_id):
    response = client.delete(f"/streams/{stream['id']}/offers/{offer_id}")
    assert response.status_code == 200, response.text
    return response.json()


def restore(client, stream, offer_id):
    url = f"/streams/{stream['id']}/offers/{offer_id}/restore"
    response = client.post(url)
    assert response.status_code == 200, response.text
    return response.json()


def pin(client, stream, offer_id, pinned=True):
    url = f"/streams/{stream['id']}/offers/{offer_id}"
    response = client.patch(url, json={"pinned": pinned})
    assert response.status_code == 200, response.text
    return response.json()


def push(client, stream):
    response = client.post(f"/streams/{stream['id']}/push")
    assert response.status_code == 200, response.text
    return response.json()


def cancel(client, stream):
    response = client.post(f"/streams/{stream['id']}/cancel")
    assert response.status_code == 200, response.text
    return response.json()


def fetch(client, campaign):
    response = client.post(f"/campaigns/{campaign['id']}/streams/fetch")
    assert response.status_code == 200, response.text
    return response.json()


def test_add_offer_is_draft_until_push(client, keitaro, stream):
    result = add(client, stream, 2)
    assert shares(result) == {1: 50, 2: 50}
    assert result["is_dirty"] is True
    assert keitaro_shares(keitaro, stream) == {1: 100}

    result = push(client, stream)
    assert result["is_dirty"] is False
    assert keitaro_shares(keitaro, stream) == {1: 50, 2: 50}


def test_shares_are_split_evenly(client, stream):
    add(client, stream, 2)
    assert shares(add(client, stream, 3)) == {1: 34, 2: 33, 3: 33}
    assert shares(add(client, stream, 4)) == {1: 25, 2: 25, 3: 25, 4: 25}


def test_cancel_drops_unpublished_offers(client, keitaro, stream):
    add(client, stream, 2)
    result = cancel(client, stream)
    assert shares(result) == {1: 100}
    assert removed(result) == []
    assert result["is_dirty"] is False
    assert keitaro_shares(keitaro, stream) == {1: 100}


def test_remove_offer_goes_to_archive(client, keitaro, stream):
    add(client, stream, 2)
    push(client, stream)

    result = remove(client, stream, 1)
    assert shares(result) == {2: 100}
    assert removed(result) == [1]
    assert result["offers"][0]["share"] == 0
    assert result["is_dirty"] is True
    assert keitaro_shares(keitaro, stream) == {1: 50, 2: 50}

    result = push(client, stream)
    assert removed(result) == [1]
    assert result["is_dirty"] is False
    assert keitaro_shares(keitaro, stream) == {2: 100}


def test_cancel_restores_removed_offer(client, stream):
    add(client, stream, 2)
    push(client, stream)
    remove(client, stream, 1)
    result = cancel(client, stream)
    assert shares(result) == {1: 50, 2: 50}
    assert result["is_dirty"] is False


def test_bring_back(client, keitaro, stream):
    add(client, stream, 2)
    push(client, stream)
    remove(client, stream, 1)
    push(client, stream)

    result = restore(client, stream, 1)
    assert shares(result) == {1: 50, 2: 50}
    assert result["is_dirty"] is True

    push(client, stream)
    assert keitaro_shares(keitaro, stream) == {1: 50, 2: 50}


def test_cancel_returns_brought_back_offer_to_archive(client, stream):
    add(client, stream, 2)
    push(client, stream)
    remove(client, stream, 1)
    push(client, stream)
    restore(client, stream, 1)

    result = cancel(client, stream)
    assert shares(result) == {2: 100}
    assert removed(result) == [1]


def test_add_removed_offer_brings_it_back(client, stream):
    add(client, stream, 2)
    push(client, stream)
    remove(client, stream, 1)
    assert shares(add(client, stream, 1)) == {1: 50, 2: 50}


def test_remove_unpublished_offer_deletes_it(client, stream):
    add(client, stream, 2)
    result = remove(client, stream, 2)
    assert shares(result) == {1: 100}
    assert removed(result) == []
    assert result["is_dirty"] is False


def test_fetch_marks_offers_missing_in_keitaro_as_removed(
    client, keitaro, campaign, stream,
):
    add(client, stream, 2)
    add(client, stream, 3)
    add(client, stream, 4)
    push(client, stream)

    keitaro.streams[stream["keitaro_id"]]["offers"] = [
        {"offer_id": 1, "share": 25, "state": "active"},
        {"offer_id": 4, "share": 25, "state": "active"},
    ]
    result = fetch(client, campaign)[1]
    assert shares(result) == {1: 25, 4: 25}
    assert removed(result) == [2, 3]
    assert result["is_dirty"] is False

    assert shares(restore(client, stream, 2)) == {1: 34, 2: 33, 4: 33}


def test_fetch_adds_offers_created_in_keitaro(client, keitaro, campaign, stream):
    keitaro.streams[stream["keitaro_id"]]["offers"].append(
        {"offer_id": 3, "share": 0, "state": "active"},
    )
    result = fetch(client, campaign)[1]
    assert shares(result) == {1: 100, 3: 0}
    assert result["offers"][1]["name"] == "Offer 3"


def test_fetch_drops_streams_deleted_in_keitaro(client, keitaro, campaign):
    redirect_stream = client.get(
        f"/campaigns/{campaign['id']}/streams",
    ).json()[0]
    del keitaro.streams[redirect_stream["keitaro_id"]]
    assert len(fetch(client, campaign)) == 1


def test_pinned_share_survives_rebalance(client, keitaro, stream):
    add(client, stream, 2)
    add(client, stream, 3)
    add(client, stream, 4)
    result = pin(client, stream, 2)
    assert result["offers"][1]["pinned"] is True
    assert shares(result) == {1: 25, 2: 25, 3: 25, 4: 25}

    assert shares(remove(client, stream, 4)) == {1: 38, 2: 25, 3: 37}
    assert shares(add(client, stream, 4)) == {1: 25, 2: 25, 3: 25, 4: 25}
    assert shares(remove(client, stream, 1)) == {2: 25, 3: 38, 4: 37}

    push(client, stream)
    assert keitaro_shares(keitaro, stream) == {2: 25, 3: 38, 4: 37}

    pin(client, stream, 2, pinned=False)
    assert shares(add(client, stream, 1)) == {1: 25, 2: 25, 3: 25, 4: 25}


def test_add_offer_twice(client, stream):
    url = f"/streams/{stream['id']}/offers"
    assert client.post(url, json={"offer_id": 1}).status_code == 409


def test_add_unknown_offer(client, stream):
    url = f"/streams/{stream['id']}/offers"
    assert client.post(url, json={"offer_id": 999}).status_code == 404


def test_remove_last_offer(client, stream):
    url = f"/streams/{stream['id']}/offers/1"
    assert client.delete(url).status_code == 409


def test_remove_missing_offer(client, stream):
    url = f"/streams/{stream['id']}/offers/2"
    assert client.delete(url).status_code == 404


def test_restore_active_offer(client, stream):
    url = f"/streams/{stream['id']}/offers/1/restore"
    assert client.post(url).status_code == 404


def test_stream_without_offers(client, campaign):
    stream = client.get(f"/campaigns/{campaign['id']}/streams").json()[0]
    url = f"/streams/{stream['id']}/offers"
    assert client.post(url, json={"offer_id": 2}).status_code == 409


def test_unknown_stream(client):
    url = "/streams/424242/offers"
    assert client.post(url, json={"offer_id": 2}).status_code == 404
    assert client.post("/streams/424242/push").status_code == 404
