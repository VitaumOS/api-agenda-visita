from datetime import date, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status

from app.core.config import (
    FIM_EXPEDIENTE,
    FUSO_BRASILIA,
    INICIO_EXPEDIENTE,
    INTERVALO_DESLOCAMENTO,
    INTERVALO_SUGESTOES,
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
        if (inicio.time() < INICIO_EXPEDIENTE or fim.date() != inicio.date() or fim.time() > FIM_EXPEDIENTE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O agendamento deve ocorrer entre 08:00 e 19:00 no horário de Brasília."
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
                sugestoes = self._sugerir_horarios(inicio, dados.duracao_minutos, dados.imovel_id, visitas_existentes)
                raise AgendamentoConflito(motivo, sugestoes)

        # Monta a resposta com um identificador único.
        agendamento = AgendamentoLeitura(
            agendamento_id=f"ag-{uuid4().hex[:8]}",
            corretor_id=dados.corretor_id,
            imovel_id=dados.imovel_id,
            inicio=inicio,
            fim=fim,
            status="confirmado"
        )
        #guarda no repositório
        self.repositorio.adicionar(agendamento)
        return agendamento

    # Lista as visitas do corretor na data informada.
    def listar(self, corretor_id: str, dia: date) -> list[AgendamentoLeitura]:
        return self.repositorio.listar_por_corretor_e_dia(corretor_id, dia)

    @staticmethod
    def _tem_conflito(inicio: datetime,fim: datetime,imovel_id: str,existente: AgendamentoLeitura) -> bool:
        # No mesmo imóvel, a visita só ocorre se não houver sobreposição.
        if imovel_id == existente.imovel_id:
            return inicio < existente.fim and existente.inicio < fim

        # Para imóveis diferentes, analisa o intervalo de deslocamento.
        deslocamento = timedelta(minutes=INTERVALO_DESLOCAMENTO)
        return not (fim + deslocamento <= existente.inicio or existente.fim + deslocamento <= inicio)

    def _sugerir_horarios(self, inicio_solicitado: datetime, duracao_minutos: int, imovel_id: str, visitas_existentes: list[AgendamentoLeitura] ) -> list[str]:
        # Calcula o primeiro e o último início possíveis dentro do expediente.
        primeiro_inicio = datetime.combine(inicio_solicitado.date(), INICIO_EXPEDIENTE, tzinfo=FUSO_BRASILIA)
        ultimo_inicio = datetime.combine( inicio_solicitado.date(), FIM_EXPEDIENTE, tzinfo=FUSO_BRASILIA) - timedelta(minutes=duracao_minutos)

        # Percorre os horários de meia em meia hora e conserva apenas os livres.
        passo = timedelta(minutes=INTERVALO_SUGESTOES)
        horarios_livres: list[datetime] = []
        candidato = primeiro_inicio
        while candidato <= ultimo_inicio:
            fim_candidato = candidato + timedelta(minutes=duracao_minutos)

            # Começa considerando o horário livre e procura algum conflito.
            esta_livre = True
            for visita in visitas_existentes:
                if self._tem_conflito(candidato, fim_candidato,imovel_id,visita):
                    esta_livre = False
                    break
            if esta_livre and candidato != inicio_solicitado:
                horarios_livres.append(candidato)
            candidato += passo

        # Coloca primeiro opções do mesmo turno e, depois, as mais próximas.
        mesmo_turno = self._turno(inicio_solicitado)
        horarios_livres.sort(
            key=lambda horario: (
                self._turno(horario) != mesmo_turno, #Mesmo turno
                abs((horario - inicio_solicitado).total_seconds()), #mais próximo do solicitado
                horario
            )
        )

        # Converte e devolve no máximo três alternativas.
        sugestoes: list[str] = []
        for horario in horarios_livres[:3]:
            sugestoes.append(horario.isoformat())

        return sugestoes

    @staticmethod
    def _turno(horario: datetime) -> str:
        # Considera manhã os horários anteriores ao meio-dia.
        return "manha" if horario.hour < 12 else "tarde"
