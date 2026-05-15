# NewsLens

## O projeto
Agente de briefing de notícias configurável por tema.
Frontend React conectado a um backend FastAPI.

## Stack
- Frontend: React 19 + Vite + Tailwind v4
- Backend: Python + FastAPI + Uvicorn

## Estrutura
- frontend/ — interface React
- agent/ — servidor FastAPI e lógica do agente
- docker-compose.yml — serviços externos (a partir da Aula 3)

## Convenções
- Variáveis de ambiente sempre no .env — nunca hardcoded
- .env nunca vai pro git
