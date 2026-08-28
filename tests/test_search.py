from fastapi.testclient import TestClient

from tests.test_properties import sample_payload


def create(client: TestClient, **overrides) -> dict:
    resp = client.post("/properties", json=sample_payload(**overrides))
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_search_ranks_by_text_overlap(client: TestClient) -> None:
    create(
        client,
        title="Casa com piscina e churrasqueira em Jurerê",
        description="Casa espaçosa com piscina aquecida, churrasqueira e vista para o mar.",
    )
    create(
        client,
        title="Studio compacto no Centro",
        description="Studio mobiliado pequeno, ideal para uma pessoa, próximo ao terminal.",
    )
    create(
        client,
        title="Sala comercial na Trindade",
        description="Sala comercial para escritório, com recepção e duas vagas.",
    )

    resp = client.get("/search", params={"q": "casa com piscina e churrasqueira", "limit": 3})
    assert resp.status_code == 200
    body = resp.json()

    assert body["query"] == "casa com piscina e churrasqueira"
    assert body["count"] == 3
    assert "piscina" in body["items"][0]["property"]["title"].lower()
    scores = [i["score"] for i in body["items"]]
    assert scores == sorted(scores, reverse=True)


def test_search_applies_structured_filters(client: TestClient) -> None:
    create(client, operation="sale", description="Apartamento à venda com varanda gourmet.")
    create(client, operation="rent", description="Apartamento para alugar com varanda gourmet.")

    resp = client.get("/search", params={"q": "apartamento varanda gourmet", "operation": "rent"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items
    assert all(i["property"]["operation"] == "rent" for i in items)


def test_search_ignores_properties_without_embedding(client: TestClient, db_session) -> None:
    # create() goes through the service, which always sets an embedding; this one bypasses it.
    from realestate_rag_agent.repositories.models import Property

    db_session.add(
        Property(
            title="Sem embedding",
            description="Este imóvel não tem vetor e não deve aparecer na busca.",
            operation="sale",
            property_type="house",
            price=100000,
            area_m2=50,
            neighborhood="Centro",
            city="Florianópolis",
            state="SC",
        )
    )
    db_session.commit()
    create(client, title="Com embedding", description="Casa normal indexada para busca.")

    resp = client.get("/search", params={"q": "imóvel casa", "limit": 10})
    titles = [i["property"]["title"] for i in resp.json()["items"]]
    assert "Sem embedding" not in titles
    assert "Com embedding" in titles


def test_search_requires_query(client: TestClient) -> None:
    assert client.get("/search").status_code == 422
    assert client.get("/search", params={"q": "a"}).status_code == 422
