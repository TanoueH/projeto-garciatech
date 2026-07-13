-- Migration 012 - relatorio semanal executivo consultivo (MVP 0.7H)

CREATE TABLE IF NOT EXISTS public.relatorios_semanais_executivos_obra (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'construtora-piloto',
    obra_codigo TEXT NOT NULL,
    area TEXT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    tipo_relatorio TEXT NOT NULL DEFAULT 'RELATORIO_SEMANAL_EXECUTIVO',
    status TEXT NOT NULL DEFAULT 'GERADO',
    payload_relatorio JSONB NOT NULL DEFAULT '{}'::jsonb,
    resposta_telegram TEXT NULL,
    origem TEXT NOT NULL DEFAULT 'AGENTE_008_GESTAO_OPERACIONAL_OBRA',
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_relatorios_semanais_executivos_obra_codigo
    ON public.relatorios_semanais_executivos_obra (obra_codigo);
CREATE INDEX IF NOT EXISTS idx_relatorios_semanais_executivos_area
    ON public.relatorios_semanais_executivos_obra (area);
CREATE INDEX IF NOT EXISTS idx_relatorios_semanais_executivos_data_inicio
    ON public.relatorios_semanais_executivos_obra (data_inicio);
CREATE INDEX IF NOT EXISTS idx_relatorios_semanais_executivos_data_fim
    ON public.relatorios_semanais_executivos_obra (data_fim);
CREATE INDEX IF NOT EXISTS idx_relatorios_semanais_executivos_tipo_relatorio
    ON public.relatorios_semanais_executivos_obra (tipo_relatorio);
CREATE INDEX IF NOT EXISTS idx_relatorios_semanais_executivos_criado_em
    ON public.relatorios_semanais_executivos_obra (criado_em);
