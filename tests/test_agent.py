import json
import uuid

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from tests.test_properties import sample_payload


def _tool_call(name: str, args: dict) -> dict:
    return {"name": name, "args": args, "id": f"call_{uuid.uuid4().hex[:8]}", "type": "tool_call"}


def create(client: TestClient, **overrides) -> dict:
    resp = client.post("/properties", json=sample_payload(**overrides))
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_agent_calls_search_tool_and_answers(client: TestClient, fake_agent_model) -> None:
    create(client, title="Apartamento 2Q na Trindade", description="Ótimo apê perto da UFSC.")
    create(client, title="Casa na Lagoa", description="Casa ampla com vista para a lagoa.")

    fake_agent_model(
        [
            AIMessage(
                content="",
                tool_calls=[_tool_call("search_properties", {"query": "apê perto da UFSC"})],
            ),
            AIMessage(content="Encontrei um apartamento na Trindade que combina."),
        ]
    )

    resp = client.post("/agent/chat", json={"message": "quero um apê perto da UFSC"})
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["thread_id"]
    assert "Trindade" in body["reply"]
    assert [c["name"] for c in body["tool_calls"]] == ["search_properties"]
    assert body["properties"]
    assert all("id" in p and "price" in p for p in body["properties"])


def test_agent_answers_without_tools(client: TestClient, fake_agent_model) -> None:
    fake_agent_model([AIMessage(content="Posso ajudar a buscar imóveis em Florianópolis.")])

    resp = client.post("/agent/chat", json={"message": "oi, o que você faz?"})
    body = resp.json()
    assert body["tool_calls"] == []
    assert body["properties"] == []
    assert "imóveis" in body["reply"]


def test_agent_get_property_details(client: TestClient, fake_agent_model) -> None:
    prop = create(client, description="Casa com quintal grande e piscina aquecida.")

    fake_agent_model(
        [
            AIMessage(
                content="",
                tool_calls=[_tool_call("get_property_details", {"property_id": prop["id"]})],
            ),
            AIMessage(content="Aqui estão os detalhes do imóvel."),
        ]
    )

    resp = client.post("/agent/chat", json={"message": f"detalhes do imóvel {prop['id']}"})
    body = resp.json()
    assert body["properties"][0]["id"] == prop["id"]
    assert "piscina" in body["properties"][0]["description"]


def test_agent_thread_id_roundtrips(client: TestClient, fake_agent_model) -> None:
    fake_agent_model(
        [
            AIMessage(content="Primeira resposta."),
            AIMessage(content="Segunda resposta, lembrando do contexto."),
        ]
    )

    first = client.post("/agent/chat", json={"message": "oi"}).json()
    tid = first["thread_id"]

    second = client.post("/agent/chat", json={"message": "e agora?", "thread_id": tid}).json()
    assert second["thread_id"] == tid


def test_agent_chat_stream_emits_events(client: TestClient, fake_agent_model) -> None:
    create(client, title="Studio no Centro", description="Studio compacto e mobiliado.")

    fake_agent_model(
        [
            AIMessage(
                content="",
                tool_calls=[_tool_call("filter_properties", {"property_type": "studio"})],
            ),
            AIMessage(content="Achei um studio no Centro."),
        ]
    )

    events = []
    with client.stream("POST", "/agent/chat/stream", json={"message": "studio no centro"}) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        for line in resp.iter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))

    types = [e["type"] for e in events]
    assert "tool_call" in types
    assert "tool_result" in types
    assert types[-1] == "done"
    assert events[-1]["thread_id"]
