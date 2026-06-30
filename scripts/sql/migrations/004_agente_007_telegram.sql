/*
===============================================================================
Construction Science Agents
Migration 004 — Agente 007 Telegram executivo
===============================================================================

Objetivos:
- registrar eventos recebidos pelo canal executivo Telegram;
- preservar payload bruto, payload normalizado, hash e idempotência;
- gerar comandos executivos auditáveis sem executar RPA, impressão ou PDF real;
- manter aprovação humana para ações sensíveis.

Esta migration não remove dados.
===============================================================================
*/

BEGIN;

-- ============================================================================
-- 1. Eventos recebidos pelo canal Telegram executivo
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.eventos_telegram (
    id                         BIGSERIAL PRIMARY KEY,
    tenant_id                  VARCHAR(100) NOT NULL DEFAULT 'construtora-piloto',
    obra_codigo                VARCHAR(50),
    canal                      VARCHAR(50) NOT NULL DEFAULT 'telegram',

    telegram_update_id         VARCHAR(100),
    telegram_message_id        VARCHAR(100),
    telegram_user_id           VARCHAR(100),
    telegram_username          VARCHAR(100),
    chat_id                    VARCHAR(100),
    chat_type                  VARCHAR(50),
    remetente_nome             TEXT,
    remetente_identificador    TEXT,

    usuario_autorizado         BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_autorizacao         TEXT,

    tipo_mensagem              VARCHAR(50) NOT NULL DEFAULT 'texto',
    conteudo                   TEXT,
    anexos                     JSONB NOT NULL DEFAULT '[]'::jsonb,

    payload_original           JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_normalizado        JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_hash               CHAR(64) NOT NULL,
    idempotency_key            VARCHAR(180) NOT NULL,
    correlation_id             UUID NOT NULL,

    intencao                   VARCHAR(100),
    confianca                  NUMERIC(5,4),
    agente_destino             VARCHAR(100),
    status_processamento       VARCHAR(40) NOT NULL DEFAULT 'RECEBIDO',
    mensagem_erro              TEXT,

    criado_em                  TIMESTAMP WITHOUT TIME ZONE
                               NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em              TIMESTAMP WITHOUT TIME ZONE
                               NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_eventos_telegram_idempotency_key
        UNIQUE (idempotency_key),

    CONSTRAINT chk_eventos_telegram_status
        CHECK (
            status_processamento IN (
                'RECEBIDO',
                'DUPLICADO',
                'CLASSIFICADO',
                'COMANDO_GERADO',
                'IGNORADO',
                'ERRO'
            )
        )
);

COMMENT ON TABLE public.eventos_telegram IS
'Eventos recebidos pelo canal executivo Telegram para o Agente 007.';

COMMENT ON COLUMN public.eventos_telegram.usuario_autorizado IS
'Indica se o usuário Telegram foi autorizado pela política local da API Core.';

COMMENT ON COLUMN public.eventos_telegram.motivo_autorizacao IS
'Motivo da autorização ou bloqueio aplicado ao usuário Telegram.';


-- ============================================================================
-- 2. Comandos executivos gerados pelo Agente 007
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.comandos_executivos (
    id                         BIGSERIAL PRIMARY KEY,
    id_comando                 UUID NOT NULL,

    evento_telegram_id         BIGINT REFERENCES public.eventos_telegram(id),
    tenant_id                  VARCHAR(100) NOT NULL DEFAULT 'construtora-piloto',
    obra_codigo                VARCHAR(50),
    correlation_id             UUID NOT NULL,

    agente_origem              VARCHAR(100) NOT NULL
                               DEFAULT 'AGENTE_007_ORQUESTRADOR_EXECUTIVO',
    agente_destino             VARCHAR(100),
    tipo_comando               VARCHAR(100) NOT NULL,
    payload_comando            JSONB NOT NULL DEFAULT '{}'::jsonb,
    justificativa              TEXT,

    status                     VARCHAR(40) NOT NULL DEFAULT 'PENDENTE',
    requer_aprovacao           BOOLEAN NOT NULL DEFAULT TRUE,
    aprovado_por               TEXT,
    aprovado_em                TIMESTAMP WITHOUT TIME ZONE,

    executado_por              TEXT,
    executado_em               TIMESTAMP WITHOUT TIME ZONE,
    resultado                  JSONB,
    evidencias                 JSONB NOT NULL DEFAULT '[]'::jsonb,
    mensagem_erro              TEXT,

    criado_em                  TIMESTAMP WITHOUT TIME ZONE
                               NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em              TIMESTAMP WITHOUT TIME ZONE
                               NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_comandos_executivos_id_comando
        UNIQUE (id_comando),

    CONSTRAINT chk_comandos_executivos_status
        CHECK (
            status IN (
                'PENDENTE',
                'AGUARDANDO_APROVACAO',
                'APROVADO',
                'REJEITADO',
                'EM_EXECUCAO',
                'CONCLUIDO',
                'ERRO',
                'CANCELADO'
            )
        )
);

COMMENT ON TABLE public.comandos_executivos IS
'Comandos auditáveis gerados pelo Agente 007. A execução externa é proibida nesta etapa.';

COMMENT ON COLUMN public.comandos_executivos.requer_aprovacao IS
'Quando verdadeiro, o comando deve iniciar em AGUARDANDO_APROVACAO.';


-- ============================================================================
-- 3. Índices auxiliares
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_eventos_telegram_correlation_id
    ON public.eventos_telegram (correlation_id);

CREATE INDEX IF NOT EXISTS idx_eventos_telegram_chat_id
    ON public.eventos_telegram (chat_id);

CREATE INDEX IF NOT EXISTS idx_eventos_telegram_user_id
    ON public.eventos_telegram (telegram_user_id);

CREATE INDEX IF NOT EXISTS idx_eventos_telegram_username
    ON public.eventos_telegram (telegram_username);

CREATE INDEX IF NOT EXISTS idx_eventos_telegram_status
    ON public.eventos_telegram (status_processamento);

CREATE INDEX IF NOT EXISTS idx_eventos_telegram_criado_em
    ON public.eventos_telegram (criado_em);

CREATE INDEX IF NOT EXISTS idx_comandos_executivos_evento
    ON public.comandos_executivos (evento_telegram_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_comandos_executivos_evento_telegram
    ON public.comandos_executivos (evento_telegram_id)
    WHERE evento_telegram_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_comandos_executivos_status
    ON public.comandos_executivos (status);

CREATE INDEX IF NOT EXISTS idx_comandos_executivos_correlation_id
    ON public.comandos_executivos (correlation_id);

CREATE INDEX IF NOT EXISTS idx_comandos_executivos_agente_destino
    ON public.comandos_executivos (agente_destino);

COMMIT;
