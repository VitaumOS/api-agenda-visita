from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status

from app.core.config import (
    FIM_EXPEDIENTE,
    FUSO_BRASILIA,
    INICIO_EXPEDIENTE,
    INTERVALO_DESLOCAMENTO,
)
from app.core.exceptions import AgendamentoConflito
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

        # Busca as visitas existentes do mesmo corretor naquele dia.
        visitas_existentes = self.repositorio.listar_por_corretor_e_dia(dados.corretor_id, inicio.date())

        # Verifica se a visita conflita com algum compromisso existente.
        for existente in visitas_existentes:
            if self._tem_conflito(inicio, fim, dados.imovel_id, existente):
                if inicio < existente.fim and existente.inicio < fim:
                    motivo = "Corretor já possui um agendamento nesse horário."
                else:
                    motivo = "Corretor indisponível devido ao tempo de deslocamento necessário."
                raise AgendamentoConflito(motivo)

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

    @staticmethod
    def _tem_conflito(inicio: datetime,fim: datetime,imovel_id: str,existente: AgendamentoLeitura) -> bool:
        # No mesmo imóvel, a visita só ocorre se não houver sobreposição.
        if imovel_id == existente.imovel_id:
            return inicio < existente.fim and existente.inicio < fim

        # Para imóveis diferentes, analisa o intervalo de deslocamento.
        deslocamento = timedelta(minutes=INTERVALO_DESLOCAMENTO)
        return not (fim + deslocamento <= existente.inicio or existente.fim + deslocamento <= inicio)
