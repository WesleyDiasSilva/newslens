# NewsLens

## O projeto
Agente de briefing de notícias configurável por tema.
Frontend React conectado a um backend FastAPI que busca notícias via Tavily.

## Stack
- Frontend: React 19 + Vite + Tailwind v4
- Backend: Python + FastAPI + Uvicorn
- Busca: Tavily API
- Banco vetorial: Qdrant via Docker (a partir da Aula 3)
- Observabilidade: LangFuse (a partir da Aula 5)

## Estrutura
- frontend/ — interface React
- agent/ — servidor FastAPI e lógica do agente
- docker-compose.yml — serviços externos

## Convenções
- Backend em Python, frontend em Node/React
- Variáveis de ambiente sempre no .env — nunca hardcoded
- .env nunca vai pro git
- CORS liberado apenas para localhost durante desenvolvimento
