from fastapi import FastAPI

# Importa os roteadores criados na pasta de rotas.
from app.api.routes.agendamentos import router as agendamentos_router
from app.api.routes.health import router as health_router

from app.repositories.agendamento_repository import AgendamentoRepositorio
from app.services.agendamento_service import AgendamentoService

app = FastAPI(
    title="API de Agenda de Visitas",
    description="API para organizar visitas a imóveis."
)

# Cria o repositório e o serviço para esta instância da aplicação.
app.state.agendamento_service = AgendamentoService(AgendamentoRepositorio())

# Conecta os roteadores à aplicação principal.
app.include_router(health_router)
app.include_router(agendamentos_router)

# Define uma rota simples para confirmar que a aplicação está respondendo.
@app.get("/")
def pagina_inicial() -> dict[str, str]:
    return {"mensagem": "API de Agenda de Visitas está funcionando"}
