-- Validacao da persistencia do relatorio semanal executivo (MVP 0.7H)

SELECT
    to_regclass('public.relatorios_semanais_executivos_obra') AS tabela_relatorios_semanais;

SELECT
    id,
    obra_codigo,
    area,
    data_inicio,
    data_fim,
    tipo_relatorio,
    status,
    payload_relatorio ->> 'status_executivo' AS status_executivo,
    criado_em
FROM public.relatorios_semanais_executivos_obra
ORDER BY criado_em DESC, id DESC
LIMIT 10;
