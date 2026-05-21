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

## Padrões de qualidade obrigatórios

- Sempre escreva testes antes da implementação (TDD)
- Nunca implemente sem spec aprovada (SDD)
- Para tasks que envolvam mais de 2 arquivos, gere um plan antes de agir

## Comportamento esperado

- Se receber uma tarefa de implementação sem spec: recuse e peça a spec primeiro
- Se receber uma tarefa de implementação sem testes: recuse e peça os testes primeiro
- Se receber uma tarefa grande: ative plan mode automaticamente

## Slash commands

/plan-feature
- Ativa plan mode
- Lista arquivos impactados
- Lista testes que precisam ser criados ou atualizados
- Pausa para aprovação antes de qualquer mudança

/run-tests
- Roda a suite completa em agent/tests/
- Reporta cada falha com localização exata e o que era esperado vs o que veio

/review-pr
- Revisa contra as convenções do CLAUDE.md
- Aponta funções sem type hints
- Aponta cobertura de testes abaixo do esperado
- Aponta variáveis de ambiente hardcoded
