-- Migration 017 - MVP 0.8A: controle de revisoes documentais de projetos.

CREATE TABLE IF NOT EXISTS public.revisoes_documentais_obra (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'construtora-piloto',
    obra_codigo TEXT NOT NULL,
    documento_minio_id BIGINT NULL,
    documento_substituido_id BIGINT NULL,
    revisao_anterior_id BIGINT NULL,
    bucket TEXT NULL,
    object_key TEXT NULL,
    minio_uri TEXT NULL,
    nome_arquivo_original TEXT NOT NULL,
    caminho_origem TEXT NULL,
    disciplina TEXT NULL,
    area TEXT NULL,
    codigo_documento TEXT NULL,
    titulo_documento TEXT NULL,
    revisao_detectada TEXT NULL,
    data_documento DATE NULL,
    tipo_documento TEXT NULL,
    status_revisao TEXT NOT NULL DEFAULT 'RECEBIDO_PARA_ANALISE',
    status_vigencia TEXT NOT NULL DEFAULT 'NAO_VIGENTE',
    liberado_para_campo BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_alteracao TEXT NULL,
    observacao TEXT NULL,
    responsavel_upload TEXT NULL,
    responsavel_analise TEXT NULL,
    aprovado_por TEXT NULL,
    aprovado_em TIMESTAMPTZ NULL,
    rejeitado_por TEXT NULL,
    rejeitado_em TIMESTAMPTZ NULL,
    motivo_rejeicao TEXT NULL,
    criado_por TEXT NOT NULL DEFAULT 'AGENTE_008_GESTAO_OPERACIONAL_OBRA',
    origem TEXT NOT NULL DEFAULT 'MINIO',
    enviado_para_terceiros BOOLEAN NOT NULL DEFAULT FALSE,
    gerou_link_publico BOOLEAN NOT NULL DEFAULT FALSE,
    alterou_rdo_oficial BOOLEAN NOT NULL DEFAULT FALSE,
    alterou_cronograma BOOLEAN NOT NULL DEFAULT FALSE,
    executou_rpa BOOLEAN NOT NULL DEFAULT FALSE,
    sincronizou_openproject BOOLEAN NOT NULL DEFAULT FALSE,
    liberou_execucao_campo BOOLEAN NOT NULL DEFAULT FALSE,
    metadados JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_revisoes_documentais_status_revisao CHECK (status_revisao IN (
        'RECEBIDO_PARA_ANALISE', 'EM_ANALISE_TECNICA', 'APROVADO_COMO_VIGENTE',
        'REJEITADO', 'SUBSTITUIDO', 'OBSOLETO', 'AS_BUILT'
    )),
    CONSTRAINT chk_revisoes_documentais_status_vigencia CHECK (status_vigencia IN (
        'NAO_VIGENTE', 'VIGENTE', 'SUBSTITUIDO', 'OBSOLETO', 'HISTORICO'
    )),
    CONSTRAINT fk_revisoes_documentais_anterior FOREIGN KEY (revisao_anterior_id)
        REFERENCES public.revisoes_documentais_obra (id)
);

CREATE INDEX IF NOT EXISTS idx_revisoes_documentais_obra_codigo ON public.revisoes_documentais_obra (obra_codigo);
CREATE INDEX IF NOT EXISTS idx_revisoes_documentais_documento_minio_id ON public.revisoes_documentais_obra (documento_minio_id);
CREATE INDEX IF NOT EXISTS idx_revisoes_documentais_documento_substituido_id ON public.revisoes_documentais_obra (documento_substituido_id);
CREATE INDEX IF NOT EXISTS idx_revisoes_documentais_revisao_anterior_id ON public.revisoes_documentais_obra (revisao_anterior_id);
CREATE INDEX IF NOT EXISTS idx_revisoes_documentais_disciplina ON public.revisoes_documentais_obra (disciplina);
CREATE INDEX IF NOT EXISTS idx_revisoes_documentais_area ON public.revisoes_documentais_obra (area);
CREATE INDEX IF NOT EXISTS idx_revisoes_documentais_codigo_documento ON public.revisoes_documentais_obra (codigo_documento);
CREATE INDEX IF NOT EXISTS idx_revisoes_documentais_revisao_detectada ON public.revisoes_documentais_obra (revisao_detectada);
CREATE INDEX IF NOT EXISTS idx_revisoes_documentais_status_revisao ON public.revisoes_documentais_obra (status_revisao);
CREATE INDEX IF NOT EXISTS idx_revisoes_documentais_status_vigencia ON public.revisoes_documentais_obra (status_vigencia);
CREATE INDEX IF NOT EXISTS idx_revisoes_documentais_liberado_campo ON public.revisoes_documentais_obra (liberado_para_campo);
CREATE INDEX IF NOT EXISTS idx_revisoes_documentais_criado_em ON public.revisoes_documentais_obra (criado_em);
CREATE UNIQUE INDEX IF NOT EXISTS uq_revisoes_documentais_objeto_minio
    ON public.revisoes_documentais_obra (obra_codigo, bucket, object_key)
    WHERE bucket IS NOT NULL AND object_key IS NOT NULL;

COMMENT ON TABLE public.revisoes_documentais_obra IS
'Registro auditavel de novas revisoes; recebimento nao implica vigencia nem liberacao para campo.';
