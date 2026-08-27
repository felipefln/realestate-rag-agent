from fastapi.testclient import TestClient


def sample_payload(**overrides) -> dict:
    payload = {
        "title": "Apartamento 2Q na Trindade",
        "description": "Apartamento à venda no bairro Trindade, perto da UFSC.",
        "operation": "sale",
        "property_type": "apartment",
        "price": 850000,
        "condo_fee": 620,
        "iptu": 2400,
        "bedrooms": 2,
        "bathrooms": 2,
        "parking_spaces": 1,
        "area_m2": 72.5,
        "neighborhood": "Trindade",
        "city": "Florianópolis",
        "state": "SC",
        "amenities": ["elevador", "sacada"],
    }
    payload.update(overrides)
    return payload


def create(client: TestClient, **overrides) -> dict:
    resp = client.post("/properties", json=sample_payload(**overrides))
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_and_get(client: TestClient) -> None:
    created = create(client)
    assert created["id"]
    assert created["created_at"]

    got = client.get(f"/properties/{created['id']}")
    assert got.status_code == 200
    assert got.json()["title"] == "Apartamento 2Q na Trindade"


def test_get_unknown_returns_404(client: TestClient) -> None:
    resp = client.get("/properties/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_list_pagination_and_envelope(client: TestClient) -> None:
    for i in range(3):
        create(client, title=f"Imóvel {i}", price=500000 + i)

    resp = client.get("/properties", params={"limit": 2, "offset": 0})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert body["limit"] == 2
    assert len(body["items"]) == 2

    page2 = client.get("/properties", params={"limit": 2, "offset": 2}).json()
    assert len(page2["items"]) == 1


def test_list_filters(client: TestClient) -> None:
    create(client, operation="sale", price=900000, neighborhood="Centro", bedrooms=3)
    create(client, operation="rent", price=3500, neighborhood="Campeche", bedrooms=2)
    create(client, operation="sale", price=450000, neighborhood="Campeche", bedrooms=1)

    rent = client.get("/properties", params={"operation": "rent"}).json()
    assert rent["total"] == 1

    campeche = client.get("/properties", params={"neighborhood": "campeche"}).json()
    assert campeche["total"] == 2

    cheap_sales = client.get(
        "/properties", params={"operation": "sale", "max_price": 500000}
    ).json()
    assert cheap_sales["total"] == 1

    two_plus = client.get("/properties", params={"min_bedrooms": 2}).json()
    assert two_plus["total"] == 2


def test_list_filter_by_amenities(client: TestClient) -> None:
    create(client, title="com piscina e churras", amenities=["piscina", "churrasqueira"])
    create(client, title="só piscina", amenities=["piscina"])
    create(client, title="sem amenities", amenities=[])

    one = client.get("/properties", params={"amenities": ["piscina"]}).json()
    assert one["total"] == 2

    both = client.get("/properties", params={"amenities": ["piscina", "churrasqueira"]}).json()
    assert both["total"] == 1
    assert both["items"][0]["title"] == "com piscina e churras"


def test_patch_updates_fields(client: TestClient) -> None:
    created = create(client, price=800000)
    resp = client.patch(f"/properties/{created['id']}", json={"price": 780000})
    assert resp.status_code == 200
    assert resp.json()["price"] == 780000.0
    assert resp.json()["title"] == created["title"]


def test_delete(client: TestClient) -> None:
    created = create(client)
    assert client.delete(f"/properties/{created['id']}").status_code == 204
    assert client.get(f"/properties/{created['id']}").status_code == 404
    assert client.delete(f"/properties/{created['id']}").status_code == 404


def test_create_validation_rejects_negative_price(client: TestClient) -> None:
    resp = client.post("/properties", json=sample_payload(price=-1))
    assert resp.status_code == 422
