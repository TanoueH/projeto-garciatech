-- Validacao nao destrutiva do MVP 0.7J.

SELECT
    id,
    obra_codigo,
    area,
    exportacao_relatorio_id,
    relatorio_semanal_id,
    data_inicio,
    data_fim,
    status,
    nome_arquivo,
    caminho_local,
    minio_uri,
    tamanho_bytes,
    sha256,
    enviado_para_terceiros,
    gerou_link_publico,
    alterou_rdo_oficial,
    alterou_cronograma,
    executou_rpa,
    sincronizou_openproject,
    metadados,
    criado_em
FROM public.pdfs_relatorios_semanais_obra
ORDER BY criado_em DESC, id DESC
LIMIT 20;

SELECT
    COUNT(*) AS total_pdfs,
    COUNT(*) FILTER (WHERE minio_uri IS NOT NULL) AS armazenados_minio,
    COUNT(*) FILTER (WHERE caminho_local IS NOT NULL) AS armazenados_localmente,
    COUNT(*) FILTER (
        WHERE enviado_para_terceiros
           OR gerou_link_publico
           OR alterou_rdo_oficial
           OR alterou_cronograma
           OR executou_rpa
           OR sincronizou_openproject
    ) AS violacoes_governanca
FROM public.pdfs_relatorios_semanais_obra;
