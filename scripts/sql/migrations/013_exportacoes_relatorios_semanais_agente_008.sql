-- Migration 013 - exportacao controlada do relatorio semanal executivo (MVP 0.7I)

CREATE TABLE IF NOT EXISTS public.exportacoes_relatorios_semanais_obra (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'construtora-piloto',
    obra_codigo TEXT NOT NULL,
    area TEXT NULL,
    relatorio_semanal_id BIGINT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    formato TEXT NOT NULL DEFAULT 'MARKDOWN',
    status TEXT NOT NULL DEFAULT 'GERADO',
    titulo TEXT NOT NULL,
    conteudo_markdown TEXT NOT NULL,
    resumo_executivo TEXT NULL,
    gerado_por TEXT NOT NULL DEFAULT 'AGENTE_008_GESTAO_OPERACIONAL_OBRA',
    aprovado_por TEXT NULL,
    aprovado_em TIMESTAMPTZ NULL,
    enviado_para_terceiros BOOLEAN NOT NULL DEFAULT false,
    alterou_rdo_oficial BOOLEAN NOT NULL DEFAULT false,
    alterou_cronograma BOOLEAN NOT NULL DEFAULT false,
    executou_rpa BOOLEAN NOT NULL DEFAULT false,
    sincronizou_openproject BOOLEAN NOT NULL DEFAULT false,
    gerou_pdf BOOLEAN NOT NULL DEFAULT false,
    gerou_link_publico BOOLEAN NOT NULL DEFAULT false,
    metadados JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_exportacoes_relatorios_semanais_obra_codigo
    ON public.exportacoes_relatorios_semanais_obra (obra_codigo);
CREATE INDEX IF NOT EXISTS idx_exportacoes_relatorios_semanais_area
    ON public.exportacoes_relatorios_semanais_obra (area);
CREATE INDEX IF NOT EXISTS idx_exportacoes_relatorios_semanais_relatorio_id
    ON public.exportacoes_relatorios_semanais_obra (relatorio_semanal_id);
CREATE INDEX IF NOT EXISTS idx_exportacoes_relatorios_semanais_data_inicio
    ON public.exportacoes_relatorios_semanais_obra (data_inicio);
CREATE INDEX IF NOT EXISTS idx_exportacoes_relatorios_semanais_data_fim
    ON public.exportacoes_relatorios_semanais_obra (data_fim);
CREATE INDEX IF NOT EXISTS idx_exportacoes_relatorios_semanais_formato
    ON public.exportacoes_relatorios_semanais_obra (formato);
CREATE INDEX IF NOT EXISTS idx_exportacoes_relatorios_semanais_status
    ON public.exportacoes_relatorios_semanais_obra (status);
CREATE INDEX IF NOT EXISTS idx_exportacoes_relatorios_semanais_criado_em
    ON public.exportacoes_relatorios_semanais_obra (criado_em);
