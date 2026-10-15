from fastapi import FastAPI

# Cria a aplicação FastAPI que o servidor Uvicorn vai executar.
app = FastAPI(
    title="API de Agenda de Visitas",
    description="API para organizar visitas a imóveis."
)

# Define uma rota simples para confirmar que a aplicação está respondendo.
@app.get("/")
def pagina_inicial() -> dict[str, str]:
    return {"mensagem": "API de Agenda de Visitas está funcionando"}
