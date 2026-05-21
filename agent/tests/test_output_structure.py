"""Estrutura do output do endpoint /api/briefing após a memória.

Conforme a SPEC, a resposta deve incluir, além dos campos atuais,
metadados de memória.
"""


def _post(client, tema="dolar", modo="simples"):
    resp = client.post("/api/briefing", json={"tema": tema, "modo": modo})
    assert resp.status_code == 200
    return resp.json()


def test_campos_originais_presentes(client):
    body = _post(client)
    assert "briefing" in body
    assert "tempo_ms" in body
    assert "num_chamadas" in body
    assert "modo" in body


def test_briefing_e_string_nao_vazia(client):
    body = _post(client)
    assert isinstance(body["briefing"], str)
    assert body["briefing"].strip() != ""


def test_tempo_ms_e_inteiro_nao_negativo(client):
    body = _post(client)
    assert isinstance(body["tempo_ms"], int)
    assert body["tempo_ms"] >= 0


def test_num_chamadas_e_inteiro_positivo(client):
    body = _post(client)
    assert isinstance(body["num_chamadas"], int)
    assert body["num_chamadas"] >= 1


def test_resposta_contem_metadados_de_memoria(client):
    body = _post(client)
    assert "memoria" in body, "resposta deve conter bloco de metadados de memória"


def test_metadados_memoria_tem_briefings_anteriores_consultados(client):
    body = _post(client)
    memoria = body["memoria"]
    assert "briefings_anteriores_consultados" in memoria
    assert isinstance(memoria["briefings_anteriores_consultados"], int)
    assert memoria["briefings_anteriores_consultados"] >= 0


def test_metadados_memoria_tem_primeira_vez(client):
    body = _post(client)
    memoria = body["memoria"]
    assert "primeira_vez" in memoria
    assert isinstance(memoria["primeira_vez"], bool)


def test_metadados_memoria_tem_data_briefing_mais_antigo(client):
    body = _post(client)
    memoria = body["memoria"]
    assert "data_briefing_mais_antigo" in memoria


def test_metadados_memoria_tem_disponivel(client):
    body = _post(client)
    memoria = body["memoria"]
    assert "disponivel" in memoria
    assert isinstance(memoria["disponivel"], bool)
