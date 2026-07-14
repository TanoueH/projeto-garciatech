-- Migration 019 - MVP 0.8C: liberacao documental controlada para uso em campo.

CREATE TABLE IF NOT EXISTS public.liberacoes_revisoes_documentais_campo_obra (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'construtora-piloto',
    obra_codigo TEXT NOT NULL,
    revisao_documental_id BIGINT NOT NULL,
    aprovacao_revisao_id BIGINT NULL,
    documento_minio_id BIGINT NULL,
    disciplina TEXT NULL,
    area TEXT NULL,
    codigo_documento TEXT NULL,
    revisao_detectada TEXT NULL,
    decisao TEXT NOT NULL,
    status_liberacao_resultante TEXT NOT NULL,
    liberado_para_campo BOOLEAN NOT NULL DEFAULT FALSE,
    liberacao_suspensa BOOLEAN NOT NULL DEFAULT FALSE,
    liberacao_revogada BOOLEAN NOT NULL DEFAULT FALSE,
    motivo TEXT NULL,
    observacao TEXT NULL,
    instrucoes_campo TEXT NULL,
    decisor_nome TEXT NULL,
    decisor_telegram_user_id TEXT NULL,
    decisor_telegram_username TEXT NULL,
    decisor_chat_id TEXT NULL,
    canal TEXT NOT NULL DEFAULT 'telegram',
    origem TEXT NOT NULL DEFAULT 'AGENTE_007_ORQUESTRADOR_EXECUTIVO',
    enviado_para_terceiros BOOLEAN NOT NULL DEFAULT FALSE,
    gerou_link_publico BOOLEAN NOT NULL DEFAULT FALSE,
    enviou_arquivo BOOLEAN NOT NULL DEFAULT FALSE,
    alterou_rdo_oficial BOOLEAN NOT NULL DEFAULT FALSE,
    alterou_cronograma BOOLEAN NOT NULL DEFAULT FALSE,
    executou_rpa BOOLEAN NOT NULL DEFAULT FALSE,
    sincronizou_openproject BOOLEAN NOT NULL DEFAULT FALSE,
    alterou_minio BOOLEAN NOT NULL DEFAULT FALSE,
    moveu_arquivo_minio BOOLEAN NOT NULL DEFAULT FALSE,
    apagou_arquivo_minio BOOLEAN NOT NULL DEFAULT FALSE,
    criou_ordem_servico BOOLEAN NOT NULL DEFAULT FALSE,
    autorizou_execucao_servico BOOLEAN NOT NULL DEFAULT FALSE,
    metadados JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_liberacoes_campo_revisao FOREIGN KEY (revisao_documental_id)
        REFERENCES public.revisoes_documentais_obra (id),
    CONSTRAINT fk_liberacoes_campo_aprovacao FOREIGN KEY (aprovacao_revisao_id)
        REFERENCES public.aprovacoes_revisoes_documentais_obra (id)
);

CREATE INDEX IF NOT EXISTS idx_liberacoes_campo_obra_codigo ON public.liberacoes_revisoes_documentais_campo_obra (obra_codigo);
CREATE INDEX IF NOT EXISTS idx_liberacoes_campo_revisao_id ON public.liberacoes_revisoes_documentais_campo_obra (revisao_documental_id);
CREATE INDEX IF NOT EXISTS idx_liberacoes_campo_aprovacao_id ON public.liberacoes_revisoes_documentais_campo_obra (aprovacao_revisao_id);
CREATE INDEX IF NOT EXISTS idx_liberacoes_campo_documento_minio_id ON public.liberacoes_revisoes_documentais_campo_obra (documento_minio_id);
CREATE INDEX IF NOT EXISTS idx_liberacoes_campo_disciplina ON public.liberacoes_revisoes_documentais_campo_obra (disciplina);
CREATE INDEX IF NOT EXISTS idx_liberacoes_campo_area ON public.liberacoes_revisoes_documentais_campo_obra (area);
CREATE INDEX IF NOT EXISTS idx_liberacoes_campo_codigo_documento ON public.liberacoes_revisoes_documentais_campo_obra (codigo_documento);
CREATE INDEX IF NOT EXISTS idx_liberacoes_campo_revisao_detectada ON public.liberacoes_revisoes_documentais_campo_obra (revisao_detectada);
CREATE INDEX IF NOT EXISTS idx_liberacoes_campo_decisao ON public.liberacoes_revisoes_documentais_campo_obra (decisao);
CREATE INDEX IF NOT EXISTS idx_liberacoes_campo_status ON public.liberacoes_revisoes_documentais_campo_obra (status_liberacao_resultante);
CREATE INDEX IF NOT EXISTS idx_liberacoes_campo_liberado ON public.liberacoes_revisoes_documentais_campo_obra (liberado_para_campo);
CREATE INDEX IF NOT EXISTS idx_liberacoes_campo_suspensa ON public.liberacoes_revisoes_documentais_campo_obra (liberacao_suspensa);
CREATE INDEX IF NOT EXISTS idx_liberacoes_campo_revogada ON public.liberacoes_revisoes_documentais_campo_obra (liberacao_revogada);
CREATE INDEX IF NOT EXISTS idx_liberacoes_campo_criado_em ON public.liberacoes_revisoes_documentais_campo_obra (criado_em);

ALTER TABLE public.revisoes_documentais_obra
    ADD COLUMN IF NOT EXISTS liberado_para_campo_por TEXT NULL,
    ADD COLUMN IF NOT EXISTS liberado_para_campo_em TIMESTAMPTZ NULL,
    ADD COLUMN IF NOT EXISTS liberacao_campo_status TEXT NULL,
    ADD COLUMN IF NOT EXISTS liberacao_campo_observacao TEXT NULL,
    ADD COLUMN IF NOT EXISTS liberacao_campo_instrucoes TEXT NULL,
    ADD COLUMN IF NOT EXISTS liberacao_campo_revogada_por TEXT NULL,
    ADD COLUMN IF NOT EXISTS liberacao_campo_revogada_em TIMESTAMPTZ NULL,
    ADD COLUMN IF NOT EXISTS motivo_revogacao_campo TEXT NULL,
    ADD COLUMN IF NOT EXISTS liberacao_campo_decisao_em TIMESTAMPTZ NULL;

COMMENT ON TABLE public.liberacoes_revisoes_documentais_campo_obra IS
'Trilha auditavel de liberacao documental para referencia em campo; nao autoriza execucao de servico.';
