-- Validacao nao destrutiva do MVP 0.7L.

SELECT
    id,
    obra_codigo,
    area,
    pdf_relatorio_id,
    aprovacao_relatorio_id,
    canal_pretendido,
    destinatario_nome,
    destinatario_contato,
    status,
    validacao_pdf_status,
    pdf_aprovado,
    envio_executado,
    enviado_para_terceiros,
    gerou_link_publico,
    gerou_presigned_url,
    anexou_arquivo,
    alterou_rdo_oficial,
    alterou_cronograma,
    executou_rpa,
    sincronizou_openproject,
    alterou_minio,
    criado_em
FROM public.solicitacoes_envio_relatorios_semanais_obra
ORDER BY criado_em DESC, id DESC
LIMIT 20;

SELECT
    COUNT(*) AS total_solicitacoes,
    COUNT(*) FILTER (
        WHERE status = 'SOLICITADO_AGUARDANDO_EXECUCAO_CONTROLADA'
    ) AS aguardando_execucao_controlada,
    COUNT(*) FILTER (
        WHERE envio_executado
           OR enviado_para_terceiros
           OR gerou_link_publico
           OR gerou_presigned_url
           OR anexou_arquivo
           OR alterou_rdo_oficial
           OR alterou_cronograma
           OR executou_rpa
           OR sincronizou_openproject
           OR alterou_minio
    ) AS violacoes_governanca
FROM public.solicitacoes_envio_relatorios_semanais_obra;
