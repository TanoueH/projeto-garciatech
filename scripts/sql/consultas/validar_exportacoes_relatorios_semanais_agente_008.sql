-- Validacao nao destrutiva da exportacao semanal controlada (MVP 0.7I)

SELECT
    id,
    obra_codigo,
    area,
    relatorio_semanal_id,
    data_inicio,
    data_fim,
    formato,
    status,
    enviado_para_terceiros,
    alterou_rdo_oficial,
    alterou_cronograma,
    executou_rpa,
    sincronizou_openproject,
    gerou_pdf,
    gerou_link_publico,
    criado_em
FROM public.exportacoes_relatorios_semanais_obra
ORDER BY criado_em DESC, id DESC
LIMIT 20;

SELECT
    count(*) FILTER (WHERE formato <> 'MARKDOWN') AS formatos_fora_do_mvp,
    count(*) FILTER (
        WHERE enviado_para_terceiros
           OR alterou_rdo_oficial
           OR alterou_cronograma
           OR executou_rpa
           OR sincronizou_openproject
           OR gerou_pdf
           OR gerou_link_publico
    ) AS exportacoes_com_acao_proibida
FROM public.exportacoes_relatorios_semanais_obra;
