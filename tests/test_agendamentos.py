from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.agendamento_repository import AgendamentoRepositorio
from app.services.agendamento_service import AgendamentoService


client = TestClient(app)

# Evita que agendamentos de um teste afetem os testes seguintes.
@pytest.fixture(autouse=True)
def limpar_agenda() -> None:
    app.state.agendamento_service = AgendamentoService(AgendamentoRepositorio())


def criar_payload(corretor_id: str = "c-101",imovel_id: str = "im-553",inicio: str = "2026-06-10T14:00:00-03:00",duracao: int = 60) -> dict[str, object]:
    return {
        "corretorId": corretor_id,
        "imovelId": imovel_id,
        "inicio": inicio,
        "duracaoMinutos": duracao
    }


def criar_agendamento(corretor_id: str,imovel_id: str,inicio: str,duracao: int = 60):
    return client.post("/api/agendamentos",json=criar_payload(corretor_id, imovel_id, inicio, duracao))


# Verifica que a criação retorna HTTP 201 e todos os campos do contrato esperado.
def test_cria_agendamento_e_retorna_contrato_esperado() -> None:
    resposta = client.post("/api/agendamentos", json=criar_payload())
    corpo = resposta.json()

    assert resposta.status_code == 201
    assert set(corpo) == {
        "agendamentoId",
        "corretorId",
        "imovelId",
        "inicio",
        "fim",
        "status"
    }
    assert corpo["agendamentoId"].startswith("ag-")
    assert corpo["corretorId"] == "c-101"
    assert corpo["imovelId"] == "im-553"
    assert corpo["inicio"] == "2026-06-10T14:00:00-03:00"
    assert corpo["fim"] == "2026-06-10T15:00:00-03:00"
    assert corpo["status"] == "confirmado"


# Verifica que a API rejeita um ID de corretor enviado como nulo.
def test_rejeita_corretor_nulo() -> None:
    payload = criar_payload()
    payload["corretorId"] = None

    resposta = client.post("/api/agendamentos", json=payload)

    assert resposta.status_code == 400


# Verifica que a API rejeita um ID de imóvel enviado como nulo.
def test_rejeita_imovel_nulo() -> None:
    payload = criar_payload()
    payload["imovelId"] = None

    resposta = client.post("/api/agendamentos", json=payload)

    assert resposta.status_code == 400


# Verifica que a API rejeita visitas com duração inferior a 30 minutos.
def test_rejeita_duracao_menor_que_trinta() -> None:
    payload = criar_payload()
    payload["duracaoMinutos"] = 29

    resposta = client.post("/api/agendamentos", json=payload)

    assert resposta.status_code == 400


# Verifica que a API rejeita durações que não são múltiplos de 30 minutos.
def test_rejeita_duracao_que_nao_e_multiplo_de_trinta() -> None:
    payload = criar_payload()
    payload["duracaoMinutos"] = 45

    resposta = client.post("/api/agendamentos", json=payload)

    assert resposta.status_code == 400


# Verifica que a API rejeita visitas com duração superior a 180 minutos.
def test_rejeita_duracao_maior_que_cento_e_oitenta() -> None:
    payload = criar_payload()
    payload["duracaoMinutos"] = 210

    resposta = client.post("/api/agendamentos", json=payload)

    assert resposta.status_code == 400


# Verifica que a API rejeita pedidos sem o campo do corretor.
def test_rejeita_corretor_ausente() -> None:
    payload = criar_payload()
    payload.pop("corretorId")

    resposta = client.post("/api/agendamentos", json=payload)

    assert resposta.status_code == 400


# Verifica que a API rejeita pedidos sem o campo do imóvel.
def test_rejeita_imovel_ausente() -> None:
    payload = criar_payload()
    payload.pop("imovelId")

    resposta = client.post("/api/agendamentos", json=payload)

    assert resposta.status_code == 400


# Verifica que a API rejeita horários de início sem informação de fuso.
def test_rejeita_inicio_sem_fuso_horario() -> None:
    resposta = client.post("/api/agendamentos",json=criar_payload(inicio="2026-06-10T14:00:00"))

    assert resposta.status_code == 400


# Verifica que a API rejeita valores de início que não são datas válidas.
def test_rejeita_inicio_em_formato_invalido() -> None:
    resposta = client.post("/api/agendamentos",json=criar_payload(inicio="data-invalida"))

    assert resposta.status_code == 400


# Verifica que o início deve ser enviado como texto no formato ISO 8601.
def test_rejeita_inicio_numerico() -> None:
    payload = criar_payload()
    payload["inicio"] = 1781092800

    resposta = client.post("/api/agendamentos", json=payload)

    assert resposta.status_code == 400


# Verifica que uma string que não segue o formato ISO 8601 é rejeitada.
def test_rejeita_inicio_em_string_que_nao_e_iso8601() -> None:
    payload = criar_payload()
    payload["inicio"] = "1781092800"

    resposta = client.post("/api/agendamentos", json=payload)

    assert resposta.status_code == 400


# Verifica que um agendamento pode começar exatamente às 08:00.
def test_aceita_inicio_exatamente_as_oito() -> None:
    resposta = client.post("/api/agendamentos", json=criar_payload(inicio="2026-06-10T08:00:00-03:00", duracao=30))

    assert resposta.status_code == 201


# Verifica que um agendamento pode terminar exatamente às 19:00.
def test_aceita_fim_exatamente_as_dezenove() -> None:
    resposta = client.post("/api/agendamentos", json=criar_payload(inicio="2026-06-10T18:30:00-03:00", duracao=30))

    assert resposta.status_code == 201
    assert resposta.json()["fim"] == "2026-06-10T19:00:00-03:00"


# Verifica que a API rejeita agendamentos iniciados antes das 08:00.
def test_rejeita_inicio_antes_das_oito() -> None:
    resposta = client.post("/api/agendamentos",json=criar_payload(inicio="2026-06-10T07:59:00-03:00", duracao=30))

    assert resposta.status_code == 400


# Verifica que a API rejeita agendamentos que terminam depois das 19:00.
def test_rejeita_fim_um_minuto_depois_das_dezenove() -> None:
    resposta = client.post("/api/agendamentos",json=criar_payload(inicio="2026-06-10T18:31:00-03:00", duracao=30))

    assert resposta.status_code == 400


# Verifica que visitas consecutivas no mesmo imóvel não precisam de deslocamento.
def test_permite_visitas_consecutivas_no_mesmo_imovel() -> None:
    primeira = criar_agendamento("c-101", "im-553", "2026-06-10T14:00:00-03:00")
    segunda = criar_agendamento("c-101", "im-553", "2026-06-10T15:00:00-03:00")

    assert primeira.status_code == 201
    assert segunda.status_code == 201


# Verifica que horários sobrepostos são rejeitados com resposta HTTP 409.
def test_rejeita_sobreposicao_e_retorna_conflito() -> None:
    criar_agendamento( "c-101", "im-553", "2026-06-10T14:00:00-03:00")
    resposta = criar_agendamento( "c-101", "im-553", "2026-06-10T14:30:00-03:00")
    corpo = resposta.json()

    assert resposta.status_code == 409
    assert corpo["status"] == "conflito"
    assert "motivo" in corpo
    assert len(corpo["sugestoes"]) <= 3


# Verifica que exatamente 30 minutos entre imóveis diferentes são aceitos.
def test_aceita_trinta_minutos_entre_imoveis_diferentes() -> None:
    criar_agendamento( "c-101", "im-553", "2026-06-10T14:00:00-03:00")
    resposta = criar_agendamento( "c-101", "im-999", "2026-06-10T15:30:00-03:00")

    assert resposta.status_code == 201


# Verifica que menos de 30 minutos entre imóveis diferentes causam conflito.
def test_rejeita_intervalo_menor_que_trinta_minutos_entre_imoveis() -> None:
    criar_agendamento( "c-101", "im-553", "2026-06-10T14:00:00-03:00")
    resposta = criar_agendamento("c-101", "im-999", "2026-06-10T15:29:00-03:00")

    assert resposta.status_code == 409


# Verifica que o intervalo mínimo também é respeitado antes de uma visita existente.
def test_aceita_trinta_minutos_antes_de_visita_em_outro_imovel() -> None:
    criar_agendamento("c-101", "im-553", "2026-06-10T15:00:00-03:00")
    resposta = criar_agendamento("c-101", "im-999", "2026-06-10T13:30:00-03:00")

    assert resposta.status_code == 201


# Verifica que menos de 30 minutos antes de uma visita em outro imóvel causa conflito.
def test_rejeita_menos_de_trinta_minutos_antes_de_visita_em_outro_imovel() -> None:
    criar_agendamento("c-101", "im-553", "2026-06-10T15:00:00-03:00")
    resposta = criar_agendamento("c-101", "im-999", "2026-06-10T14:01:00-03:00", 30)

    assert resposta.status_code == 409


# Verifica que o conflito retorna três sugestões livres priorizando o mesmo turno.
def test_sugere_tres_horarios_livres_priorizando_o_mesmo_turno() -> None:
    criar_agendamento( "c-101", "im-553", "2026-06-10T14:00:00-03:00")
    resposta = criar_agendamento("c-101", "im-999", "2026-06-10T15:00:00-03:00")
    sugestoes = resposta.json()["sugestoes"]

    assert resposta.status_code == 409
    assert len(sugestoes) == 3
    assert sugestoes[0] == "2026-06-10T15:30:00-03:00"
    for sugestao in sugestoes:
        assert int(sugestao[11:13]) >= 12
    solicitado = datetime.fromisoformat("2026-06-10T15:00:00-03:00")
    for sugestao in sugestoes:
        inicio = datetime.fromisoformat(sugestao)
        fim = inicio + timedelta(minutes=60)
        assert inicio.date() == solicitado.date()
        assert inicio != solicitado
        assert inicio >= datetime.fromisoformat("2026-06-10T15:30:00-03:00")
        assert inicio.hour >= 8
        assert fim <= datetime.fromisoformat("2026-06-10T19:00:00-03:00")
    assert len(set(sugestoes)) == len(sugestoes)


# Verifica que a API retorna somente as duas alternativas livres, mesmo podendo retornar até três.
def test_sugere_menos_de_tres_horarios_quando_so_dois_estao_livres() -> None:
    horarios_livres = {"2026-06-10T08:30:00-03:00", "2026-06-10T09:00:00-03:00"}
    for minuto in range(8 * 60, 19 * 60, 30):
        horario = f"2026-06-10T{minuto // 60:02}:{minuto % 60:02}:00-03:00"
        if horario not in horarios_livres:
            assert criar_agendamento("c-101", "im-553", horario, 30).status_code == 201

    resposta = criar_agendamento("c-101", "im-553", "2026-06-10T08:00:00-03:00", 30)

    assert resposta.status_code == 409
    assert resposta.json()["sugestoes"] == [
        "2026-06-10T08:30:00-03:00",
        "2026-06-10T09:00:00-03:00"
    ]


# Verifica que a lista de sugestões fica vazia quando não há horário disponível.
def test_retorna_lista_vazia_de_sugestoes_quando_todos_horarios_estao_ocupados() -> None:
    for minuto in range(8 * 60, 19 * 60, 30):
        horario = f"2026-06-10T{minuto // 60:02}:{minuto % 60:02}:00-03:00"
        assert criar_agendamento("c-101", "im-553", horario, 30).status_code == 201

    resposta = criar_agendamento("c-101", "im-553", "2026-06-10T08:00:00-03:00", 30)

    assert resposta.status_code == 409
    assert resposta.json()["sugestoes"] == []


# Verifica que, sem alternativas no turno solicitado, a API oferece alternativas do outro turno.
def test_sugere_outro_turno_quando_nao_ha_horarios_livres_no_mesmo_turno() -> None:
    for minuto in range(12 * 60, 19 * 60, 30):
        horario = f"2026-06-10T{minuto // 60:02}:{minuto % 60:02}:00-03:00"
        assert criar_agendamento("c-101", "im-553", horario, 30).status_code == 201

    resposta = criar_agendamento("c-101", "im-553", "2026-06-10T14:00:00-03:00", 30)

    assert resposta.status_code == 409
    sugestoes = resposta.json()["sugestoes"]
    assert sugestoes == [
        "2026-06-10T11:30:00-03:00",
        "2026-06-10T11:00:00-03:00",
        "2026-06-10T10:30:00-03:00"
    ]
    for sugestao in sugestoes:
        assert int(sugestao[11:13]) < 12


# Verifica que um horário enviado em UTC é convertido para o horário de Brasília na resposta.
def test_converte_inicio_de_outro_fuso_para_brasilia() -> None:
    resposta = client.post("/api/agendamentos",json=criar_payload(inicio="2026-06-10T11:00:00+00:00"))

    assert resposta.status_code == 201
    assert resposta.json()["inicio"] == "2026-06-10T08:00:00-03:00"
    assert resposta.json()["fim"] == "2026-06-10T09:00:00-03:00"


# Verifica que a consulta usa a data local de Brasília quando a conversão muda o dia.
def test_lista_agendamento_na_data_local_apos_conversao_de_fuso() -> None:
    resposta = client.post("/api/agendamentos",json=criar_payload(inicio="2026-06-11T00:00:00+03:00", duracao=30))
    assert resposta.status_code == 201
    assert resposta.json()["inicio"] == "2026-06-10T18:00:00-03:00"

    data_local = client.get("/api/agendamentos",params={"corretorId": "c-101", "data": "2026-06-10"})
    data_enviada = client.get("/api/agendamentos",params={"corretorId": "c-101", "data": "2026-06-11"})

    inicios_data_local = []
    for item in data_local.json():
        inicios_data_local.append(item["inicio"])
    assert inicios_data_local == ["2026-06-10T18:00:00-03:00"]
    assert data_enviada.json() == []


# Verifica que a listagem filtra corretor e data e ordena os resultados por início.
def test_lista_agendamentos_do_corretor_e_data_em_ordem_cronologica() -> None:
    criar_agendamento( "c-101", "im-553", "2026-06-10T16:00:00-03:00")
    criar_agendamento( "c-101", "im-553", "2026-06-10T14:00:00-03:00")
    criar_agendamento( "c-202", "im-553", "2026-06-10T14:00:00-03:00")
    criar_agendamento( "c-101", "im-553", "2026-06-11T14:00:00-03:00")

    resposta = client.get("/api/agendamentos",params={"corretorId": "c-101", "data": "2026-06-10"})

    assert resposta.status_code == 200
    inicios = []
    for item in resposta.json():
        inicios.append(item["inicio"])
    assert inicios == [
        "2026-06-10T14:00:00-03:00",
        "2026-06-10T16:00:00-03:00"
    ]
