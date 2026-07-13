-- Migration 014 - PDF privado do relatorio semanal executivo (MVP 0.7J)

CREATE TABLE IF NOT EXISTS public.pdfs_relatorios_semanais_obra (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'construtora-piloto',
    obra_codigo TEXT NOT NULL,
    area TEXT NULL,
    exportacao_relatorio_id BIGINT NULL,
    relatorio_semanal_id BIGINT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    titulo TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'GERADO',
    nome_arquivo TEXT NOT NULL,
    caminho_local TEXT NULL,
    bucket TEXT NULL,
    object_key TEXT NULL,
    minio_uri TEXT NULL,
    tamanho_bytes BIGINT NULL,
    sha256 TEXT NULL,
    gerado_por TEXT NOT NULL DEFAULT 'AGENTE_008_GESTAO_OPERACIONAL_OBRA',
    aprovado_por TEXT NULL,
    aprovado_em TIMESTAMPTZ NULL,
    enviado_para_terceiros BOOLEAN NOT NULL DEFAULT false,
    gerou_link_publico BOOLEAN NOT NULL DEFAULT false,
    alterou_rdo_oficial BOOLEAN NOT NULL DEFAULT false,
    alterou_cronograma BOOLEAN NOT NULL DEFAULT false,
    executou_rpa BOOLEAN NOT NULL DEFAULT false,
    sincronizou_openproject BOOLEAN NOT NULL DEFAULT false,
    metadados JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pdfs_relatorios_semanais_obra_codigo
    ON public.pdfs_relatorios_semanais_obra (obra_codigo);
CREATE INDEX IF NOT EXISTS idx_pdfs_relatorios_semanais_area
    ON public.pdfs_relatorios_semanais_obra (area);
CREATE INDEX IF NOT EXISTS idx_pdfs_relatorios_semanais_exportacao_id
    ON public.pdfs_relatorios_semanais_obra (exportacao_relatorio_id);
CREATE INDEX IF NOT EXISTS idx_pdfs_relatorios_semanais_relatorio_id
    ON public.pdfs_relatorios_semanais_obra (relatorio_semanal_id);
CREATE INDEX IF NOT EXISTS idx_pdfs_relatorios_semanais_data_inicio
    ON public.pdfs_relatorios_semanais_obra (data_inicio);
CREATE INDEX IF NOT EXISTS idx_pdfs_relatorios_semanais_data_fim
    ON public.pdfs_relatorios_semanais_obra (data_fim);
CREATE INDEX IF NOT EXISTS idx_pdfs_relatorios_semanais_status
    ON public.pdfs_relatorios_semanais_obra (status);
CREATE INDEX IF NOT EXISTS idx_pdfs_relatorios_semanais_criado_em
    ON public.pdfs_relatorios_semanais_obra (criado_em);
