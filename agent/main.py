import os
import time
from typing import Literal

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
    modo: Literal["simples", "subagentes"] = "simples"

    @field_validator("tema")
    @classmethod
    def _tema_nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("tema não pode ser vazio ou conter apenas espaços")
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


@app.post("/api/briefing")
async def criar_briefing(req: BriefingRequest):
    inicio = time.perf_counter()
    num_chamadas = 0

    memoria_disponivel = True
    historico_dados: dict = {"total": 0, "mais_antigo": None, "top_n": []}
    try:
        historico_dados = memory_store.get(req.tema)
    except Exception:
        memoria_disponivel = False

    historico = historico_dados["top_n"]
    if historico:
        system_prompt = (
            SYSTEM_PROMPT
            + RAG_INSTRUCOES
            + "\n\n"
            + _montar_contexto_historico(historico)
        )
    else:
        system_prompt = SYSTEM_PROMPT

    if req.modo == "simples":
        instrucao = (
            f"Tema: {req.tema}\n\n"
            "Faça 1 busca no Tavily sobre este tema e monte o briefing "
            "no formato pedido."
        )
        briefing = chamar_agente(instrucao, system_prompt)
        num_chamadas = 1
    else:
        angulos = [
            (
                "Visão geral",
                f"Faça 1 busca no Tavily sobre o tema '{req.tema}' (visão geral) "
                "e liste as notícias encontradas no formato pedido.",
            ),
            (
                "Últimas notícias",
                f"Faça 1 busca no Tavily sobre '{req.tema} últimas notícias' "
                "e liste as notícias encontradas no formato pedido.",
            ),
            (
                "Análise",
                f"Faça 1 busca no Tavily sobre '{req.tema} análise' "
                "e liste as notícias encontradas no formato pedido.",
            ),
        ]
        partes: list[str] = []
        for i, (rotulo, instrucao) in enumerate(angulos):
            if i > 0:
                time.sleep(0.5)
            resultado = chamar_agente(instrucao, system_prompt)
            partes.append(f"## {rotulo}\n\n{resultado}")
            num_chamadas += 1
        briefing = (
            f"Briefing sobre '{req.tema}'\n\n" + "\n\n".join(partes)
        )

    try:
        memory_store.add(req.tema, briefing)
    except Exception:
        memoria_disponivel = False

    tempo_ms = int((time.perf_counter() - inicio) * 1000)

    mais_antigo = historico_dados["mais_antigo"]
    data_briefing_mais_antigo = (
        mais_antigo.date().isoformat() if mais_antigo is not None else None
    )

    print(
        f"[briefing] modo={req.modo} tema={req.tema!r} "
        f"chamadas={num_chamadas} briefings_anteriores={historico_dados['total']} "
        f"disponivel={memoria_disponivel} tempo_ms={tempo_ms}",
        flush=True,
    )

    return {
        "briefing": briefing,
        "tempo_ms": tempo_ms,
        "num_chamadas": num_chamadas,
        "modo": req.modo,
        "memoria": {
            "briefings_anteriores_consultados": historico_dados["total"],
            "primeira_vez": historico_dados["total"] == 0,
            "data_briefing_mais_antigo": data_briefing_mais_antigo,
            "disponivel": memoria_disponivel,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
