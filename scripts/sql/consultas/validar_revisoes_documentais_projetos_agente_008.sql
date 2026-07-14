-- Validacao da migration 017 / MVP 0.8A.

SELECT status_revisao, status_vigencia, liberado_para_campo, COUNT(*) AS total
FROM public.revisoes_documentais_obra
GROUP BY status_revisao, status_vigencia, liberado_para_campo
ORDER BY status_revisao, status_vigencia, liberado_para_campo;

SELECT obra_codigo, bucket, object_key, COUNT(*) AS total
FROM public.revisoes_documentais_obra
WHERE bucket IS NOT NULL AND object_key IS NOT NULL
GROUP BY obra_codigo, bucket, object_key
HAVING COUNT(*) > 1;

SELECT id, obra_codigo, nome_arquivo_original
FROM public.revisoes_documentais_obra
WHERE enviado_para_terceiros
   OR gerou_link_publico
   OR alterou_rdo_oficial
   OR alterou_cronograma
   OR executou_rpa
   OR sincronizou_openproject
   OR liberou_execucao_campo
   OR liberado_para_campo;
