-- Migration 007 - análise documental assistida pelo Agente 008 (MVP 0.6H)

CREATE TABLE IF NOT EXISTS public.analises_documentais_obra (
    id BIGSERIAL PRIMARY KEY,
    documento_id BIGINT NOT NULL REFERENCES public.documentos_minio_obra(id),
    obra_codigo TEXT NOT NULL,
    tipo_analise TEXT NOT NULL DEFAULT 'ANALISE_PRELIMINAR',
    status TEXT NOT NULL DEFAULT 'CONCLUIDA',
    resumo TEXT,
    observacoes JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadados_extraidos JSONB NOT NULL DEFAULT '{}'::jsonb,
    resposta_telegram TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_analises_documentais_obra_documento_id
    ON public.analises_documentais_obra (documento_id);

CREATE INDEX IF NOT EXISTS idx_analises_documentais_obra_obra_codigo
    ON public.analises_documentais_obra (obra_codigo);

