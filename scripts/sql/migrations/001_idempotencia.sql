/*
===============================================================================
Projeto Garcia
Migration 001 — Idempotência e rastreabilidade entre agentes
===============================================================================

Objetivos:
- impedir o processamento repetido do mesmo evento;
- impedir documentos, RDOs e pendências duplicados;
- permitir rastreamento ponta a ponta com correlation_id;
- preservar os identificadores técnicos já existentes.

Esta migration não remove dados.
===============================================================================
*/

BEGIN;

-- ============================================================================
-- 1. Tabela central de eventos processados
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.eventos_processados (
    id                  BIGSERIAL PRIMARY KEY,
    idempotency_key     VARCHAR(128) NOT NULL,
    correlation_id      UUID,
    agente              VARCHAR(100) NOT NULL,
    origem              VARCHAR(100),
    obra_codigo         VARCHAR(50),
    status              VARCHAR(30) NOT NULL DEFAULT 'PROCESSANDO',
    recurso_tipo        VARCHAR(100),
    recurso_id          VARCHAR(100),
    payload_hash        CHAR(64),
    mensagem_erro       TEXT,
    criado_em           TIMESTAMP WITHOUT TIME ZONE
                         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em       TIMESTAMP WITHOUT TIME ZONE
                         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    concluido_em        TIMESTAMP WITHOUT TIME ZONE,

    CONSTRAINT uq_eventos_processados_idempotency_key
        UNIQUE (idempotency_key)
);

COMMENT ON TABLE public.eventos_processados IS
'Controle central de idempotência dos eventos processados pelos agentes.';

COMMENT ON COLUMN public.eventos_processados.idempotency_key IS
'Chave determinística que identifica unicamente um evento ou conteúdo.';

COMMENT ON COLUMN public.eventos_processados.correlation_id IS
'Identificador para rastrear a execução entre os agentes 00, 01, 02 e 03.';

COMMENT ON COLUMN public.eventos_processados.payload_hash IS
'Hash SHA-256 do payload normalizado ou conteúdo do documento.';


-- ============================================================================
-- 2. Índices auxiliares da tabela central
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_eventos_processados_correlation_id
    ON public.eventos_processados (correlation_id);

CREATE INDEX IF NOT EXISTS idx_eventos_processados_agente
    ON public.eventos_processados (agente);

CREATE INDEX IF NOT EXISTS idx_eventos_processados_obra
    ON public.eventos_processados (obra_codigo);

CREATE INDEX IF NOT EXISTS idx_eventos_processados_status
    ON public.eventos_processados (status);

CREATE INDEX IF NOT EXISTS idx_eventos_processados_criado_em
    ON public.eventos_processados (criado_em);


-- ============================================================================
-- 3. Colunas de idempotência em documentos_obra
-- ============================================================================

ALTER TABLE public.documentos_obra
    ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128);

ALTER TABLE public.documentos_obra
    ADD COLUMN IF NOT EXISTS correlation_id UUID;

ALTER TABLE public.documentos_obra
    ADD COLUMN IF NOT EXISTS payload_hash CHAR(64);

CREATE UNIQUE INDEX IF NOT EXISTS uq_documentos_obra_idempotency_key
    ON public.documentos_obra (idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_documentos_obra_correlation_id
    ON public.documentos_obra (correlation_id);

CREATE INDEX IF NOT EXISTS idx_documentos_obra_payload_hash
    ON public.documentos_obra (payload_hash);


-- ============================================================================
-- 4. Colunas de idempotência em rdo_obra
-- ============================================================================

ALTER TABLE public.rdo_obra
    ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128);

ALTER TABLE public.rdo_obra
    ADD COLUMN IF NOT EXISTS correlation_id UUID;

ALTER TABLE public.rdo_obra
    ADD COLUMN IF NOT EXISTS evento_origem_id VARCHAR(128);

CREATE UNIQUE INDEX IF NOT EXISTS uq_rdo_obra_idempotency_key
    ON public.rdo_obra (idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_rdo_obra_correlation_id
    ON public.rdo_obra (correlation_id);

CREATE INDEX IF NOT EXISTS idx_rdo_obra_evento_origem
    ON public.rdo_obra (evento_origem_id);


-- ============================================================================
-- 5. Colunas de idempotência em pendencias_obra
-- ============================================================================

ALTER TABLE public.pendencias_obra
    ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128);

ALTER TABLE public.pendencias_obra
    ADD COLUMN IF NOT EXISTS correlation_id UUID;

CREATE UNIQUE INDEX IF NOT EXISTS uq_pendencias_obra_idempotency_key
    ON public.pendencias_obra (idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_pendencias_obra_correlation_id
    ON public.pendencias_obra (correlation_id);


-- ============================================================================
-- 6. Restrição de consistência do RDO
-- ============================================================================

ALTER TABLE public.rdo_obra
    DROP CONSTRAINT IF EXISTS chk_rdo_status_pendencias;

ALTER TABLE public.rdo_obra
    ADD CONSTRAINT chk_rdo_status_pendencias
    CHECK (
        NOT (
            status_rdo = 'MINUTA_GERADA'
            AND possui_pendencias IS TRUE
        )
    );


-- ============================================================================
-- 7. Restrições de status da tabela de eventos
-- ============================================================================

ALTER TABLE public.eventos_processados
    DROP CONSTRAINT IF EXISTS chk_eventos_processados_status;

ALTER TABLE public.eventos_processados
    ADD CONSTRAINT chk_eventos_processados_status
    CHECK (
        status IN (
            'PROCESSANDO',
            'CONCLUIDO',
            'ERRO',
            'DUPLICADO',
            'IGNORADO'
        )
    );

COMMIT;