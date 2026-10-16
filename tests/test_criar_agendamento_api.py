from fastapi.testclient import TestClient

from app.main import app


# O cliente faz requisições de teste sem iniciar um servidor externo.
client = TestClient(app)


# Confirma que o endpoint cria uma visita usando o contrato camelCase do PDF.
def test_cria_agendamento() -> None:
    resposta = client.post( "/api/agendamentos",
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
    resposta = client.post( "/api/agendamentos",
        json={
            "corretorId": "c-101",
            "imovelId": "im-553",
            "inicio": "2026-06-10T14:00:00-03:00",
            "duracaoMinutos": 45,
        },
    )

    assert resposta.status_code == 400


# Cria visitas de teste em horários diferentes para o mesmo corretor.
def enviar_agendamento(corretor_id: str,imovel_id: str,inicio: str,duracao: int = 60):
    return client.post( "/api/agendamentos",
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
    assert len(segunda.json()["sugestoes"]) == 3


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


# Sugestões para um conflito à tarde devem priorizar outros horários da tarde.
def test_sugestoes_priorizam_o_mesmo_turno_e_respeitam_deslocamento() -> None:
    primeira = enviar_agendamento(
        "c-sugestoes-tarde", "im-1", "2026-06-12T14:00:00-03:00"
    )
    conflito = enviar_agendamento(
        "c-sugestoes-tarde", "im-2", "2026-06-12T15:00:00-03:00"
    )

    sugestoes = conflito.json()["sugestoes"]

    assert primeira.status_code == 201
    assert conflito.status_code == 409
    assert len(sugestoes) == 3
    assert all(sugestao.startswith("2026-06-12T") for sugestao in sugestoes)
    assert all(int(sugestao[11:13]) >= 12 for sugestao in sugestoes)
    assert sugestoes[0] == "2026-06-12T15:30:00-03:00"


# Conflitos pela manhã também recebem opções, priorizando o turno da manhã.
def test_sugestoes_de_conflito_pela_manha_priorizam_o_mesmo_turno() -> None:
    primeira = enviar_agendamento(
        "c-sugestoes-manha", "im-1", "2026-06-12T10:00:00-03:00"
    )
    conflito = enviar_agendamento(
        "c-sugestoes-manha", "im-2", "2026-06-12T10:30:00-03:00"
    )

    sugestoes = conflito.json()["sugestoes"]

    assert primeira.status_code == 201
    assert conflito.status_code == 409
    assert len(sugestoes) == 3
    assert all(sugestao.startswith("2026-06-12T") for sugestao in sugestoes)
    assert all(int(sugestao[11:13]) < 12 for sugestao in sugestoes[:2])


# Confirma que visitas que terminam depois das 19h são rejeitadas.
def test_rejeita_agendamento_que_termina_depois_das_dezenove() -> None:
    reposta = client.post("api/agendamentos",
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
    resposta = client.post("/api/agendamentos",
        json={
            "corretorId": "c-104",
            "imovelId": "im-553",
            "inicio": "2026-06-10T10:30:00+00:00",
            "duracaoMinutos": 60,
        },
    )

    assert resposta.status_code == 400


# A consulta deve ordenar os resultados mesmo que tenham sido criados fora de ordem.
def test_lista_agendamentos_em_ordem_cronologica() -> None:
    enviar_agendamento(
        "c-listagem-ordem", "im-listagem", "2026-06-15T16:00:00-03:00"
    )
    enviar_agendamento(
        "c-listagem-ordem", "im-listagem", "2026-06-15T14:00:00-03:00"
    )

    resposta = client.get("/api/agendamentos",
        params={"corretorId": "c-listagem-ordem", "data": "2026-06-15"},
    )

    assert resposta.status_code == 200
    assert [item["inicio"] for item in resposta.json()] == [
        "2026-06-15T14:00:00-03:00",
        "2026-06-15T16:00:00-03:00",
    ]


# A consulta deve excluir visitas de outros corretores e de outras datas.
def test_lista_agendamentos_filtrando_corretor_e_data() -> None:
    enviar_agendamento(
        "c-listagem-filtro", "im-listagem", "2026-06-16T14:00:00-03:00"
    )
    enviar_agendamento(
        "c-listagem-outro", "im-listagem", "2026-06-16T15:00:00-03:00"
    )
    enviar_agendamento(
        "c-listagem-filtro", "im-listagem", "2026-06-17T14:00:00-03:00"
    )

    resposta = client.get(
        "/api/agendamentos",
        params={"corretorId": "c-listagem-filtro", "data": "2026-06-16"},
    )

    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    assert resposta.json()[0]["corretorId"] == "c-listagem-filtro"
    assert resposta.json()[0]["inicio"] == "2026-06-16T14:00:00-03:00"


# A data da consulta deve seguir o formato ISO YYYY-MM-DD.
def test_lista_agendamentos_rejeita_data_invalida() -> None:
    resposta = client.get(
        "/api/agendamentos",
        params={"corretorId": "c-listagem-data", "data": "16-06-2026"},
    )

    assert resposta.status_code == 400
