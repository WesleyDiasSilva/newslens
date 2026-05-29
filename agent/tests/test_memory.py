"""Testes da infraestrutura de memória (agent/memory.py).

Pré-requisitos para rodar:
- Container do Postgres com pgvector ativo (docker compose up -d db).
- Variáveis POSTGRES_* configuradas (.env do agent).

A OpenAI é mockada em todos os testes — nenhuma chamada externa é feita.

Premissa de design (validada por estes testes):
- memory.py importa o cliente como `from openai import OpenAI` e instancia
  dentro das funções (não no topo do módulo), para que o patch funcione.
- save_briefing(tema, conteudo) gera embedding do conteúdo a ser persistido.
- search_similar(tema, limit=3) gera embedding do tema e busca por
  distância coseno, retornando lista de dicts com ao menos "tema" e
  "conteudo".
"""
import os
from unittest.mock import MagicMock, patch

import psycopg2
import pytest

import memory


def _pg_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "newslens"),
        password=os.getenv("POSTGRES_PASSWORD", "newslens_dev"),
        dbname=os.getenv("POSTGRES_DB", "newslens"),
    )


@pytest.fixture
def db():
    """Garante schema inicializado e tabela briefings limpa por teste."""
    memory.init_db()
    conn = _pg_conn()
    with conn, conn.cursor() as cur:
        cur.execute("TRUNCATE briefings RESTART IDENTITY")
    conn.close()
    yield


@pytest.fixture
def mock_openai_embedding():
    """Controla o vetor retornado e inspeciona model/input passados."""
    state = {"vector": [0.1] * 1536, "model_used": None, "input_used": None}

    def fake_create(model, input, **kwargs):
        state["model_used"] = model
        state["input_used"] = input
        resp = MagicMock()
        resp.data = [MagicMock(embedding=state["vector"])]
        return resp

    with patch("memory.OpenAI") as mock_cls:
        instance = MagicMock()
        instance.embeddings.create = fake_create
        mock_cls.return_value = instance
        yield state


# --- init_db -----------------------------------------------------------------


def test_init_db_habilita_extensao_vector():
    memory.init_db()
    conn = _pg_conn()
    with conn, conn.cursor() as cur:
        cur.execute("SELECT extname FROM pg_extension WHERE extname='vector'")
        row = cur.fetchone()
    conn.close()
    assert row is not None


def test_init_db_cria_tabela_briefings_com_colunas_esperadas():
    memory.init_db()
    conn = _pg_conn()
    with conn, conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='briefings'"
        )
        cols = {r[0] for r in cur.fetchall()}
    conn.close()
    assert {"id", "tema", "conteudo", "embedding", "criado_em"}.issubset(cols)


def test_init_db_e_idempotente():
    memory.init_db()
    memory.init_db()  # não deve levantar


# --- save_briefing -----------------------------------------------------------


def test_save_briefing_persiste_tema_e_conteudo(db, mock_openai_embedding):
    memory.save_briefing("inteligência artificial", "Resumo das novidades de IA")
    conn = _pg_conn()
    with conn, conn.cursor() as cur:
        cur.execute("SELECT tema, conteudo FROM briefings")
        rows = cur.fetchall()
    conn.close()
    assert rows == [("inteligência artificial", "Resumo das novidades de IA")]


def test_save_briefing_usa_modelo_text_embedding_3_small(db, mock_openai_embedding):
    memory.save_briefing("qualquer tema", "qualquer conteúdo")
    assert mock_openai_embedding["model_used"] == "text-embedding-3-small"


def test_save_briefing_armazena_embedding_de_1536_dimensoes(db, mock_openai_embedding):
    mock_openai_embedding["vector"] = [0.42] * 1536
    memory.save_briefing("tema", "conteúdo")
    conn = _pg_conn()
    with conn, conn.cursor() as cur:
        cur.execute("SELECT embedding FROM briefings LIMIT 1")
        (embedding,) = cur.fetchone()
    conn.close()
    # pgvector serializa como '[v1,v2,...,v1536]' — 1535 vírgulas separam 1536 valores.
    assert isinstance(embedding, str)
    assert embedding.count(",") == 1535


def test_save_briefing_grava_criado_em_automaticamente(db, mock_openai_embedding):
    memory.save_briefing("tema", "conteúdo")
    conn = _pg_conn()
    with conn, conn.cursor() as cur:
        cur.execute("SELECT criado_em FROM briefings LIMIT 1")
        (criado_em,) = cur.fetchone()
    conn.close()
    assert criado_em is not None


# --- search_similar ----------------------------------------------------------


def test_search_similar_retorna_lista_vazia_quando_banco_vazio(db, mock_openai_embedding):
    assert memory.search_similar("qualquer") == []


def test_search_similar_respeita_limit(db, mock_openai_embedding):
    for i in range(5):
        memory.save_briefing(f"tema-{i}", f"conteúdo {i}")
    results = memory.search_similar("busca", limit=2)
    assert len(results) == 2


def test_search_similar_usa_limit_default_de_3(db, mock_openai_embedding):
    for i in range(5):
        memory.save_briefing(f"tema-{i}", f"conteúdo {i}")
    assert len(memory.search_similar("busca")) == 3


def test_search_similar_ordena_por_proximidade_cosseno(db, mock_openai_embedding):
    # Briefing A — vetor "longe" da consulta
    mock_openai_embedding["vector"] = [1.0] + [0.0] * 1535
    memory.save_briefing("longe", "vetor base eixo 0")

    # Briefing B — vetor "perto" da consulta
    mock_openai_embedding["vector"] = [0.0, 1.0] + [0.0] * 1534
    memory.save_briefing("perto", "vetor base eixo 1")

    # Consulta — vetor idêntico ao "perto"
    mock_openai_embedding["vector"] = [0.0, 1.0] + [0.0] * 1534
    results = memory.search_similar("consulta", limit=2)

    assert len(results) == 2
    primeiro = results[0]
    tema = primeiro["tema"] if isinstance(primeiro, dict) else primeiro.tema
    assert tema == "perto"


def test_search_similar_gera_embedding_da_query_via_openai(db, mock_openai_embedding):
    memory.search_similar("inteligência artificial")
    assert mock_openai_embedding["model_used"] == "text-embedding-3-small"
