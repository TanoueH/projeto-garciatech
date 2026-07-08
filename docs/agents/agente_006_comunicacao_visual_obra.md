# Agente 006 — Comunicação Visual de Obra

## 1. Identidade

Nome técnico: `AGENTE_006_COMUNICACAO_VISUAL_OBRA`

Alias funcional: Agente de Placas de Aviso / Comunicação Visual de Obra.

O Agente 006 é o agente lógico responsável por preparar rascunhos textuais e especificações operacionais preliminares de placas de aviso para obra.

O Agente 006 deve usar como referência visual os modelos fornecidos pelo Eng. Renato para placas da Obra-Caio/SUM, mantendo padrão de cor, composição, hierarquia visual, contraste e estrutura de cabeçalho/corpo, sem gerar PDF ou impressão automática sem aprovação.

A referência visual base está documentada em `docs/reference/placas/README.md`. Ela registra o padrão observado: fundo azul-petróleo, cabeçalho com ícone triangular amarelo de atenção, título grande em branco, separador vertical, marca SUM à direita, corpo branco central, pictograma grande em círculo azul, texto principal grande/negrito e linguagem curta para leitura rápida em obra. A marca SUM é tratada apenas como referência visual do modelo; nenhum arquivo vetorial de logo deve ser usado neste MVP.

O template `OBRA_CAIO_SUM_V1` está aprovado como baseline visual da placa Obra-Caio/SUM. A fonte visual de verdade dessa baseline é `scripts/dev/preview_placa_template.py`; ajustes visuais futuros devem ser feitos primeiro nesse preview isolado e somente depois migrados para `app/main.py`.

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

No MVP 0.5A o processamento é determinístico/mockado. Não há geração de PDF real, impressão, RPA, OpenClaw ou envio a terceiros.

Fluxo adicional do MVP 0.5B:

```text
Telegram
    -> API Core
    -> Agente 007
    -> aprovação humana do comando GERAR_PDF_PLACA_AVISO
    -> comandos_executivos.status = APROVADO
    -> AGENTE_006_COMUNICACAO_VISUAL_OBRA
    -> PDF local em outputs/placas/{obra_codigo}/
    -> comandos_executivos.resultado + evidencias
```

No MVP 0.5B o Agente 006 pode gerar apenas PDF local de rascunho não oficial após aprovação humana registrada. O PDF não é impresso, não é enviado a terceiros, não executa RPA, não conecta OpenClaw e não altera RDO oficial.

---

## 3. Responsabilidades

O Agente 006 deve:

* preparar rascunho textual de placa de aviso;
* gerar PDF local de rascunho de placa de aviso somente quando o comando `GERAR_PDF_PLACA_AVISO` estiver `APROVADO`;
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

* gerar PDF sem aprovação humana registrada;
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

## 5. Matriz de processamento no MVP 0.5A/0.5B

| Tipo de comando | Status aceito para processamento | Resultado esperado | Observação |
| --- | --- | --- | --- |
| `PREPARAR_PLACA_AVISO` | `PENDENTE` | `tipo_resultado = RASCUNHO_PLACA_AVISO` | Gera rascunho textual não oficial e controles de não execução externa. |
| `GERAR_PDF_PLACA_AVISO` | `APROVADO` | `tipo_resultado = PDF_PLACA_AVISO_GERADO` | Gera PDF local simples em `outputs/placas/{obra_codigo}/` como rascunho não oficial. |
| `GERAR_PDF_PLACA_AVISO` | não processar quando `PENDENTE` ou `AGUARDANDO_APROVACAO` | nenhum PDF | Ação sensível; exige aprovação humana anterior. |
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

Para `GERAR_PDF_PLACA_AVISO` aprovado no MVP 0.5B, o resultado salvo em `comandos_executivos.resultado` deve conter:

* `tipo_resultado`: `PDF_PLACA_AVISO_GERADO`;
* `status`: `PDF_RASCUNHO_GERADO`;
* `arquivo_pdf`;
* `obra_codigo`;
* `agente`: `AGENTE_006_COMUNICACAO_VISUAL_OBRA`;
* `comando_origem_id`;
* `controles_operacionais`.

Controles operacionais obrigatórios do PDF:

```json
{
  "gerou_pdf_real": true,
  "imprimiu": false,
  "executou_rpa": false,
  "conectou_openclaw": false,
  "alterou_rdo_oficial": false,
  "enviou_mensagem_terceiros": false,
  "rascunho_nao_oficial": true
}
```

O comando `GERAR_PDF_PLACA_AVISO` só deve passar para `CONCLUIDO` depois que o arquivo PDF existir localmente e o caminho tiver sido salvo em `resultado` e `evidencias`.

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

Endpoint de geração de PDF local do MVP 0.5B:

```text
POST /agentes/comunicacao-obra/gerar-pdf-placa
```

O endpoint deve:

* buscar o próximo comando `GERAR_PDF_PLACA_AVISO` com status `APROVADO`;
* não processar comandos `PENDENTE` ou `AGUARDANDO_APROVACAO`;
* gerar um PDF local simples em A4 vertical;
* seguir a referência visual documentada em `docs/reference/placas/README.md`;
* usar o template `OBRA_CAIO_SUM_V1`, aprovado como baseline visual Obra-Caio/SUM;
* salvar o arquivo em `outputs/placas/{obra_codigo}/`;
* salvar o caminho do PDF em `comandos_executivos.resultado` e `comandos_executivos.evidencias`;
* atualizar status para `CONCLUIDO` somente após salvar PDF, resultado e evidências;
* retornar `acoes_externas_executadas = false`.

O PDF é rascunho local não oficial. O endpoint não imprime, não envia a terceiros, não altera `rdo_obra`, não executa RPA, não conecta OpenClaw e não afirma conformidade normativa final.
