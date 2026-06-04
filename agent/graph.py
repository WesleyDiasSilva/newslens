"""Grafo LangGraph do NewsLens.

Fluxo:
    START → buscar_noticias → avaliar_qualidade → (conditional)
      ├─ qualidade_suficiente=True  → recuperar_historico → gerar_briefing → salvar_briefing → END
      └─ qualidade_suficiente=False → refinar_busca → recuperar_historico → gerar_briefing → salvar_briefing → END

A camada de memória é acessada via `main.memory_store` (handle único,
patchável em testes) — não importa de `memory.py` direto.
"""
import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

import main


class NewsLensState(TypedDict):
    tema: str
    noticias: str
    qualidade_suficiente: bool
    historico: list
    briefing: str
    memoria: dict
    num_chamadas: Annotated[int, operator.add]


SEARCH_SYSTEM = (
    "Você é um agente de busca de notícias. Quando receber um tema, "
    "use a tool de busca do Tavily para encontrar notícias recentes "
    "e relevantes. Retorne o resultado bruto da busca em texto corrido — "
    "título, resumo e fonte de cada notícia. Não monte briefing formatado."
)

QUALIDADE_MINIMA_CHARS = 2500


def buscar_noticias(state: NewsLensState) -> dict:
    instrucao = (
        f"Tema: {state['tema']}\n\n"
        "Faça 1 busca no Tavily sobre este tema e retorne as notícias encontradas."
    )
    noticias = main.chamar_agente(instrucao, system=SEARCH_SYSTEM)
    return {"noticias": noticias, "num_chamadas": 1}


def avaliar_qualidade(state: NewsLensState) -> dict:
    resultado = len(state.get("noticias", "")) >= QUALIDADE_MINIMA_CHARS
    print(f"[grafo] avaliar_qualidade: {len(state.get('noticias', ''))} chars → {'suficiente' if resultado else 'insuficiente'}")
    return {"qualidade_suficiente": resultado}


def refinar_busca(state: NewsLensState) -> dict:
    print(f"[grafo] refinar_busca: refinando busca para '{state['tema']} últimas notícias'")
    instrucao = (
        f"Tema: {state['tema']} últimas notícias\n\n"
        "Faça 1 busca ampliada no Tavily e retorne as notícias encontradas."
    )
    noticias = main.chamar_agente(instrucao, system=SEARCH_SYSTEM)
    return {"noticias": noticias, "num_chamadas": 1}


def recuperar_historico(state: NewsLensState) -> dict:
    tema = state["tema"]
    try:
        dados = main.memory_store.get(tema)
    except Exception:
        return {
            "historico": [],
            "memoria": {
                "briefings_anteriores_consultados": 0,
                "primeira_vez": True,
                "data_briefing_mais_antigo": None,
                "disponivel": False,
            },
        }
    mais_antigo = dados["mais_antigo"]
    data_briefing_mais_antigo = (
        mais_antigo.date().isoformat() if mais_antigo is not None else None
    )
    return {
        "historico": dados["top_n"],
        "memoria": {
            "briefings_anteriores_consultados": dados["total"],
            "primeira_vez": dados["total"] == 0,
            "data_briefing_mais_antigo": data_briefing_mais_antigo,
            "disponivel": True,
        },
    }


def gerar_briefing(state: NewsLensState) -> dict:
    historico = state.get("historico") or []
    if historico:
        system_prompt = (
            main.SYSTEM_PROMPT
            + main.RAG_INSTRUCOES
            + "\n\n"
            + main._montar_contexto_historico(historico)
        )
    else:
        system_prompt = main.SYSTEM_PROMPT
    instrucao = (
        f"Tema: {state['tema']}\n\n"
        "As notícias já foram coletadas e estão abaixo. "
        "Monte o briefing no formato pedido a partir delas:\n\n"
        f"{state.get('noticias', '')}"
    )
    briefing = main.chamar_agente(instrucao, system=system_prompt)
    return {"briefing": briefing, "num_chamadas": 1}


def salvar_briefing(state: NewsLensState) -> dict:
    try:
        main.memory_store.add(state["tema"], state["briefing"])
        return {}
    except Exception:
        memoria_atual = state.get("memoria") or {}
        return {"memoria": {**memoria_atual, "disponivel": False}}


def route_qualidade(state: NewsLensState) -> str:
    return (
        "recuperar_historico"
        if state.get("qualidade_suficiente")
        else "refinar_busca"
    )


def build_graph():
    builder = StateGraph(NewsLensState)

    builder.add_node("buscar_noticias", buscar_noticias)
    builder.add_node("avaliar_qualidade", avaliar_qualidade)
    builder.add_node("refinar_busca", refinar_busca)
    builder.add_node("recuperar_historico", recuperar_historico)
    builder.add_node("gerar_briefing", gerar_briefing)
    builder.add_node("salvar_briefing", salvar_briefing)

    builder.set_entry_point("buscar_noticias")
    builder.add_edge("buscar_noticias", "avaliar_qualidade")
    builder.add_conditional_edges(
        "avaliar_qualidade",
        route_qualidade,
        {
            "recuperar_historico": "recuperar_historico",
            "refinar_busca": "refinar_busca",
        },
    )
    builder.add_edge("refinar_busca", "recuperar_historico")
    builder.add_edge("recuperar_historico", "gerar_briefing")
    builder.add_edge("gerar_briefing", "salvar_briefing")
    builder.add_edge("salvar_briefing", END)

    # TODO: trocar por PostgresSaver em produção
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    graph = build_graph()
    print("Nodes do grafo NewsLens:")
    for node_name in graph.nodes:
        print(f"  - {node_name}")
