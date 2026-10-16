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

## Testes

Com as dependências instaladas e o ambiente virtual ativado, execute todos os testes:

```powershell
python -m pytest
```

Os testes cobrem criação, validação dos dados, janela de atendimento, conflitos e deslocamento, sugestões e listagem por corretor/data.

## Endpoints

### Verificar se a API está ativa

`GET /health`

Resposta `200`:

```json
{"status": "ok"}
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
├── routes/                 # Endpoints HTTP
├── core/                   # Configurações e exceções compartilhadas
├── repositories/           # Armazenamento e consulta em memória
├── schemas/                # Validação dos dados de entrada e saída
├── services/               # Regras de agendamento e sugestões
└── main.py                 # Criação da aplicação FastAPI
tests/                      # Testes automatizados
```

O `main.py` cria a aplicação FastAPI, instancia o serviço com o repositório em memória e registra os roteadores. Os arquivos em `routes/` traduzem as requisições HTTP em chamadas ao serviço e definem os status e formatos das respostas. Os modelos de `schemas/` validam os campos recebidos e descrevem os dados devolvidos pela API.

O `AgendamentoService` concentra as regras do domínio: converte datas para Brasília, calcula o fim da visita, valida a janela de atendimento, verifica conflitos e calcula sugestões. Quando a operação é válida, ele pede ao `AgendamentoRepositorio` que guarde os dados. É importante ressaltar que a persistência foi implementada através de uma estrutura volátil em memória. O repositório mantém uma lista em memória e filtra/ordena os resultados da consulta. Essa escolha mantém a implementação simples, como permitido pelo tópico, mas significa que os agendamentos são perdidos quando a aplicação é reiniciada.

As exceções de conflito são convertidas em HTTP `409` pela aplicação. Erros de validação das requisições são convertidos em HTTP `400`, de acordo com o contrato solicitado no enunciado.

## Algoritmo de conflito e sugestões

Para criar uma visita, o serviço primeiro consulta os agendamentos do mesmo corretor na data local solicitada. Cada visita existente é comparada com o novo intervalo:

1. Se os intervalos se sobrepõem, há conflito, inclusive quando a visita existente é no mesmo imóvel.
2. Se não há sobreposição e os imóveis são iguais, não é necessário intervalo de deslocamento, já que uma visita pode começar exatamente quando a anterior termina.
3. Se os imóveis são diferentes, o serviço amplia a comparação em 30 minutos entre as visitas. O novo horário só é aceito quando há o intervalo completo antes ou depois do compromisso existente. Exatamente 30 minutos é permitido.

Se qualquer comparação indicar conflito, o serviço não grava a visita. Em vez disso,procura alternativas no mesmo dia: começa às 08:00, avança em passos de 30 minutos e deixa de testar quando a duração já não cabe até às 19:00. Cada candidato passa pela mesma regra de sobreposição e deslocamento usada na criação. O horário originalmente solicitado não é incluído entre as alternativas.

As opções livres são ordenadas primeiro para priorizar o mesmo turno do pedido, isto é,manhã antes das 12:00, tarde a partir das 12:00, depois pela proximidade ao horário solicitado e, em caso de empate, pelo horário mais cedo. A API devolve no máximo as três primeiras opções em formato ISO 8601. Se não houver horários livres, a lista `sugestoes` fica vazia.

## Principais desafios de borda: datas e fusos horários

Os principais desafios de casos de borda tratados nesta implementação são:

- **Horário sem fuso:** o campo `inicio` deve incluir data, hora e fuso-horário ISO 8601, por exemplo `2026-06-10T14:00:00-03:00`. Um valor sem fuso é rejeitado porque não identifica um instante sem ambiguidade.
- **Fusos Horários diferente de Brasília:** a requisição pode usar outro fuso. Antes das validações, o horário é convertido para `America/Sao_Paulo`. Por exemplo, `2026-06-10T11:00:00+00:00` corresponde a `2026-06-10T08:00:00-03:00` em Brasília. Esse foi simples de implementar, visto que o único processo crucial era apenas a conversão de fuso. Feito ele, todo o resto do algoritmo não precisava se preocupar com o fuso.
- **Mudança da data local:** a data usada para buscar os agendamentos é obtida depois da conversão para Brasília. DEvido a isso, um horário próximo da meia-noite pode pertencer a um dia diferente no fuso local do que no fuso enviado. Isso teve que ser tratado também.
- **Comparação do horário local:** os limites `08:00` e `19:00` são horários sem fuso. Para compará-los, o código remove o `tzinfo` apenas do valor de relógio extraído; o `datetime` do agendamento permanece com o fuso de Brasília.
- **Escolha dos horários para sugestão:** de todos os horários alternativos para sugestões, eles deveriam ser priorizados por turno, distância absoluta entre eles e por qual era mais cedo.

