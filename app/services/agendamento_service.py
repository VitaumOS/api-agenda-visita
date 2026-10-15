from datetime import timedelta
from uuid import uuid4

from fastapi import HTTPException, status

from app.core.config import FUSO_BRASILIA, INICIO_EXPEDIENTE, FIM_EXPEDIENTE
from app.repositories.agendamento_repository import AgendamentoRepositorio
from app.schemas.agendamento import AgendamentoCria, AgendamentoLeitura


# Executa as ações de negócio relacionadas a agendamentos.
class AgendamentoService:
    def __init__(self, repositorio: AgendamentoRepositorio) -> None:
        self.repositorio = repositorio

    # Cria e guarda uma visita usando os dados já validados pelo schema.
    def criar(self, dados: AgendamentoCria) -> AgendamentoLeitura:
        # Converte o horário enviado para o fuso local
        inicio = dados.inicio.astimezone(FUSO_BRASILIA)

        # Calcula o fim usando o início.
        fim = inicio + timedelta(minutes=dados.duracao_minutos)

        # Confere que a visita começa dentro do expediente e termina no mesmo dia.
        if (inicio.time().replace(tzinfo=None) < INICIO_EXPEDIENTE
            or fim.date() != inicio.date()
            or fim.time().replace(tzinfo=None) > FIM_EXPEDIENTE):

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O agendamento deve ocorrer entre 08:00 e 19:00 no horário de Brasília.",
            )

        # Monta a resposta com um identificador temporário único.
        agendamento = AgendamentoLeitura(
            agendamento_id=f"ag-{uuid4().hex[:8]}",
            corretor_id=dados.corretor_id,
            imovel_id=dados.imovel_id,
            inicio=inicio,
            fim=fim,
            status="confirmado",
        )

        self.repositorio.adicionar(agendamento)
        return agendamento
