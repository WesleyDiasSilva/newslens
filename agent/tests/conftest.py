"""Fixtures compartilhadas para a suite de testes.

A funcionalidade de memória ainda não foi implementada. As fixtures aqui
são tolerantes a essa ausência: o que falha é a asserção, não a coleta.

Isolamento de schema:
    Os testes operam num schema "test" separado do schema "public" (onde
    moram os dados de seed). A fixture _setup_test_schema cria o schema e
    define PGOPTIONS=-c search_path=test,public no env — libpq aplica isso
    em toda conexão psycopg2 que não passa `options=` explicitamente, o que
    inclui memory._connect. memory.py não precisa saber que existe schema
    separado.
"""
import os
from unittest.mock import patch

import psycopg2
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

load_dotenv()

import main


FAKE_BRIEFING = (
    "# Briefing fake\n\n"
    "## 1. Notícia exemplo\n"
    "Resumo curto.\n"
    "Fonte: https://exemplo.com\n"
)


def _admin_conn():
    """Conexão sem search_path customizado, pra DDL de schema."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "newslens"),
        password=os.getenv("POSTGRES_PASSWORD", "newslens_dev"),
        dbname=os.getenv("POSTGRES_DB", "newslens"),
    )


@pytest.fixture(scope="session", autouse=True)
def _setup_test_schema():
    """Cria o schema 'test' e direciona conexões da sessão pra ele via PGOPTIONS.

    Teardown dropa 'test CASCADE', preservando 'public.briefings' (seed).
    """
    conn = _admin_conn()
    with conn, conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS test")
    conn.close()

    os.environ["PGOPTIONS"] = "-c search_path=test,public"
    yield
    os.environ.pop("PGOPTIONS", None)

    conn = _admin_conn()
    with conn, conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS test CASCADE")
    conn.close()


@pytest.fixture(autouse=True)
def mock_chamar_agente():
    """Evita chamar a API real do Anthropic/Tavily em testes."""
    with patch.object(main, "chamar_agente", return_value=FAKE_BRIEFING):
        yield


@pytest.fixture(autouse=True)
def reset_memory():
    """Limpa a memória entre testes, se ela existir."""
    for attr in ("memory_store", "memoria", "_memory"):
        store = getattr(main, attr, None)
        if store is not None and hasattr(store, "clear"):
            store.clear()
    yield
    for attr in ("memory_store", "memoria", "_memory"):
        store = getattr(main, attr, None)
        if store is not None and hasattr(store, "clear"):
            store.clear()


@pytest.fixture
def client():
    with TestClient(main.app) as c:
        yield c
