# Representa um conflito que impede criar o agendamento solicitado.
class AgendamentoConflito(Exception):
    def __init__(self, motivo: str, sugestoes: list[str] | None = None) -> None:
        # Guarda a explicação e as alternativas que serão enviadas ao cliente.
        self.motivo = motivo
        self.sugestoes = sugestoes or []
        super().__init__(motivo)
