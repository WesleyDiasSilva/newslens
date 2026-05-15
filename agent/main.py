import os
import time
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from tavily import TavilyClient

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise RuntimeError("TAVILY_API_KEY não definida no .env")

tavily = TavilyClient(api_key=TAVILY_API_KEY)

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


def buscar_tavily(query: str) -> list[dict]:
    try:
        resposta = tavily.search(query=query, topic="news", max_results=5)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao consultar Tavily: {exc}")
    return resposta.get("results", []) if isinstance(resposta, dict) else []


def deduplicar(resultados: list[dict]) -> list[dict]:
    vistos: set[str] = set()
    unicos: list[dict] = []
    for item in resultados:
        url = item.get("url") or ""
        if url and url in vistos:
            continue
        vistos.add(url)
        unicos.append(item)
    return unicos


def formatar_briefing(tema: str, resultados: list[dict]) -> str:
    if not resultados:
        return f"Nenhuma notícia recente encontrada sobre '{tema}'."

    linhas = [f"Briefing sobre '{tema}'", ""]
    for i, item in enumerate(resultados, start=1):
        titulo = item.get("title") or "(sem título)"
        resumo = item.get("content") or "(sem resumo)"
        fonte = item.get("url") or "(sem fonte)"
        linhas.append(f"{i}. {titulo}")
        linhas.append(f"   Resumo: {resumo}")
        linhas.append(f"   Fonte: {fonte}")
        linhas.append("")
    return "\n".join(linhas).rstrip()


@app.post("/api/briefing")
async def criar_briefing(req: BriefingRequest):
    inicio = time.perf_counter()
    num_chamadas = 0

    if req.modo == "simples":
        resultados = buscar_tavily(req.tema)
        num_chamadas = 1
    else:
        queries = [
            req.tema,
            f"{req.tema} últimas notícias",
            f"{req.tema} análise",
        ]
        acumulado: list[dict] = []
        for i, q in enumerate(queries):
            if i > 0:
                time.sleep(0.5)
            acumulado.extend(buscar_tavily(q))
            num_chamadas += 1
        resultados = deduplicar(acumulado)

    briefing = formatar_briefing(req.tema, resultados)
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
