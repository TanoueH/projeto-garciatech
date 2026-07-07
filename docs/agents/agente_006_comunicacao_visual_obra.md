# Agente 006 — Comunicação Visual de Obra

## 1. Identidade

Nome técnico: `AGENTE_006_COMUNICACAO_VISUAL_OBRA`

Alias funcional: Agente de Placas de Aviso / Comunicação Visual de Obra.

O Agente 006 é o agente lógico responsável por preparar rascunhos textuais e especificações operacionais preliminares de placas de aviso para obra.

O Agente 006 deve usar como referência visual os modelos fornecidos pelo Eng. Renato para placas da Obra-Caio/SUM, mantendo padrão de cor, composição, hierarquia visual, contraste e estrutura de cabeçalho/corpo, sem gerar PDF ou impressão automática sem aprovação.

A referência visual base está documentada em `docs/reference/placas/README.md`. Ela registra o padrão observado: fundo azul-petróleo, cabeçalho com ícone triangular amarelo de atenção, título grande em branco, separador vertical, marca SUM à direita, corpo branco central, pictograma grande em círculo azul, texto principal grande/negrito e linguagem curta para leitura rápida em obra. A marca SUM é tratada apenas como referência visual do modelo; nenhum arquivo vetorial de logo deve ser usado neste MVP.

---

## 2. Papel na arquitetura

O Agente 006 recebe comandos auditáveis gerados pelo `AGENTE_007_ORQUESTRADOR_EXECUTIVO` e prepara apenas conteúdo preliminar para revisão humana.

Fluxo do MVP 0.5A:

```text
Telegram
    -> API Core
    -> Agente 007
    -> comandos_executivos
    -> AGENTE_006_COMUNICACAO_VISUAL_OBRA
    -> comandos_executivos.resultado
```

Neste MVP o processamento é determinístico/mockado. Não há geração de PDF real, impressão, RPA, OpenClaw ou envio a terceiros.

---

## 3. Responsabilidades

O Agente 006 deve:

* preparar rascunho textual de placa de aviso;
* sugerir título;
* sugerir mensagem principal;
* sugerir mensagem secundária;
* sugerir tipo de placa;
* sugerir formato;
* sugerir campos preliminares de layout conforme referência Obra-Caio/SUM;
* sugerir local de instalação, quando informado ou inferível pela mensagem;
* registrar que o conteúdo é rascunho não oficial;
* indicar campos que exigem confirmação;
* exigir aprovação posterior para PDF, impressão ou instalação.

---

## 4. Limites obrigatórios

O Agente 006 não pode:

* gerar PDF real;
* imprimir;
* executar RPA;
* conectar OpenClaw;
* enviar mensagem a terceiros;
* alterar RDO oficial;
* afirmar conformidade normativa final;
* bypassar aprovação humana para PDF, impressão ou instalação;
* inventar dados operacionais ausentes.

Todo conteúdo deve indicar que o rascunho precisa ser validado pelo responsável técnico/segurança do trabalho antes de uso oficial.

---

## 5. Matriz de processamento no MVP 0.5A

| Tipo de comando | Status aceito para processamento | Resultado esperado | Observação |
| --- | --- | --- | --- |
| `PREPARAR_PLACA_AVISO` | `PENDENTE` | `tipo_resultado = RASCUNHO_PLACA_AVISO` | Gera rascunho textual não oficial e controles de não execução externa. |
| `GERAR_PDF_PLACA_AVISO` | não processar quando `AGUARDANDO_APROVACAO` | nenhum PDF real | Ação sensível; exige aprovação posterior. |
| `IMPRIMIR_PLACA_AVISO` | não processar quando `AGUARDANDO_APROVACAO` | nenhuma impressão | Ação sensível; exige aprovação posterior. |
| `INSTALAR_PLACA_AVISO` | não processar quando `AGUARDANDO_APROVACAO` | nenhuma instalação | Ação sensível; exige aprovação posterior. |

---

## 6. Resultado esperado

O resultado salvo em `comandos_executivos.resultado` deve conter:

* `tipo_resultado`: `RASCUNHO_PLACA_AVISO`;
* `agente`: `AGENTE_006_COMUNICACAO_VISUAL_OBRA`;
* `obra_codigo`;
* `tipo_comando`;
* `titulo`;
* `titulo_cabecalho`;
* `mensagem_principal`;
* `mensagem_secundaria`;
* `tipo_placa`;
* `tipo_icone`;
* `cor_base`;
* `area_pictograma`;
* `texto_principal`;
* `texto_secundario`;
* `formato_sugerido`;
* `estilo_visual_referencia`;
* `observacao_validacao_tecnica`;
* `local_instalacao_sugerido`;
* `status`: `RASCUNHO_NAO_OFICIAL`;
* `campos_a_confirmar`;
* `controles_operacionais`.

Controles operacionais obrigatórios:

```json
{
  "gerou_pdf_real": false,
  "imprimiu": false,
  "executou_rpa": false,
  "conectou_openclaw": false,
  "alterou_rdo_oficial": false,
  "enviou_mensagem_terceiros": false,
  "requer_aprovacao_para_pdf_ou_impressao": true
}
```

O comando só deve passar para `CONCLUIDO` depois que o resultado tiver sido salvo.

---

## 7. Endpoint de processamento

Endpoint controlado:

```text
POST /agentes/comunicacao-obra/processar-comando
```

O endpoint deve:

* buscar o próximo comando `PENDENTE` para `AGENTE_006_COMUNICACAO_VISUAL_OBRA`;
* processar apenas `PREPARAR_PLACA_AVISO`;
* ignorar comandos `AGUARDANDO_APROVACAO`;
* gerar resultado determinístico/mockado;
* salvar resultado em `comandos_executivos.resultado`;
* atualizar status para `CONCLUIDO` somente após salvar resultado;
* retornar `mensagem_resposta_executiva` curta.
