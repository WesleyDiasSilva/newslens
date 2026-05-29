"""Infraestrutura de memória semântica: persiste briefings e busca por similaridade.

Funções públicas:
- init_db(): habilita pgvector e cria a tabela briefings (idempotente).
- save_briefing(tema, conteudo): gera embedding e persiste.
- search_similar(tema, limit=3): retorna briefings mais próximos por distância coseno.
"""
import os

import psycopg2
from openai import OpenAI


def _connect():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "newslens"),
        password=os.getenv("POSTGRES_PASSWORD", "newslens_dev"),
        dbname=os.getenv("POSTGRES_DB", "newslens"),
    )


def _embed(texto: str) -> list[float]:
    client = OpenAI()
    resp = client.embeddings.create(model="text-embedding-3-small", input=texto)
    return resp.data[0].embedding


def _vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(repr(float(v)) for v in vec) + "]"


def init_db() -> None:
    conn = _connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS briefings (
                    id SERIAL PRIMARY KEY,
                    tema TEXT NOT NULL,
                    conteudo TEXT NOT NULL,
                    embedding vector(1536),
                    criado_em TIMESTAMP DEFAULT NOW()
                )
                """
            )
    finally:
        conn.close()


def save_briefing(tema: str, conteudo: str) -> None:
    embedding = _embed(conteudo)
    conn = _connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO briefings (tema, conteudo, embedding) VALUES (%s, %s, %s)",
                (tema, conteudo, _vector_literal(embedding)),
            )
    finally:
        conn.close()


def search_similar(tema: str, limit: int = 3) -> list[dict]:
    query_vec = _embed(tema)
    conn = _connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tema, conteudo, criado_em
                FROM briefings
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (_vector_literal(query_vec), limit),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    return [
        {"id": r[0], "tema": r[1], "conteudo": r[2], "criado_em": r[3]}
        for r in rows
    ]
