# Construction Science Agents

**Construction Science Agents** é uma arquitetura experimental e evolutiva para automação inteligente de gestão de obras civis, combinando agentes, APIs, banco de dados, automação de mensagens e observabilidade.

O MVP atual é o **Obra-Caio Control Tower**, desenvolvido para organizar entradas operacionais de obra, registrar mensagens, apoiar RDOs, pendências, compras, documentos e fluxos de decisão técnica.

## Objetivo do MVP

O objetivo inicial é transformar mensagens e documentos recebidos por canais operacionais, como WhatsApp e e-mail, em registros estruturados no banco de dados, permitindo posterior processamento por agentes especializados.

A arquitetura foi reorganizada para que o **n8n deixe de ser o cérebro do sistema** e passe a atuar como camada de entrada, saída e integração. A lógica de negócio passa a residir no serviço Python/FastAPI `api_core`.

## Arquitetura atual

```text
WhatsApp / Evolution API
        ↓
n8n
        ↓
api_core / FastAPI
        ↓
PostgreSQL
        ↓
agent_worker
```

## Serviços principais

| Serviço         | Função                          | Acesso local                   |
| --------------- | ------------------------------- | ------------------------------ |
| `api_core`      | API principal do sistema        | http://127.0.0.1:8000/docs     |
| `agent_worker`  | Worker de agentes em background | Sem interface web              |
| `n8n`           | Entrada/saída e automações      | http://127.0.0.1:5678          |
| `postgres`      | Banco de dados principal        | 127.0.0.1:15432                |
| `redis`         | Cache/fila interna              | Interno                        |
| `evolution-api` | Integração WhatsApp             | http://127.0.0.1:8080/manager/ |
| `minio`         | Armazenamento de documentos     | http://127.0.0.1:9001          |
| `grafana`       | Dashboards                      | http://127.0.0.1:13001         |
| `dashboard`     | Painel local de desenvolvimento | http://127.0.0.1:8109          |

## Estrutura principal

```text
.
├── app/
│   ├── main.py
│   └── workers/
│       └── agent_worker.py
├── dashboard/
│   └── index.html
├── data/
├── docs/
├── infra/
│   └── n8n/
│       └── workflows/
├── outputs/
├── docker-compose.yml
├── docker-compose.override.example.yml
├── Dockerfile.api
├── requirements-api.txt
└── README.md
```

## Subir a stack

Antes de subir, crie um arquivo `.env` local baseado nas variáveis necessárias do projeto. O `.env` não deve ser versionado.

```bash
docker compose up -d
```

Verificar serviços:

```bash
docker compose ps
```

Verificar saúde da API:

```bash
curl -s http://127.0.0.1:8000/status/health | python3 -m json.tool
```

## Teste da API Core

Enviar uma entrada manual:

```bash
curl -s -X POST http://127.0.0.1:8000/webhooks/entrada \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "construtora-piloto",
    "obra_codigo": "OBRA-CAIO",
    "canal": "teste",
    "remetente_nome": "Heloi",
    "tipo_mensagem": "texto",
    "conteudo": "OBRA-CAIO: teste de entrada operacional pelo api_core.",
    "anexos": []
  }' | python3 -m json.tool
```

Consultar registros no banco:

```bash
docker compose exec postgres psql -U garcia_admin -d garcia_db -c "
SELECT id, obra_codigo, canal, remetente_nome, tipo_mensagem, status_processamento, criado_em
FROM mensagens_recebidas
ORDER BY id DESC
LIMIT 10;
"
```

## Idempotência

O endpoint `/webhooks/entrada` gera uma `idempotency_key` a partir da obra, canal e hash do payload.

Comportamento esperado:

```text
Primeira chamada com payload novo  → RECEBIDA
Chamada repetida com mesmo payload → DUPLICADA
```

A segunda chamada não cria novo registro nem altera o registro original.

## Workflow n8n recomendado

O n8n deve atuar como camada leve de entrada e saída.

Fluxo recomendado:

```text
WF_00_WHATSAPP_ENTRADA_API_CORE

Webhook Evolution
        ↓
Normalização mínima
        ↓
HTTP Request
POST http://api_core:8000/webhooks/entrada
        ↓
Resposta operacional ao remetente
```

Dentro do container do n8n, nunca usar `127.0.0.1:8000` para chamar a API. Usar o nome do serviço Docker:

```text
http://api_core:8000/webhooks/entrada
```

## Segurança

Não versionar:

```text
.env
backups/
outputs/debug/
docker-compose.override.yml
arquivos com API keys
exports brutos de workflows contendo credenciais
```

Antes de qualquer commit, verificar segredos:

```bash
git diff --cached | grep -niE "sk-|apikey|api_key|password|secret|token|admin123|garcia_admin_123|minioadmin"
```

## Status atual

* Stack MVP Docker: operacional.
* `api_core`: saudável.
* PostgreSQL: saudável.
* n8n: ativo.
* Evolution API: ativa.
* Dashboard local: ativo.
* Idempotência da entrada: validada.
* Próxima etapa: limpeza e reconstrução dos workflows n8n.
