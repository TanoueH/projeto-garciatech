import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import psycopg
from psycopg.types.json import Json
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field


APP_NAME = "Construction Science Agents API"
APP_VERSION = "0.1.0"


DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
TZ = os.getenv("TZ", "America/Sao_Paulo")


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="API core do MVP Obra-Caio Control Tower.",
)


class EntradaPayload(BaseModel):
    tenant_id: Optional[str] = Field(default="construtora-piloto")
    obra_codigo: Optional[str] = Field(default="OBRA-CAIO")
    canal: Optional[str] = Field(default="desconhecido")
    remetente_nome: Optional[str] = None
    remetente_identificador: Optional[str] = None
    tipo_mensagem: Optional[str] = "texto"
    conteudo: Optional[str] = None
    anexos: Optional[list[dict[str, Any]]] = Field(default_factory=list)
    payload_original: Optional[Dict[str, Any]] = Field(default_factory=dict)


def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não definida.")
    return psycopg.connect(DATABASE_URL)


def stable_hash(data: Any) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ensure_core_tables() -> None:
    sql = """
    CREATE TABLE IF NOT EXISTS mensagens_recebidas (
        id SERIAL PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        obra_codigo TEXT NOT NULL,
        canal TEXT NOT NULL,
        remetente_nome TEXT,
        remetente_identificador TEXT,
        tipo_mensagem TEXT,
        conteudo TEXT,
        anexos JSONB DEFAULT '[]'::jsonb,
        payload_original JSONB,
        payload_normalizado JSONB,
        correlation_id UUID NOT NULL,
        idempotency_key TEXT UNIQUE NOT NULL,
        payload_hash TEXT,
        status_processamento TEXT DEFAULT 'RECEBIDA',
        criado_em TIMESTAMP DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS eventos_processados (
        id SERIAL PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        obra_codigo TEXT,
        idempotency_key TEXT UNIQUE NOT NULL,
        correlation_id UUID,
        agente TEXT,
        origem TEXT,
        status TEXT NOT NULL,
        recurso_tipo TEXT,
        recurso_id INTEGER,
        payload_hash TEXT,
        mensagem_erro TEXT,
        criado_em TIMESTAMP DEFAULT NOW(),
        atualizado_em TIMESTAMP DEFAULT NOW()
    );
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


@app.on_event("startup")
def startup_event():
    ensure_core_tables()


@app.get("/")
def root():
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "status": "online",
        "mvp": "Obra-Caio Control Tower",
    }


@app.get("/status/health")
def healthcheck():
    db_status = "unknown"

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        db_status = "ok"
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "error",
                "error": str(exc),
            },
        )

    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/webhooks/entrada")
async def receber_entrada(
    request: Request,
    x_correlation_id: Optional[str] = Header(default=None),
):
    raw_payload = await request.json()

    try:
        payload = EntradaPayload(**raw_payload)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Payload inválido para entrada.",
                "error": str(exc),
            },
        )

    correlation_id = x_correlation_id or str(uuid.uuid4())

    normalized = {
        "tenant_id": payload.tenant_id or "construtora-piloto",
        "obra_codigo": payload.obra_codigo or "OBRA-CAIO",
        "canal": payload.canal or "desconhecido",
        "remetente_nome": payload.remetente_nome,
        "remetente_identificador": payload.remetente_identificador,
        "tipo_mensagem": payload.tipo_mensagem or "texto",
        "conteudo": payload.conteudo,
        "anexos": payload.anexos or [],
        "correlation_id": correlation_id,
    }

    payload_hash = stable_hash(raw_payload)
    idempotency_key = f"{normalized['obra_codigo']}:{normalized['canal']}:{payload_hash}"

    insert_sql = """
    INSERT INTO mensagens_recebidas (
        tenant_id,
        obra_codigo,
        canal,
        remetente_nome,
        remetente_identificador,
        tipo_mensagem,
        conteudo,
        anexos,
        payload_original,
        payload_normalizado,
        correlation_id,
        idempotency_key,
        payload_hash,
        status_processamento
    )
    VALUES (
        %(tenant_id)s,
        %(obra_codigo)s,
        %(canal)s,
        %(remetente_nome)s,
        %(remetente_identificador)s,
        %(tipo_mensagem)s,
        %(conteudo)s,
        %(anexos)s,
        %(payload_original)s,
        %(payload_normalizado)s,
        %(correlation_id)s,
        %(idempotency_key)s,
        %(payload_hash)s,
        'RECEBIDA'
    )
    ON CONFLICT (idempotency_key)
    DO NOTHING
    RETURNING id, status_processamento;
    """

    row = None

    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    insert_sql,
                    {
                        "tenant_id": normalized["tenant_id"],
                        "obra_codigo": normalized["obra_codigo"],
                        "canal": normalized["canal"],
                        "remetente_nome": normalized["remetente_nome"],
                        "remetente_identificador": normalized["remetente_identificador"],
                        "tipo_mensagem": normalized["tipo_mensagem"],
                        "conteudo": normalized["conteudo"],
                        "anexos": Json(normalized["anexos"]),
                        "payload_original": Json(raw_payload),
                        "payload_normalizado": Json(normalized),
                        "correlation_id": correlation_id,
                        "idempotency_key": idempotency_key,
                        "payload_hash": payload_hash,
                    },
                )

                row = cur.fetchone()

                if row is None:
                    cur.execute(
                        """
                        SELECT id, 'DUPLICADA' AS status_processamento
                        FROM mensagens_recebidas
                        WHERE idempotency_key = %(idempotency_key)s;
                        """,
                        {"idempotency_key": idempotency_key},
                    )
                    row = cur.fetchone()

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Erro ao registrar entrada no banco.",
                "error": str(exc),
                "idempotency_key": idempotency_key,
            },
        )

    if row is None:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Falha ao registrar ou recuperar mensagem recebida.",
                "idempotency_key": idempotency_key,
            },
        )

    return {
        "ok": True,
        "mensagem_id": row[0],
        "status_processamento": row[1],
        "correlation_id": correlation_id,
        "idempotency_key": idempotency_key,
        "next_action": "CLASSIFICAR",
        "message": "Entrada registrada com sucesso.",
    }


@app.post("/agentes/classificar")
async def classificar_payload(request: Request):
    payload = await request.json()
    texto = json.dumps(payload, ensure_ascii=False).lower()

    if any(term in texto for term in ["nota fiscal", "nf-e", "nfe", "danfe"]):
        categoria = "NOTA_FISCAL"
    elif any(term in texto for term in ["orçamento", "cotação", "proposta"]):
        categoria = "ORCAMENTO_RECEBIDO"
    elif any(term in texto for term in ["comprar", "compra", "material", "faltou", "precisa cotar"]):
        categoria = "SOLICITACAO_COMPRA"
    elif any(term in texto for term in ["pendência", "problema", "atraso", "não executado"]):
        categoria = "PENDENCIA"
    elif any(term in texto for term in ["rdo", "hoje executamos", "equipe", "atividade"]):
        categoria = "RELATO_RDO"
    elif any(term in texto for term in ["foto", "imagem"]):
        categoria = "FOTO_OBRA"
    else:
        categoria = "MENSAGEM_GERAL"

    return {
        "ok": True,
        "categoria": categoria,
        "metodo": "rule_based_mvp",
        "observacao": "Classificador provisório sem LLM para teste inicial do api_core.",
    }


@app.get("/obras/{obra_codigo}/resumo-dia")
def resumo_dia(obra_codigo: str):
    sql = """
    SELECT
        COUNT(*) FILTER (WHERE status_processamento = 'RECEBIDA') AS recebidas,
        COUNT(*) FILTER (WHERE status_processamento = 'DUPLICADA') AS duplicadas,
        COUNT(*) AS total
    FROM mensagens_recebidas
    WHERE obra_codigo = %(obra_codigo)s
      AND criado_em::date = CURRENT_DATE;
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {"obra_codigo": obra_codigo})
            row = cur.fetchone()

    return {
        "obra_codigo": obra_codigo,
        "data": datetime.now().date().isoformat(),
        "mensagens_recebidas": row[0] or 0,
        "mensagens_duplicadas": row[1] or 0,
        "total_mensagens": row[2] or 0,
    }
