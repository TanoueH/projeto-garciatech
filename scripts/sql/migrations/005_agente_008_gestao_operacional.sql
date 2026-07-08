-- Migration 005 - AGENTE_008_GESTAO_OPERACIONAL_OBRA
-- Objetivo:
-- Criar o schema inicial para gestao operacional da obra,
-- incluindo areas, EAP, atividades de cronograma, dependencias,
-- restricoes e planos operacionais.
--
-- Regras:
-- - PostgreSQL continua sendo a fonte da verdade.
-- - OpenProject sera vitrine futura de Gantt, nao fonte primaria.
-- - Excel sera entrada/saida controlada, nao fonte oficial.
-- - Nenhuma acao executiva sensivel deve ocorrer sem aprovacao explicita.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- 1. Areas da obra
-- ============================================================

CREATE TABLE IF NOT EXISTS areas_obra (
    id BIGSERIAL PRIMARY KEY,
    id_area UUID NOT NULL DEFAULT gen_random_uuid(),
    obra_codigo TEXT NOT NULL,
    codigo_area TEXT NOT NULL,
    nome_area TEXT NOT NULL,
    tipo_area TEXT NOT NULL DEFAULT 'GERAL',
    descricao TEXT,
    ordem INTEGER NOT NULL DEFAULT 0,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    payload_original JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_areas_obra_codigo UNIQUE (obra_codigo, codigo_area),
    CONSTRAINT uq_areas_obra_uuid UNIQUE (id_area),
    CONSTRAINT chk_areas_obra_tipo CHECK (
        tipo_area IN (
            'GERAL',
            'PAVIMENTO',
            'SETOR',
            'AMBIENTE',
            'FRENTE_SERVICO',
            'AREA_EXTERNA',
            'OUTRO'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_areas_obra_obra_codigo
    ON areas_obra (obra_codigo);

CREATE INDEX IF NOT EXISTS idx_areas_obra_ativo
    ON areas_obra (obra_codigo, ativo);

COMMENT ON TABLE areas_obra IS
'Cadastro de areas, setores, pavimentos, ambientes ou frentes de servico da obra para uso do Agente 008.';

-- ============================================================
-- 2. EAP da obra
-- ============================================================

CREATE TABLE IF NOT EXISTS eap_obra (
    id BIGSERIAL PRIMARY KEY,
    id_eap UUID NOT NULL DEFAULT gen_random_uuid(),
    obra_codigo TEXT NOT NULL,
    codigo_eap TEXT NOT NULL,
    codigo_pai TEXT,
    nivel INTEGER NOT NULL DEFAULT 1,
    descricao TEXT NOT NULL,
    tipo_item TEXT NOT NULL DEFAULT 'PACOTE_TRABALHO',
    disciplina TEXT,
    unidade TEXT,
    ordem INTEGER NOT NULL DEFAULT 0,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    payload_original JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_eap_obra_codigo UNIQUE (obra_codigo, codigo_eap),
    CONSTRAINT uq_eap_obra_uuid UNIQUE (id_eap),
    CONSTRAINT chk_eap_obra_nivel CHECK (nivel >= 1),
    CONSTRAINT chk_eap_obra_tipo_item CHECK (
        tipo_item IN (
            'ETAPA',
            'PACOTE_TRABALHO',
            'ATIVIDADE',
            'MARCO',
            'DISCIPLINA',
            'OUTRO'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_eap_obra_obra_codigo
    ON eap_obra (obra_codigo);

CREATE INDEX IF NOT EXISTS idx_eap_obra_codigo_pai
    ON eap_obra (obra_codigo, codigo_pai);

CREATE INDEX IF NOT EXISTS idx_eap_obra_ativo
    ON eap_obra (obra_codigo, ativo);

COMMENT ON TABLE eap_obra IS
'Estrutura Analitica do Projeto da obra, usada pelo Agente 008 para organizar cronograma, custos, atividades e restricoes.';

-- ============================================================
-- 3. Atividades de cronograma
-- ============================================================

CREATE TABLE IF NOT EXISTS atividades_cronograma (
    id BIGSERIAL PRIMARY KEY,
    id_atividade UUID NOT NULL DEFAULT gen_random_uuid(),
    obra_codigo TEXT NOT NULL,
    codigo_atividade TEXT NOT NULL,
    codigo_eap TEXT,
    codigo_area TEXT,
    descricao TEXT NOT NULL,
    disciplina TEXT,
    frente_servico TEXT,
    unidade TEXT,
    quantidade_prevista NUMERIC(14, 3),
    data_inicio_planejada DATE,
    data_fim_planejada DATE,
    data_inicio_reprogramada DATE,
    data_fim_reprogramada DATE,
    data_inicio_real DATE,
    data_fim_real DATE,
    percentual_planejado NUMERIC(5, 2) NOT NULL DEFAULT 0,
    percentual_real NUMERIC(5, 2) NOT NULL DEFAULT 0,
    status_atividade TEXT NOT NULL DEFAULT 'NAO_INICIADA',
    responsavel TEXT,
    fonte_origem TEXT NOT NULL DEFAULT 'AGENTE_008',
    codigo_composicao_ref TEXT,
    fonte_composicao_ref TEXT,
    horizonte_planejamento TEXT NOT NULL DEFAULT 'BASELINE',
    criticidade TEXT NOT NULL DEFAULT 'MEDIA',
    restricoes_resumo JSONB NOT NULL DEFAULT '[]'::jsonb,
    payload_original JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_atividades_cronograma_codigo UNIQUE (obra_codigo, codigo_atividade),
    CONSTRAINT uq_atividades_cronograma_uuid UNIQUE (id_atividade),
    CONSTRAINT chk_atividades_cronograma_status CHECK (
        status_atividade IN (
            'NAO_INICIADA',
            'PROGRAMADA',
            'EM_EXECUCAO',
            'BLOQUEADA',
            'CONCLUIDA',
            'ATRASADA',
            'CANCELADA',
            'REPROGRAMADA'
        )
    ),
    CONSTRAINT chk_atividades_cronograma_horizonte CHECK (
        horizonte_planejamento IN (
            '0_15_DIAS',
            '15_30_DIAS',
            'MENSAL',
            'BASELINE',
            'OUTRO'
        )
    ),
    CONSTRAINT chk_atividades_cronograma_criticidade CHECK (
        criticidade IN ('BAIXA', 'MEDIA', 'ALTA', 'CRITICA')
    ),
    CONSTRAINT chk_atividades_cronograma_percentual_planejado CHECK (
        percentual_planejado >= 0 AND percentual_planejado <= 100
    ),
    CONSTRAINT chk_atividades_cronograma_percentual_real CHECK (
        percentual_real >= 0 AND percentual_real <= 100
    ),
    CONSTRAINT chk_atividades_cronograma_datas_planejadas CHECK (
        data_inicio_planejada IS NULL
        OR data_fim_planejada IS NULL
        OR data_inicio_planejada <= data_fim_planejada
    ),
    CONSTRAINT chk_atividades_cronograma_datas_reprogramadas CHECK (
        data_inicio_reprogramada IS NULL
        OR data_fim_reprogramada IS NULL
        OR data_inicio_reprogramada <= data_fim_reprogramada
    ),
    CONSTRAINT chk_atividades_cronograma_datas_reais CHECK (
        data_inicio_real IS NULL
        OR data_fim_real IS NULL
        OR data_inicio_real <= data_fim_real
    )
);

CREATE INDEX IF NOT EXISTS idx_atividades_cronograma_obra
    ON atividades_cronograma (obra_codigo);

CREATE INDEX IF NOT EXISTS idx_atividades_cronograma_eap
    ON atividades_cronograma (obra_codigo, codigo_eap);

CREATE INDEX IF NOT EXISTS idx_atividades_cronograma_area
    ON atividades_cronograma (obra_codigo, codigo_area);

CREATE INDEX IF NOT EXISTS idx_atividades_cronograma_status
    ON atividades_cronograma (obra_codigo, status_atividade);

CREATE INDEX IF NOT EXISTS idx_atividades_cronograma_horizonte
    ON atividades_cronograma (obra_codigo, horizonte_planejamento);

CREATE INDEX IF NOT EXISTS idx_atividades_cronograma_datas
    ON atividades_cronograma (obra_codigo, data_inicio_planejada, data_fim_planejada);

COMMENT ON TABLE atividades_cronograma IS
'Atividades operacionais e de cronograma controladas pelo Agente 008, com vinculo a EAP, area, horizonte de planejamento e status.';

-- ============================================================
-- 4. Dependencias entre atividades
-- ============================================================

CREATE TABLE IF NOT EXISTS dependencias_atividades (
    id BIGSERIAL PRIMARY KEY,
    id_dependencia UUID NOT NULL DEFAULT gen_random_uuid(),
    obra_codigo TEXT NOT NULL,
    atividade_predecessora_id BIGINT NOT NULL REFERENCES atividades_cronograma(id) ON DELETE CASCADE,
    atividade_sucessora_id BIGINT NOT NULL REFERENCES atividades_cronograma(id) ON DELETE CASCADE,
    tipo_dependencia TEXT NOT NULL DEFAULT 'FS',
    defasagem_dias INTEGER NOT NULL DEFAULT 0,
    obrigatoria BOOLEAN NOT NULL DEFAULT TRUE,
    observacoes TEXT,
    payload_original JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_dependencias_atividades_uuid UNIQUE (id_dependencia),
    CONSTRAINT uq_dependencias_atividades_relacao UNIQUE (
        obra_codigo,
        atividade_predecessora_id,
        atividade_sucessora_id,
        tipo_dependencia
    ),
    CONSTRAINT chk_dependencias_atividades_tipo CHECK (
        tipo_dependencia IN ('FS', 'SS', 'FF', 'SF')
    ),
    CONSTRAINT chk_dependencias_atividades_auto_relacao CHECK (
        atividade_predecessora_id <> atividade_sucessora_id
    )
);

CREATE INDEX IF NOT EXISTS idx_dependencias_atividades_obra
    ON dependencias_atividades (obra_codigo);

CREATE INDEX IF NOT EXISTS idx_dependencias_atividades_predecessora
    ON dependencias_atividades (atividade_predecessora_id);

CREATE INDEX IF NOT EXISTS idx_dependencias_atividades_sucessora
    ON dependencias_atividades (atividade_sucessora_id);

COMMENT ON TABLE dependencias_atividades IS
'Dependencias logicas entre atividades do cronograma para futura representacao em Gantt e analise de impacto.';

-- ============================================================
-- 5. Restricoes de atividade
-- ============================================================

CREATE TABLE IF NOT EXISTS restricoes_atividade (
    id BIGSERIAL PRIMARY KEY,
    id_restricao UUID NOT NULL DEFAULT gen_random_uuid(),
    obra_codigo TEXT NOT NULL,
    atividade_id BIGINT REFERENCES atividades_cronograma(id) ON DELETE SET NULL,
    tipo_restricao TEXT NOT NULL DEFAULT 'OUTROS',
    descricao TEXT NOT NULL,
    origem TEXT NOT NULL DEFAULT 'AGENTE_008',
    agente_origem TEXT,
    recurso_tipo TEXT,
    recurso_id TEXT,
    responsavel TEXT,
    prazo_liberacao DATE,
    status_restricao TEXT NOT NULL DEFAULT 'ABERTA',
    criticidade TEXT NOT NULL DEFAULT 'MEDIA',
    impacto_prazo_estimado INTEGER NOT NULL DEFAULT 0,
    impacto_custo_estimado NUMERIC(14, 2),
    evidencia JSONB NOT NULL DEFAULT '[]'::jsonb,
    payload_original JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_restricoes_atividade_uuid UNIQUE (id_restricao),
    CONSTRAINT chk_restricoes_atividade_tipo CHECK (
        tipo_restricao IN (
            'MATERIAL',
            'MAO_DE_OBRA',
            'EQUIPAMENTO',
            'PROJETO',
            'SEGURANCA',
            'DOCUMENTACAO',
            'FORNECEDOR',
            'CLIMA',
            'ACESSO',
            'CLIENTE',
            'NORMATIVA',
            'OUTROS'
        )
    ),
    CONSTRAINT chk_restricoes_atividade_status CHECK (
        status_restricao IN (
            'ABERTA',
            'EM_TRATAMENTO',
            'BLOQUEANTE',
            'LIBERADA',
            'CANCELADA'
        )
    ),
    CONSTRAINT chk_restricoes_atividade_criticidade CHECK (
        criticidade IN ('BAIXA', 'MEDIA', 'ALTA', 'CRITICA')
    )
);

CREATE INDEX IF NOT EXISTS idx_restricoes_atividade_obra
    ON restricoes_atividade (obra_codigo);

CREATE INDEX IF NOT EXISTS idx_restricoes_atividade_atividade
    ON restricoes_atividade (atividade_id);

CREATE INDEX IF NOT EXISTS idx_restricoes_atividade_status
    ON restricoes_atividade (obra_codigo, status_restricao);

CREATE INDEX IF NOT EXISTS idx_restricoes_atividade_criticidade
    ON restricoes_atividade (obra_codigo, criticidade);

COMMENT ON TABLE restricoes_atividade IS
'Restricoes operacionais que podem bloquear atividades do cronograma: materiais, fornecedores, projeto, seguranca, documentacao, clima e outras.';

-- ============================================================
-- 6. Planos operacionais
-- ============================================================

CREATE TABLE IF NOT EXISTS planos_operacionais_obra (
    id BIGSERIAL PRIMARY KEY,
    id_plano UUID NOT NULL DEFAULT gen_random_uuid(),
    obra_codigo TEXT NOT NULL,
    data_plano DATE NOT NULL DEFAULT CURRENT_DATE,
    horizonte TEXT NOT NULL DEFAULT '0_15_DIAS',
    tipo_plano TEXT NOT NULL DEFAULT 'PLANO_OPERACIONAL',
    resumo_executivo TEXT,
    atividades_prioritarias JSONB NOT NULL DEFAULT '[]'::jsonb,
    restricoes JSONB NOT NULL DEFAULT '[]'::jsonb,
    pendencias_criticas JSONB NOT NULL DEFAULT '[]'::jsonb,
    compras_necessarias JSONB NOT NULL DEFAULT '[]'::jsonb,
    riscos JSONB NOT NULL DEFAULT '[]'::jsonb,
    decisoes_requeridas JSONB NOT NULL DEFAULT '[]'::jsonb,
    acoes_recomendadas JSONB NOT NULL DEFAULT '[]'::jsonb,
    status_plano TEXT NOT NULL DEFAULT 'RASCUNHO',
    aprovado_por TEXT,
    aprovado_em TIMESTAMPTZ,
    origem TEXT NOT NULL DEFAULT 'AGENTE_008',
    payload_original JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_planos_operacionais_obra_uuid UNIQUE (id_plano),
    CONSTRAINT chk_planos_operacionais_obra_horizonte CHECK (
        horizonte IN (
            '0_15_DIAS',
            '15_30_DIAS',
            'MENSAL',
            'REUNIAO_OBRA',
            'OUTRO'
        )
    ),
    CONSTRAINT chk_planos_operacionais_obra_tipo CHECK (
        tipo_plano IN (
            'PLANO_OPERACIONAL',
            'PLANO_AMANHA',
            'LOOKAHEAD',
            'PROGRAMACAO_MENSAL',
            'REUNIAO_OBRA',
            'DIAGNOSTICO'
        )
    ),
    CONSTRAINT chk_planos_operacionais_obra_status CHECK (
        status_plano IN (
            'RASCUNHO',
            'AGUARDANDO_APROVACAO',
            'APROVADO',
            'REJEITADO',
            'CANCELADO',
            'ARQUIVADO'
        )
    ),
    CONSTRAINT chk_planos_operacionais_obra_aprovacao CHECK (
        (
            status_plano <> 'APROVADO'
        )
        OR (
            aprovado_por IS NOT NULL
            AND aprovado_em IS NOT NULL
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_planos_operacionais_obra_obra
    ON planos_operacionais_obra (obra_codigo);

CREATE INDEX IF NOT EXISTS idx_planos_operacionais_obra_data
    ON planos_operacionais_obra (obra_codigo, data_plano);

CREATE INDEX IF NOT EXISTS idx_planos_operacionais_obra_horizonte
    ON planos_operacionais_obra (obra_codigo, horizonte);

CREATE INDEX IF NOT EXISTS idx_planos_operacionais_obra_status
    ON planos_operacionais_obra (obra_codigo, status_plano);

COMMENT ON TABLE planos_operacionais_obra IS
'Planos, diagnosticos e programacoes gerados pelo Agente 008, sempre como rascunho ou proposta ate aprovacao explicita.';
