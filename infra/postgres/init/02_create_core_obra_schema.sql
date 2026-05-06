CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS core.obras (
    id SERIAL PRIMARY KEY,
    codigo_obra VARCHAR(50) UNIQUE NOT NULL,
    nome_obra TEXT NOT NULL,
    cliente TEXT,
    localizacao TEXT,
    data_inicio DATE,
    data_fim_prevista DATE,
    status VARCHAR(50) DEFAULT 'ativa',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS core.fornecedores (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    cnpj VARCHAR(30),
    tipo_fornecedor VARCHAR(100),
    contato TEXT,
    email TEXT,
    telefone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS core.contratos (
    id SERIAL PRIMARY KEY,
    obra_id INTEGER REFERENCES core.obras(id),
    fornecedor_id INTEGER REFERENCES core.fornecedores(id),
    numero_contrato VARCHAR(100),
    objeto TEXT,
    valor_contratado NUMERIC(14,2),
    data_inicio DATE,
    data_fim DATE,
    status VARCHAR(50) DEFAULT 'ativo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS core.documentos (
    id SERIAL PRIMARY KEY,
    obra_id INTEGER REFERENCES core.obras(id),
    tipo_documento VARCHAR(100),
    nome_arquivo TEXT NOT NULL,
    caminho_minio TEXT,
    bucket_minio VARCHAR(100),
    origem VARCHAR(100),
    responsavel TEXT,
    data_documento DATE,
    data_recebimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'recebido',
    observacoes TEXT
);

CREATE TABLE IF NOT EXISTS core.medicoes (
    id SERIAL PRIMARY KEY,
    obra_id INTEGER REFERENCES core.obras(id),
    contrato_id INTEGER REFERENCES core.contratos(id),
    numero_medicao VARCHAR(50),
    periodo_inicio DATE,
    periodo_fim DATE,
    valor_medido NUMERIC(14,2),
    percentual_avanco NUMERIC(6,2),
    status VARCHAR(50) DEFAULT 'em_analise',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS core.pendencias (
    id SERIAL PRIMARY KEY,
    obra_id INTEGER REFERENCES core.obras(id),
    titulo TEXT NOT NULL,
    descricao TEXT,
    categoria VARCHAR(100),
    prioridade VARCHAR(50),
    responsavel TEXT,
    status VARCHAR(50) DEFAULT 'aberta',
    data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_limite DATE,
    data_fechamento TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit.processamento_arquivos (
    id SERIAL PRIMARY KEY,
    nome_arquivo TEXT NOT NULL,
    origem TEXT,
    bucket_minio TEXT,
    caminho_minio TEXT,
    status VARCHAR(50),
    mensagem_erro TEXT,
    processado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
