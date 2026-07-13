-- Validacao nao destrutiva do MVP 0.7K.

SELECT
    id,
    obra_codigo,
    area,
    pdf_relatorio_id,
    decisao,
    status_resultante,
    aprovado,
    rejeitado,
    ajustes_solicitados,
    motivo,
    observacao,
    decisor_nome,
    decisor_telegram_user_id,
    decisor_telegram_username,
    decisor_chat_id,
    enviado_para_terceiros,
    gerou_link_publico,
    alterou_rdo_oficial,
    alterou_cronograma,
    executou_rpa,
    sincronizou_openproject,
    alterou_minio,
    criado_em
FROM public.aprovacoes_relatorios_semanais_obra
ORDER BY criado_em DESC, id DESC
LIMIT 20;

SELECT
    COUNT(*) AS total_decisoes,
    COUNT(*) FILTER (WHERE aprovado) AS total_aprovacoes,
    COUNT(*) FILTER (WHERE rejeitado) AS total_rejeicoes,
    COUNT(*) FILTER (WHERE ajustes_solicitados) AS total_ajustes,
    COUNT(*) FILTER (
        WHERE enviado_para_terceiros
           OR gerou_link_publico
           OR alterou_rdo_oficial
           OR alterou_cronograma
           OR executou_rpa
           OR sincronizou_openproject
           OR alterou_minio
    ) AS violacoes_governanca
FROM public.aprovacoes_relatorios_semanais_obra;

SELECT
    id,
    obra_codigo,
    status,
    aprovado_por,
    aprovado_em,
    rejeitado_por,
    rejeitado_em,
    ajustes_solicitados_por,
    ajustes_solicitados_em,
    motivo_decisao,
    observacao_decisao,
    atualizado_em
FROM public.pdfs_relatorios_semanais_obra
WHERE status IN (
    'APROVADO_PARA_USO_INTERNO',
    'REJEITADO',
    'AJUSTES_SOLICITADOS'
)
ORDER BY atualizado_em DESC, id DESC
LIMIT 20;
