# NewsLens

Agente de briefing de notícias configurável por tema. Desenvolvido ao longo do curso de IA aplicada da Cyrela Tech.

## Pré-requisitos
- Node.js 18+
- Python 3.12+
- Conta no Tavily (tavily.com) para obter a API key

## Instalação

### Backend
```bash
cd agent
pip install -r requirements.txt
cp .env.example .env
# adicione sua TAVILY_API_KEY no .env
```

### Frontend
```bash
cd frontend
npm install
```

## Rodando o projeto

### Backend
```bash
cd agent
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm run dev
```

## Branches
Cada aula tem duas branches de referência:
- `aula/0X-inicio` — estado inicial da aula
- `aula/0X-fim` — entrega final da aula
