# Referência visual de placas — Obra-Caio/SUM

Este diretório registra o padrão visual base observado nos modelos de placas fornecidos como referência para o `AGENTE_006_COMUNICACAO_VISUAL_OBRA`.

Os modelos são referência visual para composição, hierarquia e linguagem. Neste MVP, não há geração de PDF, impressão, execução de RPA, conexão com OpenClaw ou uso do logo SUM como arquivo vetorial.

O template `OBRA_CAIO_SUM_V1` foi aprovado como baseline visual para a placa Obra-Caio/SUM. A fonte visual de verdade é `scripts/dev/preview_placa_template.py`; esse script deve permanecer no projeto como ferramenta oficial de calibração visual.

## Padrão visual base

As placas observadas seguem uma estrutura de leitura rápida para ambiente de obra:

* fundo externo azul-petróleo;
* cabeçalho superior com ícone triangular amarelo de atenção;
* título grande em branco;
* separador vertical entre título e marca;
* marca SUM posicionada à direita no cabeçalho;
* corpo branco central;
* pictograma grande dentro de círculo azul;
* texto principal em fonte grande e negrito;
* linguagem curta, direta e operacional;
* alto contraste para leitura rápida no canteiro.

## Exemplos observados

1. Placa de atenção: "Segure no corrimão ao desce e subir as escadas".
2. Placa de identificação de materiais: "Material básico".
3. Placa de atenção: "Gesso".

## Diretrizes para o Agente 006

O Agente 006 deve usar este padrão apenas como referência preliminar de layout. O resultado deve sugerir campos de composição visual, mas permanecer como rascunho não oficial.

Campos esperados na especificação de layout:

* `titulo_cabecalho`;
* `tipo_icone`;
* `cor_base`;
* `area_pictograma`;
* `texto_principal`;
* `texto_secundario`;
* `formato_sugerido`;
* `estilo_visual_referencia`;
* `observacao_validacao_tecnica`.

Qualquer uso oficial da placa deve ser validado pelo responsável técnico/segurança do trabalho antes de gerar PDF, imprimir ou instalar.

## Fluxo de atualização visual

O fluxo correto para alterar o template é:

```text
preview isolado
    -> validação visual
    -> migração para app/main.py
    -> teste local
    -> fluxo real aprovado
```

Ajustes visuais futuros devem começar no preview isolado em `scripts/dev/preview_placa_template.py`. Depois da validação visual, os mesmos valores e a mesma lógica devem ser migrados para `TEMPLATE_VISUAL_OBRA_CAIO_SUM_V1` e `gerar_pdf_local_placa_aviso` em `app/main.py`.
