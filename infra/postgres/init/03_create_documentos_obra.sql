CREATE SCHEMA IF NOT EXISTS core_obra;

CREATE TABLE IF NOT EXISTS core_obra.documentos_obra (
    id BIGSERIAL PRIMARY KEY,

    obra_codigo VARCHAR(50) NOT NULL,
    tipo_documento VARCHAR(100) NOT NULL,
    responsavel VARCHAR(100),
    data_documento DATE,

    descricao TEXT,

    nome_original TEXT,
    nome_padronizado TEXT NOT NULL,
    caminho_arquivo TEXT NOT NULL,

    origem VARCHAR(100) DEFAULT 'n8n_webhook',
    status VARCHAR(50) DEFAULT 'recebido',

    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documentos_obra_codigo
ON core_obra.documentos_obra (obra_codigo);

CREATE INDEX IF NOT EXISTS idx_documentos_tipo
ON core_obra.documentos_obra (tipo_documento);

CREATE INDEX IF NOT EXISTS idx_documentos_data
ON core_obra.documentos_obra (data_documento);

CREATE INDEX IF NOT EXISTS idx_documentos_criado_em
ON core_obra.documentos_obra (criado_em);
