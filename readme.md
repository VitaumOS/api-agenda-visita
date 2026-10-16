# API de Agenda de Visitas

API em Python com FastAPI para criar e consultar visitas a imóveis. O projeto segue as regras do desafio técnico e usa armazenamento em memória.

## Requisitos

- Python 3.11 ou superior
- `pip`

## Instalação e execução

No PowerShell, crie e ative um ambiente virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências e inicie o servidor:

```powershell
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

A API ficará disponível em `http://127.0.0.1:8000`. A documentação interativa do FastAPI fica em `/docs`; a versão alternativa fica em `/redoc`.

Se o ambiente virtual já existia antes de uma dependência ser adicionada a `requirements.txt`, execute novamente `python -m pip install -r requirements.txt`.

## Endpoints

### Verificar se a API está ativa

`GET /health`

Resposta `200`:

```json
{
  "status": "ok"
}
```

### Criar agendamento

`POST /api/agendamentos`

Exemplo de requisição:

```json
{
  "corretorId": "c-101",
  "imovelId": "im-553",
  "inicio": "2026-06-10T14:00:00-03:00",
  "duracaoMinutos": 60
}
```

Em caso de sucesso, retorna `201 Created`:

```json
{
  "agendamentoId": "ag-001",
  "corretorId": "c-101",
  "imovelId": "im-553",
  "inicio": "2026-06-10T14:00:00-03:00",
  "fim": "2026-06-10T15:00:00-03:00",
  "status": "confirmado"
}
```

Dados inválidos retornam `400 Bad Request`. Um conflito de horário ou deslocamento retorna `409 Conflict`, por exemplo:

```json
{
  "status": "conflito",
  "motivo": "Corretor indisponível devido ao tempo de deslocamento necessário.",
  "sugestoes": [
    "2026-06-10T15:30:00-03:00",
    "2026-06-10T16:30:00-03:00",
    "2026-06-10T17:30:00-03:00"
  ]
}
```

### Listar agendamentos de um corretor em uma data

`GET /api/agendamentos?corretorId=c-101&data=2026-06-10`

Retorna `200 OK` com uma lista ordenada pelo horário de início. Se não houver visitas correspondentes, retorna uma lista vazia (`[]`).

## Regras de negócio

- Os horários são avaliados no fuso `America/Sao_Paulo`, mesmo que a requisição use outro offset ISO 8601.
- As visitas devem começar a partir das 08:00 e terminar até as 19:00, no mesmo dia local.
- A duração deve estar entre 30 e 180 minutos e ser múltipla de 30.
- Visitas do mesmo corretor não podem se sobrepor.
- Visitas consecutivas ao mesmo imóvel podem encaixar sem intervalo.
- Entre imóveis diferentes, deve haver pelo menos 30 minutos para deslocamento. Exatamente 30 minutos é permitido.
- Em caso de conflito, a API procura até três horários alternativos no mesmo dia, em passos de 30 minutos, que respeitem as regras de disponibilidade e o expediente. As sugestões do mesmo turno do horário solicitado são priorizadas.
- Os agendamentos são guardados em memória e se perdem quando o processo da API é reiniciado.

## Arquitetura

```text
app/
├── api/routes/       # Endpoints HTTP
├── core/             # Fuso, limites e exceções da aplicação
├── repositories/     # Armazenamento e consulta em memória
├── schemas/          # Validação dos dados de entrada e saída
├── services/         # Regras de agendamento e sugestões
└── main.py           # Criação da aplicação FastAPI
tests/                # Testes automatizados
```

O endpoint recebe a requisição e valida o formato por meio dos schemas. O serviço aplica as regras de negócio e consulta o repositório. O repositório mantém os dados em memória; não é necessário configurar um banco de dados para este desafio.

## Datas e fusos horários

O campo `inicio` deve conter data, hora e offset, como `2026-06-10T14:00:00-03:00`. Horários sem fuso são rejeitados porque não identificam um instante sem ambiguidade. Antes de aplicar a janela de atendimento ou comparar com a agenda, o serviço converte o valor para `America/Sao_Paulo`. O horário de término é calculado a partir do início já convertido.

No Windows, `zoneinfo` pode precisar dos dados IANA fornecidos pela dependência `tzdata`. Por isso ela está declarada em `requirements.txt`.

## Testes

Com as dependências instaladas e o ambiente virtual ativado, execute todos os testes:

```powershell
python -m pytest
```

Os testes cobrem os schemas, as respostas HTTP, a janela de atendimento, conflitos e deslocamento, sugestões, listagem por corretor/data e o endpoint de health.
