from http.client import responses

import pytest

import app as inventory_app


@pytest.fixture
def client():
    inventory_app.item_dict.clear()
    return inventory_app.app.test_client()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_post_stock(client):
    payload = {"name": "test", "quantity" : 15}
    response = client.post("/stock", json=payload)
    assert response.status_code == 201
    assert response.get_json() == payload


def test_get_stock(client):
    payload = {"name": "test", "quantity" : 15}
    client.post("/stock", json=payload)

    name = payload["name"]
    response = client.get(f"/stock/{name}")
    assert response.status_code == 200
    assert response.get_json() == payload


def test_get_stock_nothing(client):
    response = client.get("/stock/nothing")
    assert response.status_code == 404


def test_no_quantity(client):
    payload = {"name": "test"}
    response = client.post("/stock", json=payload)
    assert response.status_code == 400


def test_no_name(client):
    payload = {"quantity" : 15}
    response = client.post("/stock", json=payload)
    assert response.status_code == 400


def test_post_no_body(client):
    response = client.post("/stock")
    assert response.status_code == 400


def test_get_stock_multiple_post(client):
    payload = {"name": "test", "quantity" : 15}
    client.post("/stock", json=payload)
    payload = {"name": "test", "quantity" : 25}
    client.post("/stock", json=payload)

    name = payload["name"]
    response = client.get(f"/stock/{name}")
    assert response.status_code == 200
    assert response.get_json()["quantity"] == 25