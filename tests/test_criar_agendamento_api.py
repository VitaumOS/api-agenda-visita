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

    assert resposta.status_code == 400


# Cria visitas de teste em horários diferentes para o mesmo corretor.
def enviar_agendamento(
    corretor_id: str,
    imovel_id: str,
    inicio: str,
    duracao: int = 60,
):
    return client.post(
        "/api/agendamentos",
        json={
            "corretorId": corretor_id,
            "imovelId": imovel_id,
            "inicio": inicio,
            "duracaoMinutos": duracao,
        },
    )


# Visitas consecutivas ao mesmo imóvel não precisam de intervalo.
def test_mesmo_imovel_permite_visitas_consecutivas() -> None:
    primeira = enviar_agendamento(
        "c-mesmo-imovel", "im-1", "2026-06-11T14:00:00-03:00"
    )
    segunda = enviar_agendamento(
        "c-mesmo-imovel", "im-1", "2026-06-11T15:00:00-03:00"
    )

    assert primeira.status_code == 201
    assert segunda.status_code == 201


# Imóveis diferentes exigem 30 minutos entre o fim e o início das visitas.
def test_imovel_diferente_sem_intervalo_retorna_conflito_409() -> None:
    primeira = enviar_agendamento(
        "c-sem-intervalo", "im-1", "2026-06-11T14:00:00-03:00"
    )
    segunda = enviar_agendamento(
        "c-sem-intervalo", "im-2", "2026-06-11T15:00:00-03:00"
    )

    assert primeira.status_code == 201
    assert segunda.status_code == 409
    assert segunda.json()["status"] == "conflito"
    assert "deslocamento" in segunda.json()["motivo"]
    assert segunda.json()["sugestoes"] == []


# O buffer de 30 minutos pode ser exato, sem exigir minutos adicionais.
def test_imovel_diferente_com_trinta_minutos_e_aceito() -> None:
    primeira = enviar_agendamento(
        "c-intervalo-exato", "im-1", "2026-06-11T14:00:00-03:00"
    )
    segunda = enviar_agendamento(
        "c-intervalo-exato", "im-2", "2026-06-11T15:30:00-03:00"
    )

    assert primeira.status_code == 201
    assert segunda.status_code == 201


# Mesmo uma pausa menor que 30 minutos é insuficiente entre imóveis diferentes.
def test_imovel_diferente_com_intervalo_menor_que_trinta_retorna_conflito() -> None:
    primeira = enviar_agendamento(
        "c-intervalo-curto", "im-1", "2026-06-11T14:00:00-03:00"
    )
    segunda = enviar_agendamento(
        "c-intervalo-curto", "im-2", "2026-06-11T15:15:00-03:00"
    )

    assert primeira.status_code == 201
    assert segunda.status_code == 409


# Sobreposição parcial também é conflito, mesmo quando o imóvel é o mesmo.
def test_sobreposicao_parcial_retorna_conflito() -> None:
    primeira = enviar_agendamento(
        "c-sobreposicao", "im-1", "2026-06-11T14:00:00-03:00"
    )
    segunda = enviar_agendamento(
        "c-sobreposicao", "im-1", "2026-06-11T14:30:00-03:00",
        duracao=30,
    )

    assert primeira.status_code == 201
    assert segunda.status_code == 409
    assert "horário" in segunda.json()["motivo"]


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
