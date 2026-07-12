-- Migration 011 - envios automaticos do briefing executivo diario (MVP 0.7G)

CREATE TABLE IF NOT EXISTS public.envios_briefing_diario_obra (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'construtora-piloto',
    obra_codigo TEXT NOT NULL,
    area TEXT NULL,
    data_briefing DATE NOT NULL,
    tipo_briefing TEXT NOT NULL DEFAULT 'BRIEFING_EXECUTIVO_DIARIO',
    canal TEXT NOT NULL DEFAULT 'TELEGRAM',
    chat_id TEXT NULL,
    status TEXT NOT NULL DEFAULT 'PENDENTE',
    telegram_message_id TEXT NULL,
    payload_briefing JSONB NOT NULL DEFAULT '{}'::jsonb,
    resposta_telegram TEXT NULL,
    mensagem_erro TEXT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    enviado_em TIMESTAMPTZ NULL,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_envios_briefing_diario_obra_dia
    ON public.envios_briefing_diario_obra (
        obra_codigo, (COALESCE(area, '')), data_briefing, tipo_briefing, canal
    );
CREATE INDEX IF NOT EXISTS idx_envios_briefing_diario_obra_codigo
    ON public.envios_briefing_diario_obra (obra_codigo);
CREATE INDEX IF NOT EXISTS idx_envios_briefing_diario_data
    ON public.envios_briefing_diario_obra (data_briefing);
CREATE INDEX IF NOT EXISTS idx_envios_briefing_diario_status
    ON public.envios_briefing_diario_obra (status);
CREATE INDEX IF NOT EXISTS idx_envios_briefing_diario_criado_em
    ON public.envios_briefing_diario_obra (criado_em);
