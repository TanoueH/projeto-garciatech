# Integração — Agente 02 → Agente 03

## Objetivo

Esta integração conecta o Agente 02 — Gerador de Diário de Obra ao Agente 03 — Controle de Pendências da Obra.

Quando o RDO gerado apresenta `possui_pendencias = true`, o Agente 02 aciona automaticamente o Agente 03 por meio de uma requisição HTTP para registrar a pendência na tabela `pendencias_obra`.

## Fluxo

Webhook RDO  
→ Set Dados Básicos RDO  
→ Code Mock Gerador RDO  
→ Preparar RDO para PostgreSQL  
→ Insert rdo_obra  
→ IF possui_pendencias  
→ HTTP Request para Agente 03  
→ Registro em pendencias_obra  

## Endpoint acionado

POST /webhook/registrar-pendencia

## Tabelas envolvidas

- rdo_obra
- pendencias_obra

## Status

Integração validada em ambiente local com n8n self-hosted, PostgreSQL e Docker Compose.
