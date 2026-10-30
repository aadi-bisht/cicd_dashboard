import pytest
import requests

import app as api_app


@pytest.fixture
def client():
    api_app.item_list.clear()
    return api_app.app.test_client()


class FakeResponse:
    def __init__(self, data, status_code):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_post_then_get_items(client):
    payload = {"name": "pen"}
    post_response = client.post("/items", json=payload)
    assert post_response.status_code == 201
    assert post_response.get_json()["name"] == "pen"

    get_response = client.get("/items")
    assert get_response.status_code == 200
    items = get_response.get_json()
    assert len(items) == 1
    assert items[0]["name"] == "pen"


def test_post_item_no_body(client):
    response = client.post("/items")
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_post_item_no_name(client):
    response = client.post("/items", json={"quantity": 5})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_metrics(client):
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.get_data(as_text=True)


def test_stock_passthrough(client, monkeypatch):
    def fake_get(url, timeout):
        return FakeResponse({"name": "pen", "quantity": 10}, 200)

    monkeypatch.setattr(requests, "get", fake_get)

    response = client.get("/items/pen/stock")
    assert response.status_code == 200
    assert response.get_json()["quantity"] == 10


def test_stock_passthrough_not_found(client, monkeypatch):
    def fake_get(url, timeout):
        return FakeResponse({"error": "item name does not exist"}, 404)

    monkeypatch.setattr(requests, "get", fake_get)

    response = client.get("/items/ghost/stock")
    assert response.status_code == 404


def test_stock_inventory_down(client, monkeypatch):
    def fake_get(url, timeout):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(requests, "get", fake_get)

    response = client.get("/items/pen/stock")
    assert response.status_code == 503
    assert "error" in response.get_json()


def test_stock_inventory_timeout(client, monkeypatch):
    def fake_get(url, timeout):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(requests, "get", fake_get)

    response = client.get("/items/pen/stock")
    assert response.status_code == 503


def test_stock_uses_inventory_url_and_timeout(client, monkeypatch):
    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return FakeResponse({"name": "pen", "quantity": 1}, 200)

    monkeypatch.setattr(requests, "get", fake_get)

    client.get("/items/pen/stock")

    assert len(calls) == 1
    called_url, called_timeout = calls[0]
    assert called_url == f"{api_app.INVENTORY_URL}/stock/pen"
    assert called_timeout is not None