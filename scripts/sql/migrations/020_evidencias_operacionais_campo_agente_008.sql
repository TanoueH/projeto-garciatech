-- Migration 020 - MVP 0.8E: evidencias operacionais recebidas do campo.

CREATE TABLE IF NOT EXISTS public.evidencias_operacionais_obra (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'construtora-piloto',
    obra_codigo TEXT NOT NULL,
    origem TEXT NOT NULL DEFAULT 'WHATSAPP',
    canal_origem TEXT NOT NULL DEFAULT 'whatsapp',
    remetente_nome TEXT NULL,
    remetente_identificador TEXT NULL,
    remetente_autorizado BOOLEAN NOT NULL DEFAULT FALSE,
    chat_id TEXT NULL,
    message_id TEXT NULL,
    provider_message_id TEXT NULL,
    thread_id TEXT NULL,
    tipo_evidencia TEXT NOT NULL,
    subtipo_evidencia TEXT NULL,
    texto_original TEXT NULL,
    legenda TEXT NULL,
    descricao_curta TEXT NULL,
    area TEXT NULL,
    disciplina TEXT NULL,
    frente_trabalho TEXT NULL,
    categoria_operacional TEXT NULL,
    data_evento TIMESTAMPTZ NULL,
    data_recebimento TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    bucket TEXT NULL,
    object_key TEXT NULL,
    minio_uri TEXT NULL,
    nome_arquivo_original TEXT NULL,
    nome_arquivo_armazenado TEXT NULL,
    mime_type TEXT NULL,
    extensao TEXT NULL,
    tamanho_bytes BIGINT NULL,
    sha256 TEXT NULL,
    largura_px INTEGER NULL,
    altura_px INTEGER NULL,
    latitude NUMERIC NULL,
    longitude NUMERIC NULL,
    status_triagem TEXT NOT NULL DEFAULT 'RECEBIDA_AGUARDANDO_TRIAGEM',
    status_vinculacao TEXT NOT NULL DEFAULT 'NAO_VINCULADA',
    prioridade_sugerida TEXT NULL,
    confianca_classificacao NUMERIC NULL,
    observacao TEXT NULL,
    vinculo_rdo_id BIGINT NULL,
    vinculo_pendencia_id BIGINT NULL,
    vinculo_acao_operacional_id BIGINT NULL,
    vinculo_revisao_documental_id BIGINT NULL,
    incluivel_relatorio_semanal BOOLEAN NOT NULL DEFAULT FALSE,
    incluido_relatorio_semanal BOOLEAN NOT NULL DEFAULT FALSE,
    relatorio_semanal_id BIGINT NULL,
    recebido_por TEXT NOT NULL DEFAULT 'AGENTE_008_GESTAO_OPERACIONAL_OBRA',
    enviado_para_terceiros BOOLEAN NOT NULL DEFAULT FALSE,
    gerou_link_publico BOOLEAN NOT NULL DEFAULT FALSE,
    alterou_rdo_oficial BOOLEAN NOT NULL DEFAULT FALSE,
    alterou_cronograma BOOLEAN NOT NULL DEFAULT FALSE,
    criou_pendencia_automaticamente BOOLEAN NOT NULL DEFAULT FALSE,
    criou_acao_automaticamente BOOLEAN NOT NULL DEFAULT FALSE,
    executou_rpa BOOLEAN NOT NULL DEFAULT FALSE,
    sincronizou_openproject BOOLEAN NOT NULL DEFAULT FALSE,
    alterou_minio BOOLEAN NOT NULL DEFAULT FALSE,
    metadados JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_obra_codigo ON public.evidencias_operacionais_obra (obra_codigo);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_origem ON public.evidencias_operacionais_obra (origem);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_canal_origem ON public.evidencias_operacionais_obra (canal_origem);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_remetente ON public.evidencias_operacionais_obra (remetente_identificador);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_chat_id ON public.evidencias_operacionais_obra (chat_id);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_message_id ON public.evidencias_operacionais_obra (message_id);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_provider_message_id ON public.evidencias_operacionais_obra (provider_message_id);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_tipo ON public.evidencias_operacionais_obra (tipo_evidencia);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_area ON public.evidencias_operacionais_obra (area);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_disciplina ON public.evidencias_operacionais_obra (disciplina);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_frente ON public.evidencias_operacionais_obra (frente_trabalho);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_categoria ON public.evidencias_operacionais_obra (categoria_operacional);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_status_triagem ON public.evidencias_operacionais_obra (status_triagem);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_status_vinculacao ON public.evidencias_operacionais_obra (status_vinculacao);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_data_recebimento ON public.evidencias_operacionais_obra (data_recebimento);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_criado_em ON public.evidencias_operacionais_obra (criado_em);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_sha256 ON public.evidencias_operacionais_obra (sha256);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_bucket ON public.evidencias_operacionais_obra (bucket);
CREATE INDEX IF NOT EXISTS idx_evidencias_operacionais_object_key ON public.evidencias_operacionais_obra (object_key);
CREATE UNIQUE INDEX IF NOT EXISTS uq_evidencias_operacionais_provider
    ON public.evidencias_operacionais_obra (obra_codigo, canal_origem, provider_message_id)
    WHERE provider_message_id IS NOT NULL;

COMMENT ON TABLE public.evidencias_operacionais_obra IS
'Metadados auditaveis de evidencias operacionais; nao constituem RDO nem disparam acoes automaticas.';
