"""Testes do fluxo human-in-the-loop.

Cobre os dois endpoints (/api/briefing pausa, /api/briefing/retomar
prossegue) e a validação de input do retomar. A camada LLM continua
mockada via `chamar_agente` (conftest), então o interrupt é exercitado
de verdade — só o conteúdo de notícias/briefing é fake.
"""


def test_briefing_pausa_e_retorna_aguardando_aprovacao(client):
    resp = client.post("/api/briefing", json={"tema": "hitl-tema-1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "aguardando_aprovacao"


def test_briefing_pausa_expoe_thread_id_e_noticias(client):
    resp = client.post("/api/briefing", json={"tema": "hitl-tema-2"})
    body = resp.json()
    assert isinstance(body.get("thread_id"), str) and body["thread_id"]
    assert isinstance(body.get("noticias"), str) and body["noticias"]


def test_briefing_pausa_nao_inclui_briefing(client):
    resp = client.post("/api/briefing", json={"tema": "hitl-tema-3"})
    body = resp.json()
    # Briefing só sai após a aprovação — não pode vazar na pausa.
    assert "briefing" not in body or not body.get("briefing")


def test_briefing_pausa_inclui_metadados_de_memoria(client):
    resp = client.post("/api/briefing", json={"tema": "hitl-tema-4"})
    body = resp.json()
    assert "memoria" in body
    assert "disponivel" in body["memoria"]
    assert "primeira_vez" in body["memoria"]


def test_retomar_sem_thread_id_retorna_422(client):
    resp = client.post("/api/briefing/retomar", json={})
    assert resp.status_code == 422


def test_retomar_com_thread_id_vazio_retorna_422(client):
    resp = client.post("/api/briefing/retomar", json={"thread_id": ""})
    assert resp.status_code == 422


def test_retomar_com_thread_id_desconhecido_retorna_404(client):
    resp = client.post(
        "/api/briefing/retomar",
        json={"thread_id": "thread-que-nao-existe-xyz"},
    )
    assert resp.status_code == 404


def test_retomar_apos_pausa_devolve_briefing_completo(client):
    pausa = client.post("/api/briefing", json={"tema": "hitl-fluxo-completo"})
    assert pausa.status_code == 200
    thread_id = pausa.json()["thread_id"]

    retoma = client.post("/api/briefing/retomar", json={"thread_id": thread_id})
    assert retoma.status_code == 200
    body = retoma.json()
    assert isinstance(body.get("briefing"), str) and body["briefing"]
    assert "memoria" in body
    assert isinstance(body.get("num_chamadas"), int)
    assert isinstance(body.get("tempo_ms"), int)


def test_retomar_nao_devolve_status_aguardando(client):
    pausa = client.post("/api/briefing", json={"tema": "hitl-status-final"})
    thread_id = pausa.json()["thread_id"]
    retoma = client.post("/api/briefing/retomar", json={"thread_id": thread_id})
    body = retoma.json()
    assert body.get("status") != "aguardando_aprovacao"
