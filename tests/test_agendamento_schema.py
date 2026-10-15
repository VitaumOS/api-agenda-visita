import pytest
from pydantic import ValidationError
from app.schemas.agendamento import AgendamentoCria

# Monta um pedido válido para reutilizar nos testes.
def criar_dados_validos() -> dict[str, object]:
    return {
        "corretorId": "c-101",
        "imovelId": "im-553",
        "inicio": "2026-06-10T14:00:00-03:00",
        "duracaoMinutos": 60,
    }


# Confirma que os campos do JSON são convertidos para os tipos Python esperados.
def test_converte_pedido_valido() -> None:
    agendamento = AgendamentoCria.model_validate(criar_dados_validos())

    assert agendamento.corretor_id == "c-101"
    assert agendamento.imovel_id == "im-553"
    assert agendamento.duracao_minutos == 60
    assert agendamento.inicio.utcoffset() is not None


# Confirma que durações que não são múltiplos de 30 são rejeitadas.
def test_rejeita_duracao_que_nao_seja_multiplo_de_trinta() -> None:
    dados = criar_dados_validos()
    dados["duracaoMinutos"] = 45

    with pytest.raises(ValidationError):
        AgendamentoCria.model_validate(dados)


# Confirma que uma duração menor que o limite mínimo é rejeitada.
def test_rejeita_duracao_menor_que_trinta_minutos() -> None:
    dados = criar_dados_validos()
    dados["duracaoMinutos"] = 0

    with pytest.raises(ValidationError):
        AgendamentoCria.model_validate(dados)


# Confirma que um horário sem fuso não é aceito.
def test_rejeita_horario_sem_fuso() -> None:
    dados = criar_dados_validos()
    dados["inicio"] = "2026-06-10T14:00:00"

    with pytest.raises(ValidationError):
        AgendamentoCria.model_validate(dados)
