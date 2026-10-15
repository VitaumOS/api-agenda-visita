from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Importa os roteadores criados na pasta de rotas.
from app.api.routes.agendamentos import router as agendamentos_router
from app.api.routes.health import router as health_router

from app.core.exceptions import AgendamentoConflito
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

# Converte erros de validação do FastAPI para o HTTP 400 exigido pelo enunciado.
@app.exception_handler(RequestValidationError)
async def tratar_erro_de_validacao(request: Request, erro: RequestValidationError) -> JSONResponse:
    # Mantém apenas campos simples para que detalhes internos sejam serializáveis.
    detalhes = [
        {
            "loc": item["loc"],
            "msg": item["msg"],
            "type": item["type"],
        }
        for item in erro.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": detalhes},
    )


# Devolve conflitos no formato JSON definido pelo enunciado.
@app.exception_handler(AgendamentoConflito)
async def tratar_conflito(request: Request, erro: AgendamentoConflito) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "status": "conflito",
            "motivo": erro.motivo,
            "sugestoes": erro.sugestoes,
        },
    )

# Define uma rota simples para confirmar que a aplicação está respondendo.
@app.get("/")
def pagina_inicial() -> dict[str, str]:
    return {"mensagem": "API de Agenda de Visitas está funcionando"}
