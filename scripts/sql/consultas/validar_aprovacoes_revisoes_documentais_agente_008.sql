-- Validacao do MVP 0.8B: decisoes e invariantes de seguranca documental.

SELECT decisao, status_revisao_resultante, status_vigencia_resultante, COUNT(*)
FROM public.aprovacoes_revisoes_documentais_obra
GROUP BY decisao, status_revisao_resultante, status_vigencia_resultante
ORDER BY decisao;

SELECT id, obra_codigo, revisao_documental_id, decisao, criado_em
FROM public.aprovacoes_revisoes_documentais_obra
WHERE enviado_para_terceiros
   OR gerou_link_publico
   OR alterou_rdo_oficial
   OR alterou_cronograma
   OR executou_rpa
   OR sincronizou_openproject
   OR alterou_minio
   OR moveu_arquivo_minio
   OR apagou_arquivo_minio
   OR liberou_execucao_campo;

SELECT obra_codigo, codigo_documento, COUNT(*) AS vigentes
FROM public.revisoes_documentais_obra
WHERE status_vigencia = 'VIGENTE'
  AND NULLIF(BTRIM(codigo_documento), '') IS NOT NULL
GROUP BY obra_codigo, codigo_documento
HAVING COUNT(*) > 1;
