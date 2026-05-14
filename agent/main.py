from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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


@app.post("/api/briefing")
async def criar_briefing(req: BriefingRequest):
    briefing = (
        f"Briefing sobre '{req.tema}':\n\n"
        "Este é um texto fictício de exemplo gerado para fins de prototipação. "
        "O tema abordado apresenta múltiplas perspectivas relevantes para análise. "
        "Pontos principais identificados: contexto histórico, impacto atual e "
        "tendências futuras. Conteúdo meramente ilustrativo, sem valor jornalístico real."
    )
    return {"briefing": briefing}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
