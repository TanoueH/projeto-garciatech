-- Migration 009 - registro e acompanhamento de ações operacionais (MVP 0.7C)

CREATE TABLE IF NOT EXISTS public.acoes_operacionais_obra (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'construtora-piloto',
    obra_codigo TEXT NOT NULL,
    area TEXT,
    disciplina TEXT,
    titulo TEXT NOT NULL,
    descricao TEXT,
    origem TEXT NOT NULL DEFAULT 'AGENTE_008_GESTAO_OPERACIONAL_OBRA',
    tipo_acao TEXT NOT NULL DEFAULT 'ACAO_OPERACIONAL',
    prioridade TEXT NOT NULL DEFAULT 'MEDIA',
    status TEXT NOT NULL DEFAULT 'ABERTA',
    responsavel TEXT,
    prazo DATE,
    referencia_documento_id BIGINT NULL,
    referencia_comando_id BIGINT NULL,
    metadados JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    concluido_em TIMESTAMPTZ NULL,
    CONSTRAINT chk_acoes_operacionais_obra_status
        CHECK (status IN ('ABERTA', 'EM_ANDAMENTO', 'CONCLUIDA', 'CANCELADA')),
    CONSTRAINT chk_acoes_operacionais_obra_prioridade
        CHECK (prioridade IN ('BAIXA', 'MEDIA', 'ALTA', 'CRITICA'))
);

CREATE INDEX IF NOT EXISTS idx_acoes_operacionais_obra_obra_codigo
    ON public.acoes_operacionais_obra (obra_codigo);
CREATE INDEX IF NOT EXISTS idx_acoes_operacionais_obra_area
    ON public.acoes_operacionais_obra (area);
CREATE INDEX IF NOT EXISTS idx_acoes_operacionais_obra_disciplina
    ON public.acoes_operacionais_obra (disciplina);
CREATE INDEX IF NOT EXISTS idx_acoes_operacionais_obra_status
    ON public.acoes_operacionais_obra (status);
CREATE INDEX IF NOT EXISTS idx_acoes_operacionais_obra_prioridade
    ON public.acoes_operacionais_obra (prioridade);
CREATE INDEX IF NOT EXISTS idx_acoes_operacionais_obra_prazo
    ON public.acoes_operacionais_obra (prazo);
CREATE INDEX IF NOT EXISTS idx_acoes_operacionais_obra_referencia_documento
    ON public.acoes_operacionais_obra (referencia_documento_id);
CREATE INDEX IF NOT EXISTS idx_acoes_operacionais_obra_referencia_comando
    ON public.acoes_operacionais_obra (referencia_comando_id);

CREATE OR REPLACE FUNCTION public.atualizar_acoes_operacionais_obra_atualizado_em()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.atualizado_em = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_acoes_operacionais_obra_atualizado_em
    ON public.acoes_operacionais_obra;
CREATE TRIGGER trg_acoes_operacionais_obra_atualizado_em
BEFORE UPDATE ON public.acoes_operacionais_obra
FOR EACH ROW
EXECUTE FUNCTION public.atualizar_acoes_operacionais_obra_atualizado_em();
