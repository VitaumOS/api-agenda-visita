# API de Agenda de Visitas

API de agendamento de visitas a imóveis, desenvolvida em Python com FastAPI.

## Estrutura do projeto

```text
app/
├── api/
│   └── routes/
├── core/
├── main.py
├── models/
├── repositories/
├── schemas/
└── services/
tests/
```

- `app/api/routes/`: endpoints HTTP da API.
- `app/core/`: configurações e elementos compartilhados pela aplicação.
- `app/models/`: representação dos dados e entidades do domínio.
- `app/repositories/`: acesso e armazenamento dos dados.
- `app/schemas/`: formatos de entrada e saída da API.
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