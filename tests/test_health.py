from fastapi.testclient import TestClient

from app.main import app

# O cliente de teste chama a aplicação sem iniciar um servidor externo.
client = TestClient(app)

def test_verificar_saude() -> None:
    # Envia uma requisição HTTP GET para o endpoint de saúde.
    resposta = client.get("/health")
    # Confirma o código HTTP e o JSON esperado.
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}
