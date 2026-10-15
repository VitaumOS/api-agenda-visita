from fastapi import APIRouter, Request, status

from app.schemas.agendamento import AgendamentoCria, AgendamentoLeitura
from app.services.agendamento_service import AgendamentoService

# Agrupa os endpoints relacionados a agendamentos.
router = APIRouter()


# Cria um agendamento e responde com HTTP 201 (Created).
@router.post(
    "/api/agendamentos",
    response_model=AgendamentoLeitura,
    status_code=status.HTTP_201_CREATED,
)
def criar_agendamento(dados: AgendamentoCria, request: Request) -> AgendamentoLeitura:
    # Busca o serviço criado junto com a aplicação.
    servico: AgendamentoService = request.app.state.agendamento_service
    # Delega a criação para a camada de serviço.
    return servico.criar(dados)
