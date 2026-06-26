"""Juiz LLM (model-based eval) — avalia FAITHFULNESS de UM briefing.

Roda 1 exemplo de propósito (uma chamada só), pra demonstrar o LLM-as-Judge
com chain-of-thought ao vivo, sem esperar um lote. Precisa de ANTHROPIC_API_KEY.
NÃO usa Tavily/MCP — é uma chamada simples ao modelo.

Uso: python evals/judge.py   (avalia dataset.json[0])
"""
import json, os, sys
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-haiku-4-5"

RUBRICA = (
    "Você é um avaliador rigoroso de fidelidade (faithfulness). "
    "Receberá as NOTÍCIAS-FONTE e um BRIEFING gerado a partir delas. "
    "Avalie SOMENTE se o briefing se sustenta nas notícias-fonte, sem inventar fatos.\n"
    "Critérios: 10 = tudo no briefing tem respaldo na fonte; 0 = inventou a maior parte.\n"
    "IMPORTANTE: raciocine PASSO A PASSO primeiro (chain-of-thought), comparando cada "
    "afirmação do briefing com a fonte; só então dê a nota final.\n"
    "Responda no formato:\nRACIOCÍNIO: <seu raciocínio>\nNOTA: <0-10>"
)

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "dataset.json"), encoding="utf-8") as f:
        item = json.load(f)[0]

    entrada = f"NOTÍCIAS-FONTE:\n{item['noticias']}\n\nBRIEFING:\n{item['briefing']}"
    resp = client.messages.create(
        model=MODEL, max_tokens=1024, system=RUBRICA,
        messages=[{"role": "user", "content": entrada}],
    )
    texto = "\n".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    print(f"\n  Juiz LLM — faithfulness do briefing sobre '{item['tema']}':\n")
    print(texto, "\n")

if __name__ == "__main__":
    main()
