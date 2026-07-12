-- Migration 010 - governanca e historico de acoes operacionais (MVP 0.7E)

CREATE TABLE IF NOT EXISTS public.historico_acoes_operacionais_obra (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'construtora-piloto',
    obra_codigo TEXT NOT NULL,
    acao_id BIGINT NOT NULL,
    tipo_evento TEXT NOT NULL,
    status_anterior TEXT NULL,
    status_novo TEXT NULL,
    prioridade_anterior TEXT NULL,
    prioridade_nova TEXT NULL,
    responsavel_anterior TEXT NULL,
    responsavel_novo TEXT NULL,
    prazo_anterior DATE NULL,
    prazo_novo DATE NULL,
    observacao TEXT NULL,
    origem TEXT NOT NULL DEFAULT 'AGENTE_008_GESTAO_OPERACIONAL_OBRA',
    registrado_por TEXT NULL,
    metadados JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_historico_acoes_operacionais_obra_codigo
    ON public.historico_acoes_operacionais_obra (obra_codigo);
CREATE INDEX IF NOT EXISTS idx_historico_acoes_operacionais_acao_id
    ON public.historico_acoes_operacionais_obra (acao_id);
CREATE INDEX IF NOT EXISTS idx_historico_acoes_operacionais_tipo_evento
    ON public.historico_acoes_operacionais_obra (tipo_evento);
CREATE INDEX IF NOT EXISTS idx_historico_acoes_operacionais_criado_em
    ON public.historico_acoes_operacionais_obra (criado_em);
