# Agente 007 — Orquestrador Executivo do Eng. Renato

## 1. Identidade

Nome técnico: `AGENTE_007_ORQUESTRADOR_EXECUTIVO`

O Agente 007 é o agente executivo responsável por receber comandos do Eng. Renato via Telegram, interpretar a intenção, encaminhar para o agente especializado correto e gerar comandos auditáveis para execução controlada.

Este agente não substitui o Eng. Renato. Ele atua como camada de apoio, triagem, organização e orquestração.

---

## 2. Papel na arquitetura

A arquitetura de comunicação do projeto é:

```text
WhatsApp = canal operacional da obra
Telegram = canal executivo do Eng. Renato
OpenClaw / Telegram Gateway = entrada conversacional
API Core = validação, autenticação, auditoria e roteamento
Agente 007 = orquestrador executivo
Agentes especializados = execução cognitiva
PostgreSQL = memória operacional e auditoria
Ferramentas/RPA = execução controlada mediante comando auditável
```

---

## 3. Matriz de intenções RDO no MVP 0.4B

O classificador determinístico de `/telegram/entrada` deve separar as intenções de RDO antes de cair na consulta genérica.

| Intenção | Exemplos | Agente destino | Requer aprovação | Status inicial |
| --- | --- | --- | --- | --- |
| `PREPARAR_RDO` | "prepare rascunho do RDO", "prepare o RDO", "monte o RDO", "crie um rascunho do diário de obra", "prepare o diário de obra" | `AGENTE_RDO` | `false` | `PENDENTE` |
| `CONSULTAR_RDO` | "consulte o RDO", "resuma o RDO", "qual o status do RDO", "me mostre o diário de obra" | `AGENTE_RDO` | `false` | `PENDENTE` |
| `ATUALIZAR_RDO` | "atualize o RDO oficial", "altere o RDO", "corrija o RDO oficial", "registre oficialmente no RDO" | `AGENTE_RDO` | `true` | `AGUARDANDO_APROVACAO` |
| `GERAR_PDF_RDO` | "gere o PDF do RDO", "emita o PDF do diário", "feche o RDO em PDF" | `AGENTE_RDO` | `true` | `AGUARDANDO_APROVACAO` |

Prioridade obrigatória:

1. confirmações e cancelamentos continuam antes das intenções RDO;
2. `GERAR_PDF_RDO` vem antes de preparação e consulta;
3. `ATUALIZAR_RDO` vem antes de consulta;
4. `PREPARAR_RDO` vem antes de consulta quando houver verbos como preparar, montar, criar, elaborar ou menção a rascunho.

No MVP 0.4B o Agente 007 apenas registra comandos auditáveis em `comandos_executivos`. Ele não gera PDF real, não imprime, não executa RPA, não conecta OpenClaw e não altera `rdo_obra`.

---

## 4. Matriz de intenções de placas no MVP 0.5A

O classificador determinístico de `/telegram/entrada` deve reconhecer pedidos de comunicação visual de obra e encaminhar ao `AGENTE_006_COMUNICACAO_VISUAL_OBRA`.

| Intenção | Exemplos | Agente destino | Requer aprovação | Status inicial |
| --- | --- | --- | --- | --- |
| `PREPARAR_PLACA_AVISO` | "prepare uma placa", "gerar placa de aviso", "crie uma placa para a obra", "placa de uso obrigatório de EPI", "aviso para o canteiro", "comunicado para a obra", "sinalização da obra", "placa de segurança" | `AGENTE_006_COMUNICACAO_VISUAL_OBRA` | `false` | `PENDENTE` |
| `GERAR_PDF_PLACA_AVISO` | "gere o PDF da placa", "emita o PDF da placa", "PDF do aviso" | `AGENTE_006_COMUNICACAO_VISUAL_OBRA` | `true` | `AGUARDANDO_APROVACAO` |
| `IMPRIMIR_PLACA_AVISO` | "imprima a placa", "mande imprimir a placa", "solicite impressão da placa" | `AGENTE_006_COMUNICACAO_VISUAL_OBRA` | `true` | `AGUARDANDO_APROVACAO` |
| `INSTALAR_PLACA_AVISO` | "instale a placa", "fixe a placa", "coloque a placa no canteiro" | `AGENTE_006_COMUNICACAO_VISUAL_OBRA` | `true` | `AGUARDANDO_APROVACAO` |

Prioridade obrigatória:

1. confirmações e cancelamentos continuam antes das intenções de placas;
2. ações sensíveis de placa (`GERAR_PDF_PLACA_AVISO`, `IMPRIMIR_PLACA_AVISO`, `INSTALAR_PLACA_AVISO`) vêm antes de preparação;
3. intenções de placas vêm antes da impressão genérica;
4. preparação de placa gera apenas rascunho textual não oficial.

No MVP 0.5A o Agente 007 apenas registra comandos auditáveis em `comandos_executivos`. O Agente 006 prepara rascunho textual e especificação operacional preliminar. Nenhum PDF real é gerado, nenhuma impressão é executada, nenhuma instalação é feita, nenhum RPA é executado, OpenClaw não é conectado e nenhuma mensagem é enviada a terceiros. O conteúdo não afirma conformidade normativa final e deve ser validado pelo responsável técnico/segurança do trabalho antes de uso oficial.

---

## 5. Aprovação e cancelamento no MVP 0.4D

O endpoint `/telegram/entrada` também reconhece comandos executivos curtos de aprovação ou cancelamento enviados pelo Telegram:

| Frase aceita | Ação | Comando alvo | Status exigido no alvo | Novo status do alvo | Executa ação externa |
| --- | --- | --- | --- | --- | --- |
| `aprovar comando 20` | Aprovar | `comandos_executivos.id = 20` | `AGUARDANDO_APROVACAO` | `APROVADO` | Não |
| `aprova comando 20` | Aprovar | `comandos_executivos.id = 20` | `AGUARDANDO_APROVACAO` | `APROVADO` | Não |
| `autorizar comando 20` | Aprovar | `comandos_executivos.id = 20` | `AGUARDANDO_APROVACAO` | `APROVADO` | Não |
| `confirmar comando 20` | Aprovar | `comandos_executivos.id = 20` | `AGUARDANDO_APROVACAO` | `APROVADO` | Não |
| `cancelar comando 20` | Cancelar | `comandos_executivos.id = 20` | `AGUARDANDO_APROVACAO` | `CANCELADO` | Não |
| `cancela comando 20` | Cancelar | `comandos_executivos.id = 20` | `AGUARDANDO_APROVACAO` | `CANCELADO` | Não |
| `rejeitar comando 20` | Cancelar | `comandos_executivos.id = 20` | `AGUARDANDO_APROVACAO` | `CANCELADO` | Não |

O identificador principal é o `id` numérico da tabela `comandos_executivos`. Quando a mensagem traz um UUID válido, o Agente 007 pode tratar o valor como `id_comando`.

### Matriz de decisão

| Situação | Efeito no comando alvo | Auditoria | Resposta executiva |
| --- | --- | --- | --- |
| Usuário não autorizado | Não altera o alvo | Registra evento e comando de bloqueio conforme padrão atual | Informa bloqueio seguro |
| Comando alvo inexistente | Não altera nada | Registra evento Telegram | Informa que o comando não foi encontrado |
| Comando alvo com status diferente de `AGUARDANDO_APROVACAO` | Não altera o alvo | Registra evento Telegram | Informa o status atual |
| Aprovação válida | Atualiza status para `APROVADO` | Preenche `aprovado_por`, `aprovado_em`, `resultado` e `evidencias` | Confirma aprovação |
| Cancelamento/rejeição válido | Atualiza status para `CANCELADO` | Registra `resultado` e `evidencias` | Confirma cancelamento |

Status envolvidos no MVP 0.4D:

* `AGUARDANDO_APROVACAO`: único status aceito para aprovação ou cancelamento do comando alvo.
* `APROVADO`: decisão humana registrada; não dispara processamento, RPA, PDF, impressão, envio externo ou alteração de RDO neste MVP.
* `CANCELADO`: decisão humana registrada; encerra o comando sem execução.

Restrição explícita: `APROVADO` é apenas um estado auditável neste MVP. A aprovação não executa ação externa, não gera PDF, não altera `rdo_obra`, não imprime, não executa RPA, não conecta OpenClaw e não envia mensagem para terceiros.

---

## 6. Resposta real no Telegram no MVP 0.4E

O MVP 0.4E fecha o ciclo operacional de aprovação/cancelamento pelo Telegram:

```text
mensagem Telegram
    ↓
getUpdates
    ↓
scripts/telegram/processar_aprovacao_pendente_e_responder.py
    ↓
/telegram/entrada
    ↓
comando executivo atualizado e auditado
    ↓
sendMessage para o mesmo chat_id de origem
```

O script `scripts/telegram/processar_aprovacao_pendente_e_responder.py` é o courier Telegram deste fluxo. Ele lê `TELEGRAM_BOT_TOKEN` apenas do ambiente, consulta `getUpdates`, filtra somente mensagens de texto relacionadas a aprovação ou cancelamento de comando executivo e encaminha essas mensagens para `/telegram/entrada`.

Frases aceitas no MVP 0.4E:

* `aprovar comando N`
* `aprova comando N`
* `autorizar comando N`
* `confirmar comando N`
* `cancelar comando N`
* `cancela comando N`
* `rejeitar comando N`

Mensagens não relacionadas são ignoradas sem erro. O offset persistente local próprio do fluxo de aprovação é:

```text
.runtime/telegram/agente_007_aprovacao_offset.json
```

O script aceita `--reset-offset`, `--offset`, `--limit` e `--dry-run`. O `--dry-run` processa a mensagem na API Core, mas não envia `sendMessage`.

Quando a API Core retorna `mensagem_resposta_executiva` e `telegram_chat_id`, o script envia a resposta real pelo Telegram somente para esse `telegram_chat_id`. O `chat_id` nunca é aceito por argumento externo, não é decidido pelo script e não pode ser arbitrado na linha de comando.

O resumo impresso pelo script é seguro e não expõe token nem conteúdo completo da mensagem. Ele deve conter apenas dados operacionais resumidos, como `update_id`, `intencao`, `comando_executivo_id`, `status_comando`, `telegram_chat_id` mascarado, `enviado` e `dry_run`.

Restrição explícita do MVP 0.4E: a resposta real no Telegram confirma a decisão auditada, mas `APROVADO` ainda não executa ação externa. Não gera PDF, não altera `rdo_obra`, não imprime, não executa RPA, não conecta OpenClaw e não oficializa RDO.
