# WF_00_WHATSAPP_ENTRADA_API_CORE

## Objetivo

Receber eventos do WhatsApp por meio da Evolution API, usar o n8n somente para
orquestração e encaminhar a entrada normalizada para a API Core do Construction
Science Agents.

## Princípio

O n8n atua apenas como orquestrador do transporte: recebe, normaliza e encaminha
eventos. A lógica de negócio, as validações e as decisões operacionais permanecem
na API Core e nos agentes.

## Fluxo validado

```text
WhatsApp
→ Evolution API
→ n8n (recepção, normalização e encaminhamento)
→ API Core
→ PostgreSQL (persistência e rastreabilidade)
→ MinIO privado (armazenamento de mídia)
```

## Validação do MVP 0.8E

Em 22/07/2026, o fluxo foi validado de ponta a ponta com texto e fotografia real
recebidos pelo WhatsApp. A validação confirmou:

- recepção do evento pela Evolution API e encaminhamento pelo n8n à API Core;
- persistência dos dados operacionais no PostgreSQL;
- armazenamento privado da fotografia no MinIO;
- identificação do remetente e rastreabilidade da origem da mensagem;
- manutenção do n8n exclusivamente como camada de orquestração;
- ausência de alterações automáticas em RDO, cronograma, pendências ou ações.

O teste validou somente a entrada, persistência e guarda privada da mídia. Nenhuma
decisão operacional ou ação sensível foi executada pelo workflow.

## Resultado

O MVP 0.8E foi concluído e validado em 22/07/2026.
