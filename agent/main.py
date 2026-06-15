import os
import time
import uuid
from typing import Optional

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

import memory
from memory import (
    contar_por_tema,
    init_db,
    save_briefing,
    search_similar,  # noqa: F401  (kept for backwards-compat / external imports)
    search_similar_por_tema,
)
# `from graph import build_graph` é importado no fim do módulo, após
# memory_store / chamar_agente / SYSTEM_PROMPT estarem definidos —
# graph.py importa main e acessa esses símbolos.

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise RuntimeError("TAVILY_API_KEY não definida no .env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise RuntimeError("ANTHROPIC_API_KEY não definida no .env")

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

MODEL = "claude-haiku-4-5"
MCP_BETA = "mcp-client-2025-04-04"

TAVILY_MCP = {
    "type": "url",
    "url": "https://mcp.tavily.com/mcp/",
    "name": "tavily",
    "authorization_token": TAVILY_API_KEY,
}

SYSTEM_PROMPT = (
    "Você é um agente de briefing de notícias. Quando receber um tema, "
    "use a tool de busca do Tavily para encontrar as notícias mais recentes "
    "e relevantes. Retorne um briefing organizado em português com título, "
    "resumo e fonte de cada notícia. Máximo de 5 notícias."
)

RAG_INSTRUCOES = (
    "\n\nVocê tem acesso a briefings anteriores sobre este mesmo tema (abaixo). "
    "Use-os como referência temporal para identificar o que mudou desde a última "
    "consulta. Ao montar o briefing atual, destaque explicitamente o que é novo, "
    "o que evoluiu e o que foi atualizado em relação ao histórico — sem repetir "
    "notícias que já apareceram nos briefings anteriores como se fossem novidade. "
    "Mantenha o formato padrão (título, resumo e fonte por notícia, máximo de 5)."
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MemoryStore:
    """Handle único da camada de memória — patchável em testes via `main.memory_store`.

    Em caso de falha de qualquer método (banco indisponível, OpenAI offline),
    o endpoint captura a exceção e entra em fallback (disponivel=False).
    """

    def get(self, tema: str) -> dict:
        total, mais_antigo = contar_por_tema(tema)
        top_n = search_similar_por_tema(tema, limit=3) if total > 0 else []
        return {"total": total, "mais_antigo": mais_antigo, "top_n": top_n}

    def add(self, tema: str, conteudo: str) -> None:
        save_briefing(tema, conteudo)

    def clear(self) -> None:
        """Trunca briefings — usado pelo conftest entre testes.

        Em produção, o search_path default leva ao schema public e isso
        apagaria dados reais. Conftest dos testes redireciona pra schema
        `test` via PGOPTIONS, então o blast radius fica isolado.
        """
        init_db()
        conn = memory._connect()
        try:
            with conn, conn.cursor() as cur:
                cur.execute("TRUNCATE briefings RESTART IDENTITY")
        finally:
            conn.close()


memory_store = MemoryStore()


@app.on_event("startup")
def _startup_init_db() -> None:
    init_db()


class BriefingRequest(BaseModel):
    tema: str

    @field_validator("tema")
    @classmethod
    def _tema_nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("tema não pode ser vazio ou conter apenas espaços")
        return v


class RetomarRequest(BaseModel):
    thread_id: str

    @field_validator("thread_id")
    @classmethod
    def _thread_id_nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("thread_id não pode ser vazio")
        return v


def extrair_texto(response) -> str:
    partes: list[str] = []
    for bloco in response.content:
        if getattr(bloco, "type", None) == "text":
            texto = getattr(bloco, "text", "")
            if texto:
                partes.append(texto)
    return "\n".join(partes).strip()


def chamar_agente(instrucao: str, system: str = SYSTEM_PROMPT) -> str:
    try:
        response = anthropic_client.beta.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": instrucao}],
            mcp_servers=[TAVILY_MCP],
            betas=[MCP_BETA],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Falha ao consultar Anthropic: {exc}",
        )
    return extrair_texto(response)


def _montar_contexto_historico(briefings: list[dict]) -> str:
    blocos = []
    for b in briefings:
        criado = b["criado_em"]
        data = criado.date() if hasattr(criado, "date") else criado
        blocos.append(
            f"--- Briefing de {data} (tema: {b['tema']}) ---\n{b['conteudo']}"
        )
    return "Briefings anteriores sobre este tema:\n\n" + "\n\n".join(blocos)


from graph import build_graph, langfuse_handler
from langgraph.types import Command

graph = build_graph()


_MEMORIA_FALLBACK = {
    "briefings_anteriores_consultados": 0,
    "primeira_vez": True,
    "data_briefing_mais_antigo": None,
    "disponivel": False,
}


def _extrair_payload_interrupt(resultado: dict) -> Optional[dict]:
    """Devolve o dict passado a interrupt() se o grafo pausou; senão None."""
    interrupts = resultado.get("__interrupt__")
    if not interrupts:
        return None
    primeiro = interrupts[0]
    valor = getattr(primeiro, "value", primeiro)
    return valor if isinstance(valor, dict) else {"valor": valor}


@app.post("/api/briefing")
def criar_briefing(req: BriefingRequest):
    inicio = time.perf_counter()

    thread_id = f"{req.tema}::{uuid.uuid4().hex[:12]}"
    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": [langfuse_handler],
    }
    input_state = {"tema": req.tema, "num_chamadas": 0}
    resultado = graph.invoke(input_state, config=config)

    tempo_ms = int((time.perf_counter() - inicio) * 1000)

    payload_interrupt = _extrair_payload_interrupt(resultado)
    if payload_interrupt is not None:
        memoria_out = payload_interrupt.get("memoria") or dict(_MEMORIA_FALLBACK)
        print(
            f"[briefing] tema={req.tema!r} status=aguardando_aprovacao "
            f"thread_id={thread_id} tempo_ms={tempo_ms}",
            flush=True,
        )
        return {
            "status": "aguardando_aprovacao",
            "noticias": payload_interrupt.get("noticias", ""),
            "thread_id": thread_id,
            "tempo_ms": tempo_ms,
            "memoria": memoria_out,
        }

    memoria_out = resultado.get("memoria") or dict(_MEMORIA_FALLBACK)
    num_chamadas = resultado.get("num_chamadas", 0)

    print(
        f"[briefing] tema={req.tema!r} chamadas={num_chamadas} "
        f"briefings_anteriores={memoria_out.get('briefings_anteriores_consultados', 0)} "
        f"disponivel={memoria_out.get('disponivel', False)} tempo_ms={tempo_ms}",
        flush=True,
    )

    return {
        "briefing": resultado.get("briefing", ""),
        "tempo_ms": tempo_ms,
        "num_chamadas": num_chamadas,
        "memoria": memoria_out,
    }


@app.post("/api/briefing/retomar")
def retomar_briefing(req: RetomarRequest):
    inicio = time.perf_counter()
    config = {
        "configurable": {"thread_id": req.thread_id},
        "callbacks": [langfuse_handler],
    }

    snapshot = graph.get_state(config)
    if not snapshot.next:
        raise HTTPException(
            status_code=404,
            detail=f"thread_id desconhecido ou já concluído: {req.thread_id}",
        )

    resultado = graph.invoke(Command(resume="aprovado"), config=config)
    tempo_ms = int((time.perf_counter() - inicio) * 1000)

    memoria_out = resultado.get("memoria") or dict(_MEMORIA_FALLBACK)
    num_chamadas = resultado.get("num_chamadas", 0)

    print(
        f"[retomar] thread_id={req.thread_id} chamadas={num_chamadas} "
        f"disponivel={memoria_out.get('disponivel', False)} tempo_ms={tempo_ms}",
        flush=True,
    )

    return {
        "briefing": resultado.get("briefing", ""),
        "tempo_ms": tempo_ms,
        "num_chamadas": num_chamadas,
        "memoria": memoria_out,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
