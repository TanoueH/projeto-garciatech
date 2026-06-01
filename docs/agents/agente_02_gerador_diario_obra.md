# Agente 02 — Gerador de Diário de Obra

## 1. Objetivo

O **Agente 02 — Gerador de Diário de Obra** tem como objetivo transformar dados brutos de campo em uma minuta estruturada de Diário de Obra, permitindo o registro padronizado das atividades executadas, mão de obra, equipamentos, materiais, ocorrências e pendências da obra.

Nesta versão inicial, o agente opera em modo **MOCK**, utilizando regras programadas em nó `Code` do n8n, sem consumo de API de inteligência artificial.

## 2. Função no sistema Garcia Tech

O agente faz parte da arquitetura de automação documental e operacional do projeto **Garcia Tech**, atuando após a entrada de informações da obra por meio de Webhook.

Fluxo lógico:

Webhook → Set Dados Básicos RDO → Code Mock Gerador RDO → Preparar RDO para PostgreSQL → Insert rdo_obra → Respond to Webhook

## 3. Banco de dados

Os registros são armazenados na tabela `rdo_obra`.

Os campos operacionais compostos são gravados em formato `JSONB`, permitindo posterior consulta, auditoria e uso em dashboards.

## 4. Modo de processamento

modo_processamento = MOCK  
agente_versao = 0.1.0

O modo MOCK permite validar o fluxo completo sem consumo de API externa.

## 5. Situação atual

O fluxo do **Agente 02 — Gerador de Diário de Obra** foi validado com sucesso no n8n self-hosted.

Componentes validados:

- Webhook
- Set Dados Básicos RDO
- Code Mock Gerador RDO
- Preparar RDO para PostgreSQL
- Insert rdo_obra
- Respond to Webhook

O agente está pronto para versionamento no Git e integração futura com o Agente 01 — Triagem Documental.
