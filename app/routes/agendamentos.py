from datetime import date

from fastapi import APIRouter, Query, Request, status

from app.schemas.agendamento import AgendamentoCria, AgendamentoLeitura
from app.services.agendamento_service import AgendamentoService

# Agrupa os endpoints relacionados a agendamentos.
router = APIRouter()


# Cria um agendamento e responde com HTTP 201 (Created).
@router.post("/api/agendamentos",response_model=AgendamentoLeitura,status_code=status.HTTP_201_CREATED)
def criar_agendamento(dados: AgendamentoCria, request: Request) -> AgendamentoLeitura:
    # Busca o serviço criado junto com a aplicação.
    servico: AgendamentoService = request.app.state.agendamento_service
    # Delega a criação para a camada de serviço.
    return servico.criar(dados)


# Lista agendamentos de um corretor em uma data, em ordem cronológica.
@router.get("/api/agendamentos",response_model=list[AgendamentoLeitura])
def listar_agendamentos(request: Request, corretor_id: str = Query(alias="corretorId", min_length=1), dia: date = Query(alias="data")) -> list[AgendamentoLeitura]:
    # Busca o serviço criado junto com a aplicação.
    servico: AgendamentoService = request.app.state.agendamento_service
    # O repositório filtra os resultados e os devolve ordenados pelo início.
    return servico.listar(corretor_id, dia)
