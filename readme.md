# API de Agenda de Visitas

API de agendamento de visitas a imóveis, desenvolvida em Python com FastAPI.

## Estrutura do projeto

```text
app/
├── api/
│   └── routes/
│       ├── agendamentos.py
│       └── health.py
├── core/
│   ├── config.py
│   └── exceptions.py
├── main.py
├── models/
├── repositories/
│   └── agendamento_repository.py
├── schemas/
│   └── agendamento.py
└── services/
    └── agendamento_service.py
tests/
```

- `app/api/routes/`: endpoints HTTP da API; inclui `GET /health` e operações de criação e listagem de agendamentos.
- `app/core/`: configurações compartilhadas e a exceção usada para responder conflitos.
- `app/models/`: representação dos dados e entidades do domínio.
- `app/repositories/`: acesso e armazenamento dos dados; os agendamentos ficam em memória por enquanto.
- `app/schemas/`: formatos de entrada e saída da API; `agendamento.py` contém os modelos do pedido e da resposta de agendamento.
- `app/services/`: regras de negócio e lógica do agendamento.
- `tests/`: testes automatizados.

## Instalar dependências e executar

Com Python instalado, crie e ative um ambiente virtual no PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as bibliotecas listadas em `requirements.txt` e inicie o servidor:

```powershell
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

O servidor ficará disponível em `http://127.0.0.1:8000`.

Para conferir se a API está respondendo, acesse `http://127.0.0.1:8000/health`. A rota retorna `{"status": "ok"}`.

O endpoint `POST /api/agendamentos` recebe os campos em camelCase definidos pelo enunciado e cria uma visita em memória. A janela de atendimento é validada no fuso `America/Sao_Paulo`; sobreposições são rejeitadas e visitas a imóveis diferentes exigem 30 minutos de deslocamento. Em caso de conflito, a API sugere até três horários livres em intervalos de 30 minutos, priorizando o turno solicitado.

O endpoint `GET /api/agendamentos?corretorId=c-101&data=2026-06-10` lista as visitas daquele corretor na data informada, em ordem cronológica.