from datetime import datetime

from app.schemas.agendamento import AgendamentoLeitura


# Confirma que o modelo de resposta pode ser construído com nomes Python.
def test_cria_resposta_de_agendamento() -> None:
    agendamento = AgendamentoLeitura(
        agendamento_id="ag-001",
        corretor_id="c-101",
        imovel_id="im-553",
        inicio=datetime.fromisoformat("2026-06-10T14:00:00-03:00"),
        fim=datetime.fromisoformat("2026-06-10T15:00:00-03:00"),
        status="confirmado",
    )

    # Confirma que os dados principais foram guardados no modelo.
    assert agendamento.agendamento_id == "ag-001"
    assert agendamento.status == "confirmado"


# Confirma que o JSON utiliza os nomes de campos exigidos pelo enunciado.
def test_serializa_resposta_com_aliases_json() -> None:
    agendamento = AgendamentoLeitura(
        agendamento_id="ag-001",
        corretor_id="c-101",
        imovel_id="im-553",
        inicio=datetime.fromisoformat("2026-06-10T14:00:00-03:00"),
        fim=datetime.fromisoformat("2026-06-10T15:00:00-03:00"),
        status="confirmado",
    )

    resposta = agendamento.model_dump(mode="json", by_alias=True)

    assert resposta["agendamentoId"] == "ag-001"
    assert resposta["corretorId"] == "c-101"
    assert resposta["imovelId"] == "im-553"
    assert resposta["status"] == "confirmado"
