"""Comportamentos proibidos conforme a SPEC."""
import re


def _post(client, tema):
    resp = client.post("/api/briefing", json={"tema": tema})
    assert resp.status_code == 200
    return resp.json()


def test_nao_cruza_memoria_entre_temas_distintos(client):
    _post(client, "petrobras")
    _post(client, "petrobras")
    _post(client, "petrobras")
    body = _post(client, "vale")
    assert body["memoria"]["briefings_anteriores_consultados"] == 0


def test_resposta_nao_expoe_caminhos_de_arquivo(client):
    _post(client, "selic")
    body = _post(client, "selic")
    serializado = str(body)
    assert "/app/" not in serializado
    assert ".json" not in serializado
    assert ".db" not in serializado
    assert ".sqlite" not in serializado


def test_resposta_nao_expoe_ids_internos(client):
    _post(client, "selic")
    body = _post(client, "selic")
    serializado = str(body)
    # Heurística: UUIDs e IDs hex longos não devem aparecer na resposta.
    assert not re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        serializado,
        re.IGNORECASE,
    )


def test_primeira_consulta_nao_inventa_historico(client):
    """A SPEC proíbe inventar briefings que nunca aconteceram."""
    body = _post(client, "tema_que_nunca_foi_consultado_antes_xyz")
    assert body["memoria"]["briefings_anteriores_consultados"] == 0
    assert body["memoria"]["data_briefing_mais_antigo"] is None
    assert body["memoria"]["primeira_vez"] is True


def test_briefing_atual_nao_e_substituido_por_memoria(client):
    """Memória enriquece, não substitui o briefing coletado hoje."""
    _post(client, "câmbio")
    body = _post(client, "câmbio")
    # O briefing fake injetado pelo mock deve continuar aparecendo.
    assert "Briefing fake" in body["briefing"]
