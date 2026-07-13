-- Migration 015 - Aprovacao executiva do PDF do relatorio semanal (MVP 0.7K)

CREATE TABLE IF NOT EXISTS public.aprovacoes_relatorios_semanais_obra (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'construtora-piloto',
    obra_codigo TEXT NOT NULL,
    area TEXT NULL,
    pdf_relatorio_id BIGINT NOT NULL,
    exportacao_relatorio_id BIGINT NULL,
    relatorio_semanal_id BIGINT NULL,
    decisao TEXT NOT NULL,
    status_resultante TEXT NOT NULL,
    aprovado BOOLEAN NOT NULL DEFAULT false,
    rejeitado BOOLEAN NOT NULL DEFAULT false,
    ajustes_solicitados BOOLEAN NOT NULL DEFAULT false,
    motivo TEXT NULL,
    observacao TEXT NULL,
    decisor_nome TEXT NULL,
    decisor_telegram_user_id TEXT NULL,
    decisor_telegram_username TEXT NULL,
    decisor_chat_id TEXT NULL,
    canal TEXT NOT NULL DEFAULT 'telegram',
    origem TEXT NOT NULL DEFAULT 'AGENTE_007_ORQUESTRADOR_EXECUTIVO',
    enviado_para_terceiros BOOLEAN NOT NULL DEFAULT false,
    gerou_link_publico BOOLEAN NOT NULL DEFAULT false,
    alterou_rdo_oficial BOOLEAN NOT NULL DEFAULT false,
    alterou_cronograma BOOLEAN NOT NULL DEFAULT false,
    executou_rpa BOOLEAN NOT NULL DEFAULT false,
    sincronizou_openproject BOOLEAN NOT NULL DEFAULT false,
    alterou_minio BOOLEAN NOT NULL DEFAULT false,
    metadados JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_aprovacoes_relatorios_semanais_obra_codigo
    ON public.aprovacoes_relatorios_semanais_obra (obra_codigo);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_relatorios_semanais_area
    ON public.aprovacoes_relatorios_semanais_obra (area);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_relatorios_semanais_pdf_id
    ON public.aprovacoes_relatorios_semanais_obra (pdf_relatorio_id);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_relatorios_semanais_decisao
    ON public.aprovacoes_relatorios_semanais_obra (decisao);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_relatorios_semanais_status
    ON public.aprovacoes_relatorios_semanais_obra (status_resultante);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_relatorios_semanais_aprovado
    ON public.aprovacoes_relatorios_semanais_obra (aprovado);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_relatorios_semanais_rejeitado
    ON public.aprovacoes_relatorios_semanais_obra (rejeitado);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_relatorios_semanais_ajustes
    ON public.aprovacoes_relatorios_semanais_obra (ajustes_solicitados);
CREATE INDEX IF NOT EXISTS idx_aprovacoes_relatorios_semanais_criado_em
    ON public.aprovacoes_relatorios_semanais_obra (criado_em);

ALTER TABLE public.pdfs_relatorios_semanais_obra
    ADD COLUMN IF NOT EXISTS rejeitado_por TEXT NULL,
    ADD COLUMN IF NOT EXISTS rejeitado_em TIMESTAMPTZ NULL,
    ADD COLUMN IF NOT EXISTS ajustes_solicitados_por TEXT NULL,
    ADD COLUMN IF NOT EXISTS ajustes_solicitados_em TIMESTAMPTZ NULL,
    ADD COLUMN IF NOT EXISTS motivo_decisao TEXT NULL,
    ADD COLUMN IF NOT EXISTS observacao_decisao TEXT NULL;
