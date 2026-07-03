# Agente 002 — Gerador de RDO

## 1. Identidade

Nome técnico: `AGENTE_002_GERADOR_RDO`

Alias de compatibilidade no código novo: `AGENTE_RDO`

O alias `AGENTE_RDO` deve ser mantido para compatibilidade com os comandos executivos já gerados pelo Agente 007. No MVP 0.4A, ele representa o papel especializado do `AGENTE_002_GERADOR_RDO`.

---

## 2. Papel na arquitetura

O Agente 002 é o especialista em RDO, resumo operacional e diário de obra. Ele recebe comandos auditáveis gerados pelo `AGENTE_007_ORQUESTRADOR_EXECUTIVO` e prepara resultados estruturados para consulta, revisão e aprovação humana.

Fluxo inicial do MVP 0.4A:

```text
Telegram
    -> API Core
    -> Agente 007
    -> comandos_executivos
    -> AGENTE_RDO / AGENTE_002_GERADOR_RDO
    -> comandos_executivos.resultado
```

Nesta etapa, o processamento é determinístico e pode ser mockado. Não há uso obrigatório de LLM externo.

---

## 3. Responsabilidades

O Agente 002 deve:

* preparar rascunhos de RDO;
* gerar resumo executivo operacional;
* consultar pendências e eventos existentes da obra;
* retornar resultado auditável em JSON;
* registrar o resultado em `comandos_executivos.resultado`;
* permitir rastreabilidade por `id_comando`, `correlation_id`, obra e agente de origem;
* indicar campos pendentes de confirmação quando os dados forem insuficientes.

---

## 4. Limites obrigatórios

O Agente 002 não pode:

* alterar RDO oficial sem aprovação humana;
* gerar PDF real no MVP 0.4A;
* imprimir documentos;
* enviar mensagens para terceiros;
* conectar OpenClaw;
* executar RPA;
* inventar informações operacionais ausentes;
* bypassar o registro em banco.

Qualquer oficialização, alteração sensível, impressão, envio externo ou execução em sistema de terceiros deve passar por comando auditável, validação de política e aprovação humana quando aplicável.

---

## 5. Resultado esperado

O resultado salvo em `comandos_executivos.resultado` deve conter:

* `tipo_resultado`: `RASCUNHO_RDO` ou `RESUMO_EXECUTIVO_RDO`;
* agente processador;
* alias de compatibilidade;
* modo de processamento;
* identificadores de auditoria;
* resumo operacional;
* pendências e eventos consultados;
* controles explícitos de não execução externa.

O comando só deve passar para `CONCLUIDO` depois que o resultado tiver sido salvo.
