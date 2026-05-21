"""Casos de borda conforme a SPEC."""
from unittest.mock import patch

import main


def _post(client, tema, modo="simples"):
    resp = client.post("/api/briefing", json={"tema": tema, "modo": modo})
    assert resp.status_code == 200
    return resp.json()


def test_primeira_consulta_de_tema_funciona_sem_historico(client):
    body = _post(client, "tema_nunca_visto_abcdef")
    assert body["briefing"]
    assert body["memoria"]["primeira_vez"] is True


def test_temas_similares_mas_distintos_nao_compartilham_memoria(client):
    """SPEC: 'eleições' e 'eleições 2026' são temas distintos."""
    _post(client, "eleições")
    _post(client, "eleições")
    body = _post(client, "eleições 2026")
    assert body["memoria"]["primeira_vez"] is True
    assert body["memoria"]["briefings_anteriores_consultados"] == 0


def test_memoria_indisponivel_nao_bloqueia_briefing(client):
    """SPEC: degradar para comportamento sem memória, não bloquear."""
    fake_store = type(
        "BrokenStore",
        (),
        {
            "get": lambda self, *a, **k: (_ for _ in ()).throw(
                RuntimeError("indisponível")
            ),
            "add": lambda self, *a, **k: (_ for _ in ()).throw(
                RuntimeError("indisponível")
            ),
            "clear": lambda self: None,
        },
    )()
    # Tenta forçar o store quebrado se a aplicação expuser esse atributo.
    target_attr = None
    for attr in ("memory_store", "memoria", "_memory"):
        if hasattr(main, attr):
            target_attr = attr
            break
    if target_attr is None:
        # Sem atributo de memória ainda implementado: o teste falha
        # informando o contrato esperado.
        assert False, "main deve expor um store de memória patchável"

    with patch.object(main, target_attr, fake_store):
        resp = client.post(
            "/api/briefing", json={"tema": "fallback test"}
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["briefing"]
    assert body["memoria"]["disponivel"] is False


def test_historico_longo_nao_quebra(client):
    for _ in range(20):
        _post(client, "histórico longo")
    body = _post(client, "histórico longo")
    assert body["memoria"]["briefings_anteriores_consultados"] >= 20


def test_consultas_concorrentes_no_mesmo_tema_completam(client):
    """Não deve corromper memória nem retornar erro."""
    import concurrent.futures

    def chamar():
        resp = client.post(
            "/api/briefing", json={"tema": "concorrência"}
        )
        return resp.status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        resultados = list(ex.map(lambda _: chamar(), range(5)))
    assert all(s == 200 for s in resultados)

    body = _post(client, "concorrência")
    # 5 concorrentes + sanity check anterior = pelo menos 5 anteriores.
    assert body["memoria"]["briefings_anteriores_consultados"] >= 5


def test_tema_unicode_preservado(client):
    body1 = _post(client, "café com leite")
    body2 = _post(client, "café com leite")
    assert body1["memoria"]["primeira_vez"] is True
    assert body2["memoria"]["primeira_vez"] is False
