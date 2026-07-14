-- Migration 018 - MVP 0.8B: aprovacao tecnica de revisoes documentais.

CREATE TABLE IF NOT EXISTS public.aprovacoes_revisoes_documentais_obra (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'construtora-piloto',
    obra_codigo TEXT NOT NULL,
    revisao_documental_id BIGINT NOT NULL,
    documento_minio_id BIGINT NULL,
    documento_substituido_id BIGINT NULL,
    revisao_anterior_id BIGINT NULL,
    disciplina TEXT NULL,
    area TEXT NULL,
    codigo_documento TEXT NULL,
    revisao_detectada TEXT NULL,
    decisao TEXT NOT NULL,
    status_revisao_resultante TEXT NOT NULL,
    status_vigencia_resultante TEXT NOT NULL,
    aprovado BOOLEAN NOT NULL DEFAULT FALSE,
    rejeitado BOOLEAN NOT NULL DEFAULT FALSE,
    ajustes_solicitados BOOLEAN NOT NULL DEFAULT FALSE,
    motivo TEXT NULL,
    observacao TEXT NULL,
    decisor_nome TEXT NULL,
    decisor_telegram_user_id TEXT NULL,
    decisor_telegram_username TEXT NULL,
    decisor_chat_id TEXT NULL,
    canal TEXT NOT NULL DEFAULT 'telegram',
    origem TEXT NOT NULL DEFAULT 'AGENTE_007_ORQUESTRADOR_EXECUTIVO',
    enviado_para_terceiros BOOLEAN NOT NULL DEFAULT FALSE,
    gerou_link_publico BOOLEAN NOT NULL DEFAULT FALSE,
    alterou_rdo_oficial BOOLEAN NOT NULL DEFAULT FALSE,
    alterou_cronograma BOOLEAN NOT NULL DEFAULT FALSE,
    executou_rpa BOOLEAN NOT NULL DEFAULT FALSE,
    sincronizou_openproject BOOLEAN NOT NULL DEFAULT FALSE,
    alterou_minio BOOLEAN NOT NULL DEFAULT FALSE,
    moveu_arquivo_minio BOOLEAN NOT NULL DEFAULT FALSE,
    apagou_arquivo_minio BOOLEAN NOT NULL DEFAULT FALSE,
    liberou_execucao_campo BOOLEAN NOT NULL DEFAULT FALSE,
    metadados JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_aprovacoes_revisao_documental FOREIGN KEY (revisao_documental_id)
        REFERENCES public.revisoes_documentais_obra (id)
);

CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_obra_codigo ON public.aprovacoes_revisoes_documentais_obra (obra_codigo);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_revisao_id ON public.aprovacoes_revisoes_documentais_obra (revisao_documental_id);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_documento_minio_id ON public.aprovacoes_revisoes_documentais_obra (documento_minio_id);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_documento_substituido_id ON public.aprovacoes_revisoes_documentais_obra (documento_substituido_id);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_revisao_anterior_id ON public.aprovacoes_revisoes_documentais_obra (revisao_anterior_id);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_disciplina ON public.aprovacoes_revisoes_documentais_obra (disciplina);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_area ON public.aprovacoes_revisoes_documentais_obra (area);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_codigo_documento ON public.aprovacoes_revisoes_documentais_obra (codigo_documento);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_revisao_detectada ON public.aprovacoes_revisoes_documentais_obra (revisao_detectada);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_decisao ON public.aprovacoes_revisoes_documentais_obra (decisao);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_status_revisao ON public.aprovacoes_revisoes_documentais_obra (status_revisao_resultante);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_status_vigencia ON public.aprovacoes_revisoes_documentais_obra (status_vigencia_resultante);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_aprovado ON public.aprovacoes_revisoes_documentais_obra (aprovado);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_rejeitado ON public.aprovacoes_revisoes_documentais_obra (rejeitado);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_ajustes ON public.aprovacoes_revisoes_documentais_obra (ajustes_solicitados);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_revisoes_criado_em ON public.aprovacoes_revisoes_documentais_obra (criado_em);

ALTER TABLE public.revisoes_documentais_obra
    ADD COLUMN IF NOT EXISTS decisao_tecnica TEXT NULL,
    ADD COLUMN IF NOT EXISTS decisao_tecnica_por TEXT NULL,
    ADD COLUMN IF NOT EXISTS decisao_tecnica_em TIMESTAMPTZ NULL,
    ADD COLUMN IF NOT EXISTS motivo_decisao TEXT NULL,
    ADD COLUMN IF NOT EXISTS observacao_decisao TEXT NULL,
    ADD COLUMN IF NOT EXISTS substituida_por_revisao_id BIGINT NULL,
    ADD COLUMN IF NOT EXISTS substituida_em TIMESTAMPTZ NULL;

-- A migration 017 antecede o estado AJUSTES_SOLICITADOS.
ALTER TABLE public.revisoes_documentais_obra
    DROP CONSTRAINT IF EXISTS chk_revisoes_documentais_status_revisao;
ALTER TABLE public.revisoes_documentais_obra
    ADD CONSTRAINT chk_revisoes_documentais_status_revisao CHECK (status_revisao IN (
        'RECEBIDO_PARA_ANALISE', 'EM_ANALISE_TECNICA', 'APROVADO_COMO_VIGENTE',
        'REJEITADO', 'AJUSTES_SOLICITADOS', 'SUBSTITUIDO', 'OBSOLETO', 'AS_BUILT'
    ));

COMMENT ON TABLE public.aprovacoes_revisoes_documentais_obra IS
'Trilha auditavel de decisoes tecnicas documentais; vigencia nao libera execucao de campo.';
