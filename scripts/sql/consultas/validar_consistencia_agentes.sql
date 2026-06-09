/*
===============================================================================
Projeto Garcia
Consulta de auditoria e consistência dos agentes
===============================================================================

Objetivo:
- identificar registros inconsistentes;
- localizar dados incompletos;
- detectar possíveis duplicidades;
- não executar UPDATE ou DELETE.

Este script é somente leitura.
===============================================================================
*/

-- ============================================================================
-- 1. Resumo das tabelas principais
-- ============================================================================

SELECT
    'documentos_obra' AS tabela,
    COUNT(*) AS total_registros
FROM public.documentos_obra

UNION ALL

SELECT
    'rdo_obra',
    COUNT(*)
FROM public.rdo_obra

UNION ALL

SELECT
    'pendencias_obra',
    COUNT(*)
FROM public.pendencias_obra;


-- ============================================================================
-- 2. Documentos com código de obra inválido
-- ============================================================================

SELECT
    id,
    obra_codigo,
    tipo_documento,
    status,
    criado_em
FROM public.documentos_obra
WHERE
    obra_codigo IS NULL
    OR BTRIM(obra_codigo) = ''
    OR obra_codigo LIKE '=%'
ORDER BY criado_em DESC;


-- ============================================================================
-- 3. Documentos incompletos sem pendência registrada
-- ============================================================================

SELECT
    id,
    obra_codigo,
    tipo_documento,
    status,
    possui_pendencias,
    criado_em
FROM public.documentos_obra
WHERE
    status = 'INCOMPLETO'
    AND COALESCE(possui_pendencias, FALSE) = FALSE
ORDER BY criado_em DESC;


-- ============================================================================
-- 4. RDO com status incompatível com o campo possui_pendencias
-- ============================================================================

SELECT
    id,
    obra_codigo,
    data_rdo,
    status_rdo,
    possui_pendencias,
    pendencias,
    ocorrencias,
    criado_em
FROM public.rdo_obra
WHERE
       (
           status_rdo = 'MINUTA_GERADA'
           AND possui_pendencias IS TRUE
       )
    OR (
           status_rdo = 'PENDENTE_REVISAO'
           AND COALESCE(possui_pendencias, FALSE) = FALSE
       )
ORDER BY criado_em DESC;


-- ============================================================================
-- 5. RDO pendente sem conteúdo em pendencias ou ocorrencias
-- ============================================================================

SELECT
    id,
    obra_codigo,
    data_rdo,
    status_rdo,
    possui_pendencias,
    pendencias,
    ocorrencias,
    criado_em
FROM public.rdo_obra
WHERE
    possui_pendencias IS TRUE
    AND COALESCE(
        jsonb_array_length(COALESCE(pendencias -> 'itens', '[]'::jsonb)),
        0
    ) = 0
    AND COALESCE(
        jsonb_array_length(COALESCE(ocorrencias -> 'itens', '[]'::jsonb)),
        0
    ) = 0
ORDER BY criado_em DESC;


-- ============================================================================
-- 6. RDO sem campos essenciais
-- ============================================================================

SELECT
    id,
    obra_codigo,
    data_rdo,
    responsavel,
    status_rdo,
    criado_em
FROM public.rdo_obra
WHERE
    obra_codigo IS NULL
    OR BTRIM(obra_codigo) = ''
    OR data_rdo IS NULL
    OR status_rdo IS NULL
ORDER BY criado_em DESC;


-- ============================================================================
-- 7. Pendências sem descrição
-- ============================================================================

SELECT
    id,
    obra_codigo,
    origem,
    origem_tipo,
    categoria,
    prioridade,
    status_pendencia,
    criado_em
FROM public.pendencias_obra
WHERE
    descricao IS NULL
    OR BTRIM(descricao) = ''
ORDER BY criado_em DESC;


-- ============================================================================
-- 8. Pendências com classificação incompleta
-- ============================================================================

SELECT
    id,
    obra_codigo,
    descricao,
    categoria,
    prioridade,
    status_pendencia,
    criado_em
FROM public.pendencias_obra
WHERE
    categoria IS NULL
    OR BTRIM(categoria) = ''
    OR prioridade IS NULL
    OR BTRIM(prioridade) = ''
    OR status_pendencia IS NULL
    OR BTRIM(status_pendencia) = ''
ORDER BY criado_em DESC;


-- ============================================================================
-- 9. Possíveis RDO duplicados
-- Ainda não substitui a idempotência formal.
-- ============================================================================

SELECT
    obra_codigo,
    data_rdo,
    responsavel,
    status_rdo,
    COUNT(*) AS quantidade,
    ARRAY_AGG(id ORDER BY id) AS ids
FROM public.rdo_obra
GROUP BY
    obra_codigo,
    data_rdo,
    responsavel,
    status_rdo
HAVING COUNT(*) > 1
ORDER BY quantidade DESC, data_rdo DESC;


-- ============================================================================
-- 10. Possíveis pendências duplicadas
-- ============================================================================

SELECT
    obra_codigo,
    origem,
    origem_tipo,
    descricao,
    categoria,
    prioridade,
    COUNT(*) AS quantidade,
    ARRAY_AGG(id ORDER BY id) AS ids
FROM public.pendencias_obra
GROUP BY
    obra_codigo,
    origem,
    origem_tipo,
    descricao,
    categoria,
    prioridade
HAVING COUNT(*) > 1
ORDER BY quantidade DESC;


-- ============================================================================
-- 11. Registros mais recentes para inspeção conjunta
-- ============================================================================

SELECT
    'DOCUMENTO' AS entidade,
    id,
    obra_codigo,
    tipo_documento AS tipo,
    status,
    criado_em
FROM public.documentos_obra

UNION ALL

SELECT
    'RDO',
    id,
    obra_codigo,
    status_rdo,
    CASE
        WHEN possui_pendencias THEN 'COM_PENDENCIA'
        ELSE 'SEM_PENDENCIA'
    END,
    criado_em
FROM public.rdo_obra

UNION ALL

SELECT
    'PENDENCIA',
    id,
    obra_codigo,
    categoria,
    status_pendencia,
    criado_em
FROM public.pendencias_obra

ORDER BY criado_em DESC
LIMIT 30;