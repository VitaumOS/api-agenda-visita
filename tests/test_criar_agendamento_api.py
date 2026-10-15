from fastapi.testclient import TestClient

from app.main import app


# O cliente faz requisições de teste sem iniciar um servidor externo.
client = TestClient(app)


# Confirma que o endpoint cria uma visita usando o contrato camelCase do PDF.
def test_cria_agendamento() -> None:
    resposta = client.post(
        "/api/agendamentos",
        json={
            "corretorId": "c-101",
            "imovelId": "im-553",
            "inicio": "2026-06-10T14:00:00-03:00",
            "duracaoMinutos": 60,
        },
    )

    # Confere o status de criação e os campos camelCase da resposta JSON.
    assert resposta.status_code == 201
    assert resposta.json()["corretorId"] == "c-101"
    assert resposta.json()["imovelId"] == "im-553"
    assert resposta.json()["inicio"] == "2026-06-10T14:00:00-03:00"
    assert resposta.json()["fim"] == "2026-06-10T15:00:00-03:00"
    assert resposta.json()["status"] == "confirmado"


# Confirma que o endpoint rejeita uma duração que não é múltipla de 30.
def test_rejeita_duracao_invalida() -> None:
    resposta = client.post(
        "/api/agendamentos",
        json={
            "corretorId": "c-101",
            "imovelId": "im-553",
            "inicio": "2026-06-10T14:00:00-03:00",
            "duracaoMinutos": 45,
        },
    )

    assert resposta.status_code == 422


# Confirma que visitas que terminam depois das 19h são rejeitadas.
def test_rejeita_agendamento_que_termina_depois_das_dezenove() -> None:
    reposta = client.post(
            "api/agendamentos",
        json={
            "corretorId": "c-102",
            "imovelId": "im-553",
            "inicio": "2026-06-10T18:30:00-03:00",
            "duracaoMinutos": 60,
        }
    )
    assert reposta.status_code == 400

# Confirma que o horário de entrada é convertido para Brasília antes da validação.
def test_converte_fuso_e_aceita_inicio_as_oito_em_brasilia() -> None:
    resposta = client.post(
        "/api/agendamentos",
        json={
            "corretorId": "c-103",
            "imovelId": "im-553",
            "inicio": "2026-06-10T11:00:00+00:00",
            "duracaoMinutos": 60,
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["inicio"] == "2026-06-10T08:00:00-03:00"
    assert resposta.json()["fim"] == "2026-06-10T09:00:00-03:00"


# Confirma que visitas que começam antes das 8h são rejeitadas.
def test_rejeita_inicio_antes_das_oito_em_brasilia() -> None:
    resposta = client.post(
        "/api/agendamentos",
        json={
            "corretorId": "c-104",
            "imovelId": "im-553",
            "inicio": "2026-06-10T10:30:00+00:00",
            "duracaoMinutos": 60,
        },
    )

    assert resposta.status_code == 400
