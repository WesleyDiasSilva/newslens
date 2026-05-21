"""Validação de inputs do endpoint /api/briefing."""


def test_payload_minimo_valido_retorna_200(client):
    resp = client.post("/api/briefing", json={"tema": "eleições 2026"})
    assert resp.status_code == 200


def test_payload_sem_tema_retorna_422(client):
    resp = client.post("/api/briefing", json={"modo": "simples"})
    assert resp.status_code == 422


def test_payload_com_tema_vazio_retorna_422(client):
    resp = client.post("/api/briefing", json={"tema": ""})
    assert resp.status_code == 422


def test_payload_com_tema_so_espacos_retorna_422(client):
    resp = client.post("/api/briefing", json={"tema": "   "})
    assert resp.status_code == 422


def test_modo_invalido_retorna_422(client):
    resp = client.post(
        "/api/briefing",
        json={"tema": "ações Petrobras", "modo": "turbo"},
    )
    assert resp.status_code == 422


def test_modo_simples_aceito(client):
    resp = client.post(
        "/api/briefing",
        json={"tema": "Selic", "modo": "simples"},
    )
    assert resp.status_code == 200


def test_modo_subagentes_aceito(client):
    resp = client.post(
        "/api/briefing",
        json={"tema": "Selic", "modo": "subagentes"},
    )
    assert resp.status_code == 200


def test_payload_nao_json_retorna_422(client):
    resp = client.post(
        "/api/briefing",
        content="tema=teste",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 422
