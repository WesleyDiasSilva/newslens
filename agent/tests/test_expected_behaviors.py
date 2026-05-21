"""Comportamentos esperados conforme a SPEC."""


def _post(client, tema, modo="simples"):
    resp = client.post("/api/briefing", json={"tema": tema, "modo": modo})
    assert resp.status_code == 200
    return resp.json()


def test_primeira_consulta_marca_primeira_vez_true(client):
    body = _post(client, "petrobras")
    assert body["memoria"]["primeira_vez"] is True
    assert body["memoria"]["briefings_anteriores_consultados"] == 0
    assert body["memoria"]["data_briefing_mais_antigo"] is None


def test_segunda_consulta_marca_primeira_vez_false(client):
    _post(client, "petrobras")
    body = _post(client, "petrobras")
    assert body["memoria"]["primeira_vez"] is False
    assert body["memoria"]["briefings_anteriores_consultados"] >= 1


def test_consultas_repetidas_acumulam_historico(client):
    _post(client, "ibovespa")
    _post(client, "ibovespa")
    body = _post(client, "ibovespa")
    assert body["memoria"]["briefings_anteriores_consultados"] >= 2


def test_data_briefing_mais_antigo_preenchida_apos_historico(client):
    _post(client, "selic")
    body = _post(client, "selic")
    assert body["memoria"]["data_briefing_mais_antigo"] is not None


def test_temas_diferentes_tem_memorias_independentes(client):
    _post(client, "petrobras")
    _post(client, "petrobras")
    body = _post(client, "vale")
    assert body["memoria"]["primeira_vez"] is True
    assert body["memoria"]["briefings_anteriores_consultados"] == 0


def test_tema_case_insensitive_compartilha_memoria(client):
    _post(client, "Eleições 2026")
    body = _post(client, "eleições 2026")
    assert body["memoria"]["primeira_vez"] is False
    assert body["memoria"]["briefings_anteriores_consultados"] >= 1


def test_tema_com_espacos_extras_compartilha_memoria(client):
    _post(client, "dólar")
    body = _post(client, "  dólar  ")
    assert body["memoria"]["primeira_vez"] is False
    assert body["memoria"]["briefings_anteriores_consultados"] >= 1


def test_tema_caps_mistas_compartilha_memoria(client):
    _post(client, "INFLAÇÃO")
    body = _post(client, "Inflação")
    assert body["memoria"]["primeira_vez"] is False


def test_briefing_e_persistido_apos_geracao(client):
    """A SPEC exige que cada briefing seja persistido para uso futuro."""
    _post(client, "copom")
    body = _post(client, "copom")
    # 2ª consulta deve enxergar exatamente 1 briefing anterior
    assert body["memoria"]["briefings_anteriores_consultados"] == 1
