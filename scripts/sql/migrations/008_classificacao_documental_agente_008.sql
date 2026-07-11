-- Migration 008 - classificação documental técnica e controle de revisão (MVP 0.6I)

CREATE TABLE IF NOT EXISTS public.classificacoes_documentais_obra (
    id BIGSERIAL PRIMARY KEY,
    documento_id BIGINT NOT NULL REFERENCES public.documentos_minio_obra(id),
    obra_codigo TEXT NOT NULL,
    area_detectada TEXT,
    disciplina_detectada TEXT,
    status_revisao TEXT,
    data_revisao_detectada DATE,
    eh_obsoleto BOOLEAN NOT NULL DEFAULT false,
    eh_as_built BOOLEAN NOT NULL DEFAULT false,
    numero_revisao TEXT,
    palavras_chave JSONB NOT NULL DEFAULT '[]'::jsonb,
    criterios_detectados JSONB NOT NULL DEFAULT '{}'::jsonb,
    confianca_classificacao NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    metodo_classificacao TEXT NOT NULL DEFAULT 'REGRA_NOME_CAMINHO',
    status TEXT NOT NULL DEFAULT 'CLASSIFICADO',
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_classificacoes_documentais_obra_documento UNIQUE (documento_id)
);

CREATE INDEX IF NOT EXISTS idx_classificacoes_documentais_obra_obra_codigo
    ON public.classificacoes_documentais_obra (obra_codigo);
CREATE INDEX IF NOT EXISTS idx_classificacoes_documentais_obra_area_detectada
    ON public.classificacoes_documentais_obra (area_detectada);
CREATE INDEX IF NOT EXISTS idx_classificacoes_documentais_obra_disciplina_detectada
    ON public.classificacoes_documentais_obra (disciplina_detectada);
CREATE INDEX IF NOT EXISTS idx_classificacoes_documentais_obra_status_revisao
    ON public.classificacoes_documentais_obra (status_revisao);
CREATE INDEX IF NOT EXISTS idx_classificacoes_documentais_obra_eh_obsoleto
    ON public.classificacoes_documentais_obra (eh_obsoleto);
CREATE INDEX IF NOT EXISTS idx_classificacoes_documentais_obra_eh_as_built
    ON public.classificacoes_documentais_obra (eh_as_built);
CREATE INDEX IF NOT EXISTS idx_classificacoes_documentais_obra_data_revisao
    ON public.classificacoes_documentais_obra (data_revisao_detectada);
