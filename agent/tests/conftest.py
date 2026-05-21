"""Fixtures compartilhadas para a suite de testes.

A funcionalidade de memória ainda não foi implementada. As fixtures aqui
são tolerantes a essa ausência: o que falha é a asserção, não a coleta.
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import main


FAKE_BRIEFING = (
    "# Briefing fake\n\n"
    "## 1. Notícia exemplo\n"
    "Resumo curto.\n"
    "Fonte: https://exemplo.com\n"
)


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
