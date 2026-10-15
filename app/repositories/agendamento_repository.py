from datetime import date

from app.schemas.agendamento import AgendamentoLeitura

# Guarda os agendamentos em uma lista enquanto a aplicação estiver ligada.
class AgendamentoRepositorio:
    def __init__(self) -> None:
        self._agendamentos: list[AgendamentoLeitura] = []

    # Adiciona um agendamento à lista em memória.
    def adicionar(self, agendamento: AgendamentoLeitura) -> None:
        self._agendamentos.append(agendamento)

    # Retorna os agendamentos de um corretor em um dia específico.
    def listar_por_corretor_e_dia(self, corretor_id: str, dia: date) -> list[AgendamentoLeitura]:
        agendamentos: list[AgendamentoLeitura] = []
        for agendamento in self._agendamentos:
            if agendamento.corretor_id == corretor_id and agendamento.inicio.date() == dia:
                agendamentos.append(agendamento)

        # Ordena pelo horário
        return sorted(agendamentos, key=lambda agendamento: agendamento.inicio)
