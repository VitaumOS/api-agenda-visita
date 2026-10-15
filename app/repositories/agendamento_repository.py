from app.schemas.agendamento import AgendamentoLeitura

# Guarda os agendamentos em uma lista enquanto a aplicação estiver ligada.
class AgendamentoRepositorio:
    def __init__(self) -> None:
        self._agendamentos: list[AgendamentoLeitura] = []

    # Adiciona um agendamento à lista em memória.
    def adicionar(self, agendamento: AgendamentoLeitura) -> None:
        self._agendamentos.append(agendamento)
