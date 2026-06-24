# WF_00_WHATSAPP_ENTRADA_API_CORE

## Objetivo

Receber eventos da Evolution API pelo n8n, normalizar minimamente a entrada e encaminhar para a API principal do Construction Science Agents.

## Princípio

O n8n não executa lógica de negócio. Ele apenas recebe, normaliza e encaminha.

## Fluxo

```text
Webhook Evolution
→ Code: Normalizar Entrada
→ HTTP Request: POST api_core
→ Respond to Webhook
