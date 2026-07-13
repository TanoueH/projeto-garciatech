-- Migration 016 - Solicitacao controlada de envio futuro do relatorio semanal (MVP 0.7L)

CREATE TABLE IF NOT EXISTS public.solicitacoes_envio_relatorios_semanais_obra (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'construtora-piloto',
    obra_codigo TEXT NOT NULL,
    area TEXT NULL,
    pdf_relatorio_id BIGINT NOT NULL,
    aprovacao_relatorio_id BIGINT NULL,
    canal_pretendido TEXT NOT NULL,
    destinatario_nome TEXT NULL,
    destinatario_contato TEXT NULL,
    assunto TEXT NULL,
    mensagem TEXT NULL,
    status TEXT NOT NULL DEFAULT 'SOLICITADO',
    solicitado_por TEXT NULL,
    solicitante_telegram_user_id TEXT NULL,
    solicitante_telegram_username TEXT NULL,
    solicitante_chat_id TEXT NULL,
    canal_origem TEXT NOT NULL DEFAULT 'telegram',
    validacao_pdf_status TEXT NULL,
    pdf_aprovado BOOLEAN NOT NULL DEFAULT false,
    envio_executado BOOLEAN NOT NULL DEFAULT false,
    enviado_para_terceiros BOOLEAN NOT NULL DEFAULT false,
    gerou_link_publico BOOLEAN NOT NULL DEFAULT false,
    gerou_presigned_url BOOLEAN NOT NULL DEFAULT false,
    anexou_arquivo BOOLEAN NOT NULL DEFAULT false,
    alterou_rdo_oficial BOOLEAN NOT NULL DEFAULT false,
    alterou_cronograma BOOLEAN NOT NULL DEFAULT false,
    executou_rpa BOOLEAN NOT NULL DEFAULT false,
    sincronizou_openproject BOOLEAN NOT NULL DEFAULT false,
    alterou_minio BOOLEAN NOT NULL DEFAULT false,
    metadados JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_solicitacoes_envio_relatorios_semanais_obra_codigo
    ON public.solicitacoes_envio_relatorios_semanais_obra (obra_codigo);
CREATE INDEX IF NOT EXISTS idx_solicitacoes_envio_relatorios_semanais_area
    ON public.solicitacoes_envio_relatorios_semanais_obra (area);
CREATE INDEX IF NOT EXISTS idx_solicitacoes_envio_relatorios_semanais_pdf_id
    ON public.solicitacoes_envio_relatorios_semanais_obra (pdf_relatorio_id);
CREATE INDEX IF NOT EXISTS idx_solicitacoes_envio_relatorios_semanais_aprovacao_id
    ON public.solicitacoes_envio_relatorios_semanais_obra (aprovacao_relatorio_id);
CREATE INDEX IF NOT EXISTS idx_solicitacoes_envio_relatorios_semanais_canal
    ON public.solicitacoes_envio_relatorios_semanais_obra (canal_pretendido);
CREATE INDEX IF NOT EXISTS idx_solicitacoes_envio_relatorios_semanais_status
    ON public.solicitacoes_envio_relatorios_semanais_obra (status);
CREATE INDEX IF NOT EXISTS idx_solicitacoes_envio_relatorios_semanais_pdf_aprovado
    ON public.solicitacoes_envio_relatorios_semanais_obra (pdf_aprovado);
CREATE INDEX IF NOT EXISTS idx_solicitacoes_envio_relatorios_semanais_envio_executado
    ON public.solicitacoes_envio_relatorios_semanais_obra (envio_executado);
CREATE INDEX IF NOT EXISTS idx_solicitacoes_envio_relatorios_semanais_criado_em
    ON public.solicitacoes_envio_relatorios_semanais_obra (criado_em);
