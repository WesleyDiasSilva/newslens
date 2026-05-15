import os
import time
from typing import Literal

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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


class BriefingRequest(BaseModel):
    tema: str
    modo: Literal["simples", "subagentes"] = "simples"


def extrair_texto(response) -> str:
    partes: list[str] = []
    for bloco in response.content:
        if getattr(bloco, "type", None) == "text":
            texto = getattr(bloco, "text", "")
            if texto:
                partes.append(texto)
    return "\n".join(partes).strip()


def chamar_agente(instrucao: str) -> str:
    try:
        response = anthropic_client.beta.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
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


@app.post("/api/briefing")
async def criar_briefing(req: BriefingRequest):
    inicio = time.perf_counter()
    num_chamadas = 0

    if req.modo == "simples":
        instrucao = (
            f"Tema: {req.tema}\n\n"
            "Faça 1 busca no Tavily sobre este tema e monte o briefing "
            "no formato pedido."
        )
        briefing = chamar_agente(instrucao)
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
            resultado = chamar_agente(instrucao)
            partes.append(f"## {rotulo}\n\n{resultado}")
            num_chamadas += 1
        briefing = (
            f"Briefing sobre '{req.tema}'\n\n" + "\n\n".join(partes)
        )

    tempo_ms = int((time.perf_counter() - inicio) * 1000)

    print(
        f"[briefing] modo={req.modo} tema={req.tema!r} "
        f"chamadas={num_chamadas} tempo_ms={tempo_ms}",
        flush=True,
    )

    return {
        "briefing": briefing,
        "tempo_ms": tempo_ms,
        "num_chamadas": num_chamadas,
        "modo": req.modo,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
