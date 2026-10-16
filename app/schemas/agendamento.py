from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Representa os dados que o cliente precisa enviar para criar uma visita.
class AgendamentoCria(BaseModel):
    # Aceita nomes Python internamente e os nomes camelCase enviados pelo cliente.
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    corretor_id: str = Field(alias="corretorId", min_length=1)
    imovel_id: str = Field(alias="imovelId", min_length=1)
    inicio: datetime
    duracao_minutos: int = Field(alias="duracaoMinutos", ge=30, le=180, multiple_of=30)

    # Confere se o horário informado contém informação de fuso horário.
    @field_validator("inicio")
    @classmethod
    def validar_fuso_horario(cls, valor: datetime) -> datetime:
        if valor.tzinfo is None or valor.utcoffset() is None:
            raise ValueError("inicio deve incluir o fuso horário")
        return valor


# Representa os dados que a API devolve após confirmar uma visita.
class AgendamentoLeitura(BaseModel):
    # Faz a resposta JSON usar camelCase sem mudar os nomes usados no Python.
    model_config = ConfigDict(populate_by_name=True)
    agendamento_id: str = Field(alias="agendamentoId")
    corretor_id: str = Field(alias="corretorId")
    imovel_id: str = Field(alias="imovelId")
    inicio: datetime
    fim: datetime

    status: Literal["confirmado"]
