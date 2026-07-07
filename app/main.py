import hashlib
import re
import json
import os
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from typing import Any, Dict, Optional

import psycopg
from minio import Minio
from psycopg.types.json import Json
from fastapi import FastAPI, Header, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel, Field


APP_NAME = "Construction Science Agents API"
APP_VERSION = "0.1.0"


DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
TZ = os.getenv("TZ", "America/Sao_Paulo")
TELEGRAM_ALLOWED_USER_IDS = os.getenv("TELEGRAM_ALLOWED_USER_IDS")
TELEGRAM_ALLOWED_CHAT_IDS = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS")
TELEGRAM_EXECUTIVE_USER_ID = os.getenv("TELEGRAM_EXECUTIVE_USER_ID")
TELEGRAM_EXECUTIVE_CHAT_ID = os.getenv("TELEGRAM_EXECUTIVE_CHAT_ID")


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


class TelegramEntradaPayload(BaseModel):
    tenant_id: Optional[str] = Field(default="construtora-piloto")
    obra_codigo: Optional[str] = Field(default="OBRA-CAIO")
    telegram_update_id: Optional[str] = None
    telegram_message_id: Optional[str] = None
    telegram_user_id: Optional[str] = None
    telegram_username: Optional[str] = None
    chat_id: Optional[str] = None
    chat_type: Optional[str] = None
    remetente_nome: Optional[str] = None
    remetente_identificador: Optional[str] = None
    usuario_autorizado: Optional[bool] = Field(default=False)
    motivo_autorizacao: Optional[str] = None
    tipo_mensagem: Optional[str] = "texto"
    conteudo: Optional[str] = None
    anexos: Optional[list[dict[str, Any]]] = Field(default_factory=list)
    payload_original: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ProcessarComandoRDORequest(BaseModel):
    id_comando: Optional[str] = None


class ProcessarComandoComunicacaoObraRequest(BaseModel):
    id_comando: Optional[str] = None


def get_db_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL não definida.")
    return psycopg.connect(DATABASE_URL)


def stable_hash(data: Any) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_correlation_id(value: Optional[str]) -> str:
    if not value:
        return str(uuid.uuid4())

    try:
        return str(uuid.UUID(value))
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "X-Correlation-Id inválido. Use um UUID válido.",
                "error": str(exc),
            },
        )


def has_any_term(texto: str, termos: list[str]) -> bool:
    return any(termo in texto for termo in termos)


def parse_instrucao_aprovacao_comando(conteudo: Optional[str]) -> Optional[dict[str, Any]]:
    texto = (conteudo or "").strip().lower()
    if not texto:
        return None

    match = re.search(
        r"\b(aprovar|aprova|autorizar|confirmar|cancelar|cancela|rejeitar)\s+comando\s+([0-9a-fA-F-]+)\b",
        texto,
    )
    if not match:
        return None

    verbo = match.group(1)
    identificador = match.group(2)
    acao = "CANCELAR" if verbo in {"cancelar", "cancela", "rejeitar"} else "APROVAR"
    tipo_identificador = "id_comando" if "-" in identificador else "id"

    if tipo_identificador == "id":
        try:
            comando_id = int(identificador)
        except ValueError:
            return None
        return {
            "acao": acao,
            "comando_id": comando_id,
            "id_comando": None,
            "identificador": str(comando_id),
            "tipo_identificador": tipo_identificador,
        }

    try:
        id_comando = str(uuid.UUID(identificador))
    except ValueError:
        return None

    return {
        "acao": acao,
        "comando_id": None,
        "id_comando": id_comando,
        "identificador": id_comando,
        "tipo_identificador": tipo_identificador,
    }


def classificar_instrucao_aprovacao(instrucao: dict[str, Any]) -> dict[str, Any]:
    if instrucao["acao"] == "APROVAR":
        return {
            "intencao": "APROVAR_COMANDO_EXECUTIVO",
            "agente_destino": "AGENTE_007_ORQUESTRADOR_EXECUTIVO",
            "tipo_comando": "APROVAR_COMANDO_EXECUTIVO",
            "requer_aprovacao": False,
            "confianca": 0.98,
            "justificativa": "Mensagem solicita aprovação auditável de comando executivo existente.",
        }

    return {
        "intencao": "CANCELAR_COMANDO_EXECUTIVO",
        "agente_destino": "AGENTE_007_ORQUESTRADOR_EXECUTIVO",
        "tipo_comando": "CANCELAR_COMANDO_EXECUTIVO",
        "requer_aprovacao": False,
        "confianca": 0.98,
        "justificativa": "Mensagem solicita cancelamento auditável de comando executivo existente.",
    }


def parse_env_allowlist(*values: Optional[str]) -> set[str]:
    allowed: set[str] = set()
    for value in values:
        if not value:
            continue
        allowed.update(part.strip() for part in value.split(",") if part.strip())
    return allowed


def avaliar_autorizacao_telegram(payload: TelegramEntradaPayload) -> tuple[bool, str]:
    allowed_user_ids = parse_env_allowlist(
        TELEGRAM_ALLOWED_USER_IDS,
        TELEGRAM_EXECUTIVE_USER_ID,
    )
    allowed_chat_ids = parse_env_allowlist(
        TELEGRAM_ALLOWED_CHAT_IDS,
        TELEGRAM_EXECUTIVE_CHAT_ID,
    )

    if payload.telegram_user_id and payload.telegram_user_id in allowed_user_ids:
        return True, "Autorizado por telegram_user_id configurado em variável de ambiente."

    if payload.chat_id and payload.chat_id in allowed_chat_ids:
        return True, "Autorizado por chat_id configurado em variável de ambiente."

    if not allowed_user_ids and not allowed_chat_ids:
        return (
            False,
            "Bloqueado: nenhuma allowlist Telegram configurada nas variáveis de ambiente.",
        )

    if not payload.telegram_user_id and not payload.chat_id:
        return (
            False,
            "Bloqueado: payload não trouxe telegram_user_id nem chat_id para validação.",
        )

    return (
        False,
        "Bloqueado: telegram_user_id/chat_id não constam nas allowlists de ambiente.",
    )


def classificar_intencao_executiva(conteudo: Optional[str]) -> dict[str, Any]:
    texto = (conteudo or "").lower()
    termos_rdo = ["rdo", "diário de obra", "diario de obra", "diário", "diario", "relatório diário", "relatorio diario"]
    menciona_rdo = has_any_term(texto, termos_rdo)
    termos_placa = [
        "placa",
        "placa de aviso",
        "aviso para o canteiro",
        "comunicado para a obra",
        "sinalização da obra",
        "sinalizacao da obra",
        "placa de segurança",
        "placa de seguranca",
    ]
    menciona_placa = has_any_term(texto, termos_placa)

    if has_any_term(texto, ["confirmar", "confirmo", "aprovado", "aprovar"]):
        return {
            "intencao": "CONFIRMAR_COMANDO",
            "agente_destino": "AGENTE_007_ORQUESTRADOR_EXECUTIVO",
            "tipo_comando": "CONFIRMAR_COMANDO_EXECUTIVO",
            "requer_aprovacao": False,
            "confianca": 0.90,
            "justificativa": "Mensagem indica confirmação ou aprovação executiva.",
        }

    if has_any_term(texto, ["cancelar", "cancele", "rejeitar", "rejeito", "não aprovar", "nao aprovar"]):
        return {
            "intencao": "CANCELAR_COMANDO",
            "agente_destino": "AGENTE_007_ORQUESTRADOR_EXECUTIVO",
            "tipo_comando": "CANCELAR_COMANDO_EXECUTIVO",
            "requer_aprovacao": False,
            "confianca": 0.90,
            "justificativa": "Mensagem indica cancelamento ou rejeição executiva.",
        }

    if menciona_placa and has_any_term(
        texto,
        [
            "gerar pdf",
            "gerar o pdf",
            "gere o pdf",
            "pdf da placa",
            "pdf do aviso",
            "emitir pdf",
            "emita o pdf",
        ],
    ):
        return {
            "intencao": "GERAR_PDF_PLACA_AVISO",
            "agente_destino": "AGENTE_006_COMUNICACAO_VISUAL_OBRA",
            "tipo_comando": "GERAR_PDF_PLACA_AVISO",
            "requer_aprovacao": True,
            "confianca": 0.88,
            "justificativa": "Geração de PDF de placa é ação sensível e exige aprovação; nenhum PDF real é gerado nesta etapa.",
        }

    if menciona_placa and has_any_term(
        texto,
        ["imprimir", "impressão", "impressao", "imprima", "mande imprimir", "solicite impressão", "solicite impressao"],
    ):
        return {
            "intencao": "IMPRIMIR_PLACA_AVISO",
            "agente_destino": "AGENTE_006_COMUNICACAO_VISUAL_OBRA",
            "tipo_comando": "IMPRIMIR_PLACA_AVISO",
            "requer_aprovacao": True,
            "confianca": 0.88,
            "justificativa": "Impressão de placa é ação sensível e exige aprovação; nenhuma impressão real é executada nesta etapa.",
        }

    if menciona_placa and has_any_term(
        texto,
        ["instalar", "instale", "instala", "fixar", "fixe", "colocar a placa", "coloque a placa"],
    ):
        return {
            "intencao": "INSTALAR_PLACA_AVISO",
            "agente_destino": "AGENTE_006_COMUNICACAO_VISUAL_OBRA",
            "tipo_comando": "INSTALAR_PLACA_AVISO",
            "requer_aprovacao": True,
            "confianca": 0.88,
            "justificativa": "Instalação de placa é ação sensível e exige aprovação; nenhuma instalação é executada nesta etapa.",
        }

    if menciona_placa and has_any_term(
        texto,
        [
            "prepare",
            "preparar",
            "gerar placa",
            "gerar placa de aviso",
            "crie",
            "criar",
            "monte",
            "montar",
            "elabore",
            "elaborar",
            "rascunho",
            "uso obrigatório de epi",
            "uso obrigatorio de epi",
            "aviso",
            "comunicado",
            "sinalização",
            "sinalizacao",
        ],
    ):
        return {
            "intencao": "PREPARAR_PLACA_AVISO",
            "agente_destino": "AGENTE_006_COMUNICACAO_VISUAL_OBRA",
            "tipo_comando": "PREPARAR_PLACA_AVISO",
            "requer_aprovacao": False,
            "confianca": 0.87,
            "justificativa": "Mensagem indica preparação de rascunho textual de placa de aviso sem PDF, impressão ou instalação.",
        }

    if has_any_term(
        texto,
        ["imprimir", "impressão", "impressao", "imprima", "mande imprimir", "solicite impressão", "solicite impressao"],
    ):
        return {
            "intencao": "SOLICITAR_IMPRESSAO",
            "agente_destino": "AGENTE_007_ORQUESTRADOR_EXECUTIVO",
            "tipo_comando": "SOLICITAR_IMPRESSAO",
            "requer_aprovacao": True,
            "confianca": 0.86,
            "justificativa": "Solicitação de impressão exige aprovação e não executa impressão real nesta etapa.",
        }

    if menciona_rdo and has_any_term(
        texto,
        [
            "gerar pdf",
            "gerar o pdf",
            "gere o pdf",
            "emita o pdf",
            "emitir o pdf",
            "pdf do rdo",
            "pdf do diário",
            "pdf do diario",
            "rdo em pdf",
            "diário em pdf",
            "diario em pdf",
            "feche o rdo em pdf",
            "fechar o rdo em pdf",
            "exportar rdo",
            "exporte o rdo",
            "faça o pdf",
            "faca o pdf",
            "cópia em pdf",
            "copia em pdf",
        ],
    ):
        return {
            "intencao": "GERAR_PDF_RDO",
            "agente_destino": "AGENTE_RDO",
            "tipo_comando": "GERAR_PDF_RDO",
            "requer_aprovacao": True,
            "confianca": 0.86,
            "justificativa": "Solicitação registrada apenas como comando; nenhum PDF real é gerado nesta etapa.",
        }

    if menciona_rdo and has_any_term(
        texto,
        [
            "atualizar rdo",
            "alterar rdo",
            "corrigir rdo",
            "mudar rdo",
            "atualize o rdo",
            "atualiza o rdo",
            "atualizar o rdo",
            "atualize rdo",
            "atualiza rdo",
            "altere o rdo",
            "corrija o rdo",
            "lançar rdo",
            "lancar rdo",
            "registrar rdo",
            "registre oficialmente",
            "registrar oficialmente",
            "rdo oficial",
        ],
    ):
        return {
            "intencao": "ATUALIZAR_RDO",
            "agente_destino": "AGENTE_RDO",
            "tipo_comando": "ATUALIZAR_RDO",
            "requer_aprovacao": True,
            "confianca": 0.88,
            "justificativa": "Alteração de RDO é ação sensível e não altera RDO oficial nesta etapa.",
        }

    if menciona_rdo and has_any_term(
        texto,
        [
            "prepare",
            "preparar",
            "monte",
            "montar",
            "crie",
            "criar",
            "elabore",
            "elaborar",
            "rascunho",
        ],
    ):
        return {
            "intencao": "PREPARAR_RDO",
            "agente_destino": "AGENTE_RDO",
            "tipo_comando": "PREPARAR_RDO",
            "requer_aprovacao": False,
            "confianca": 0.88,
            "justificativa": "Mensagem indica preparação de rascunho de RDO sem oficialização.",
        }

    if menciona_rdo:
        return {
            "intencao": "CONSULTAR_RDO",
            "agente_destino": "AGENTE_RDO",
            "tipo_comando": "CONSULTAR_RDO",
            "requer_aprovacao": False,
            "confianca": 0.82,
            "justificativa": "Mensagem classificada como consulta executiva de RDO.",
        }

    if has_any_term(texto, ["pendência", "pendencia", "problema", "atraso", "crítico", "critico"]):
        return {
            "intencao": "CONSULTAR_PENDENCIAS",
            "agente_destino": "AGENTE_PENDENCIAS",
            "tipo_comando": "CONSULTAR_PENDENCIAS",
            "requer_aprovacao": False,
            "confianca": 0.82,
            "justificativa": "Mensagem classificada como consulta de pendências.",
        }

    if has_any_term(texto, ["documento", "nota fiscal", "nf-e", "nfe", "contrato", "arquivo"]):
        return {
            "intencao": "CONSULTAR_DOCUMENTOS",
            "agente_destino": "AGENTE_DOCUMENTOS",
            "tipo_comando": "CONSULTAR_DOCUMENTOS",
            "requer_aprovacao": False,
            "confianca": 0.80,
            "justificativa": "Mensagem classificada como consulta documental.",
        }

    if has_any_term(texto, ["orçamento", "orcamento", "cotação", "cotacao", "proposta"]):
        return {
            "intencao": "CONSULTAR_ORCAMENTOS",
            "agente_destino": "AGENTE_ORCAMENTOS",
            "tipo_comando": "CONSULTAR_ORCAMENTOS",
            "requer_aprovacao": False,
            "confianca": 0.78,
            "justificativa": "Mensagem classificada como consulta de orçamentos.",
        }

    if has_any_term(texto, ["cronograma", "prazo", "marco", "planejamento"]):
        return {
            "intencao": "CONSULTAR_CRONOGRAMA",
            "agente_destino": "AGENTE_CRONOGRAMA",
            "tipo_comando": "CONSULTAR_CRONOGRAMA",
            "requer_aprovacao": False,
            "confianca": 0.78,
            "justificativa": "Mensagem classificada como consulta de cronograma.",
        }

    return {
        "intencao": "MENSAGEM_EXECUTIVA_GERAL",
        "agente_destino": "AGENTE_007_ORQUESTRADOR_EXECUTIVO",
        "tipo_comando": "TRIAGEM_EXECUTIVA",
        "requer_aprovacao": False,
        "confianca": 0.50,
        "justificativa": "Mensagem sem intenção executiva específica no classificador determinístico mínimo.",
    }


def table_exists(conn, qualified_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass(%s);", (qualified_name,))
        row = cur.fetchone()
    return bool(row and row[0])


def listar_pendencias_rdo(conn, obra_codigo: Optional[str]) -> list[dict[str, Any]]:
    if not obra_codigo:
        return []

    if table_exists(conn, "public.pendencias_obra"):
        sql = """
        SELECT
            descricao,
            categoria,
            prioridade,
            status_pendencia,
            responsavel_acao,
            prazo_limite
        FROM public.pendencias_obra
        WHERE obra_codigo = %(obra_codigo)s
        ORDER BY criado_em DESC
        LIMIT 5;
        """
        with conn.cursor() as cur:
            cur.execute(sql, {"obra_codigo": obra_codigo})
            return [
                {
                    "descricao": row[0],
                    "categoria": row[1],
                    "prioridade": row[2],
                    "status": row[3],
                    "responsavel": row[4],
                    "prazo_limite": row[5].isoformat() if row[5] else None,
                }
                for row in cur.fetchall()
            ]

    if table_exists(conn, "core.pendencias"):
        sql = """
        SELECT
            p.titulo,
            p.descricao,
            p.categoria,
            p.prioridade,
            p.status,
            p.responsavel,
            p.data_limite
        FROM core.pendencias AS p
        JOIN core.obras AS o ON o.id = p.obra_id
        WHERE o.codigo_obra = %(obra_codigo)s
        ORDER BY p.data_abertura DESC
        LIMIT 5;
        """
        with conn.cursor() as cur:
            cur.execute(sql, {"obra_codigo": obra_codigo})
            return [
                {
                    "titulo": row[0],
                    "descricao": row[1],
                    "categoria": row[2],
                    "prioridade": row[3],
                    "status": row[4],
                    "responsavel": row[5],
                    "prazo_limite": row[6].isoformat() if row[6] else None,
                }
                for row in cur.fetchall()
            ]

    return []


def listar_eventos_rdo(conn, obra_codigo: Optional[str]) -> list[dict[str, Any]]:
    if not obra_codigo or not table_exists(conn, "core.eventos_obra"):
        return []

    sql = """
    SELECT
        e.titulo,
        e.descricao,
        e.tipo_evento,
        e.data_evento,
        e.responsavel,
        e.severidade
    FROM core.eventos_obra AS e
    JOIN core.obras AS o ON o.id = e.obra_id
    WHERE o.codigo_obra = %(obra_codigo)s
    ORDER BY e.data_evento DESC NULLS LAST, e.created_at DESC
    LIMIT 5;
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"obra_codigo": obra_codigo})
        return [
            {
                "titulo": row[0],
                "descricao": row[1],
                "tipo_evento": row[2],
                "data_evento": row[3].isoformat() if row[3] else None,
                "responsavel": row[4],
                "severidade": row[5],
            }
            for row in cur.fetchall()
        ]


def montar_resultado_agente_rdo(
    comando: dict[str, Any],
    pendencias: list[dict[str, Any]],
    eventos: list[dict[str, Any]],
) -> dict[str, Any]:
    tipo_comando = comando["tipo_comando"]
    payload_comando = comando["payload_comando"] or {}
    entrada = payload_comando.get("entrada", {})
    conteudo = entrada.get("conteudo")

    tipo_resultado = "RASCUNHO_RDO" if tipo_comando == "PREPARAR_RDO" else "RESUMO_EXECUTIVO_RDO"

    return {
        "tipo_resultado": tipo_resultado,
        "agente": "AGENTE_002_GERADOR_RDO",
        "agente_alias_compatibilidade": "AGENTE_RDO",
        "modo_processamento": "DETERMINISTICO_MOCK",
        "id_comando": str(comando["id_comando"]),
        "correlation_id": str(comando["correlation_id"]),
        "obra_codigo": comando["obra_codigo"],
        "tipo_comando": tipo_comando,
        "resumo": {
            "titulo": "Resumo executivo operacional de RDO",
            "mensagem_origem": conteudo,
            "total_pendencias_consultadas": len(pendencias),
            "total_eventos_consultados": len(eventos),
            "observacao": "Resultado preliminar gerado sem LLM externo e sem ações externas.",
        },
        "rascunho_rdo": {
            "status": "RASCUNHO_NAO_OFICIAL",
            "atividades": [],
            "pendencias_referenciadas": pendencias,
            "eventos_referenciados": eventos,
            "campos_a_confirmar": [
                "data do RDO",
                "atividades executadas",
                "equipe",
                "equipamentos",
                "condicoes_climaticas",
                "evidencias",
            ],
        },
        "controles_operacionais": {
            "alterou_rdo_oficial": False,
            "gerou_pdf_real": False,
            "imprimiu": False,
            "enviou_mensagem_terceiros": False,
            "conectou_openclaw": False,
            "executou_rpa": False,
            "requer_aprovacao_para_oficializar": True,
        },
        "gerado_em": datetime.now(timezone.utc).isoformat(),
    }


def montar_mensagem_resposta_executiva_rdo(
    obra_codigo: Optional[str],
    tipo_resultado: Optional[str],
) -> Optional[str]:
    if tipo_resultado == "RASCUNHO_RDO":
        return (
            f"Rascunho de RDO preparado para {obra_codigo}. "
            "Status: rascunho não oficial. Nenhuma ação externa foi executada. "
            "Para oficializar, será necessária aprovação."
        )

    if tipo_resultado == "RESUMO_EXECUTIVO_RDO":
        return (
            f"Resumo executivo de RDO preparado para {obra_codigo}. "
            "Nenhuma ação externa foi executada."
        )

    return None


def inferir_tipo_placa_aviso(conteudo: Optional[str]) -> str:
    texto = (conteudo or "").lower()

    if has_any_term(texto, ["epi", "capacete", "bota", "luva", "óculos", "oculos"]):
        return "SEGURANCA_USO_OBRIGATORIO_EPI"
    if has_any_term(texto, ["canteiro", "obra"]):
        return "AVISO_CANTEIRO_OBRA"
    if has_any_term(texto, ["comunicado", "comunicação", "comunicacao"]):
        return "COMUNICADO_OPERACIONAL"

    return "PLACA_AVISO_GERAL"


def inferir_local_instalacao_placa(conteudo: Optional[str]) -> Optional[str]:
    texto = (conteudo or "").lower()

    if "entrada" in texto or "portaria" in texto:
        return "Entrada/portaria da obra"
    if "canteiro" in texto:
        return "Canteiro de obras"
    if "refeitório" in texto or "refeitorio" in texto:
        return "Refeitório"
    if "almoxarifado" in texto:
        return "Almoxarifado"
    if "escada" in texto or "acesso" in texto:
        return "Área de acesso/circulação"

    return None


def montar_resultado_agente_comunicacao_obra(comando: dict[str, Any]) -> dict[str, Any]:
    payload_comando = comando["payload_comando"] or {}
    entrada = payload_comando.get("entrada", {})
    conteudo = entrada.get("conteudo")
    tipo_placa = inferir_tipo_placa_aviso(conteudo)
    local_instalacao = inferir_local_instalacao_placa(conteudo)
    cor_base = "azul-petroleo"
    estilo_visual_referencia = "docs/reference/placas/README.md"

    if tipo_placa == "SEGURANCA_USO_OBRIGATORIO_EPI":
        titulo = "USO OBRIGATÓRIO DE EPI"
        mensagem_principal = "O acesso à área de obra exige uso dos EPIs definidos para a atividade."
        mensagem_secundaria = (
            "Antes do uso oficial, validar texto, pictogramas, local de instalação "
            "e requisitos aplicáveis com o responsável técnico/segurança do trabalho."
        )
        formato_sugerido = "A3 vertical, alta legibilidade, material resistente ao ambiente da obra"
    elif tipo_placa == "AVISO_CANTEIRO_OBRA":
        titulo = "AVISO AO CANTEIRO"
        mensagem_principal = "Atenção às orientações operacionais e de segurança da obra."
        mensagem_secundaria = (
            "Conteúdo preliminar para revisão interna; validar com responsável técnico/"
            "segurança do trabalho antes de uso oficial."
        )
        formato_sugerido = "A3 vertical ou A4 horizontal, conforme ponto de instalação"
    elif tipo_placa == "COMUNICADO_OPERACIONAL":
        titulo = "COMUNICADO DA OBRA"
        mensagem_principal = "Comunicado operacional para equipes e visitantes da obra."
        mensagem_secundaria = (
            "Revisar destinatários, data de validade e responsável pela autorização "
            "antes de qualquer divulgação oficial."
        )
        formato_sugerido = "A4 vertical, linguagem objetiva e identificação da obra"
    else:
        titulo = "PLACA DE AVISO"
        mensagem_principal = "Aviso preliminar para comunicação visual da obra."
        mensagem_secundaria = (
            "Rascunho não oficial. O conteúdo deve ser validado pelo responsável "
            "técnico/segurança do trabalho antes de uso oficial."
        )
        formato_sugerido = "A3 vertical ou A4 vertical, conforme distância de leitura"

    tipo_icone = "triangulo_amarelo_atencao"
    area_pictograma = {
        "posicao": "corpo branco central",
        "composicao": "pictograma grande em círculo azul",
        "status": "pictograma_preliminar_a_definir",
    }
    observacao_validacao_tecnica = (
        "Rascunho não oficial baseado na referência visual Obra-Caio/SUM. "
        "Validar texto, pictograma, local, dimensões e requisitos aplicáveis "
        "com o responsável técnico/segurança do trabalho antes de uso oficial."
    )

    campos_a_confirmar = [
        "texto final autorizado",
        "responsavel_tecnico_ou_seguranca_do_trabalho",
        "local_exato_de_instalacao",
        "dimensoes_finais",
        "material_da_placa",
        "necessidade_de_pictogramas",
    ]
    if local_instalacao is None:
        campos_a_confirmar.append("local_instalacao")

    return {
        "tipo_resultado": "RASCUNHO_PLACA_AVISO",
        "agente": "AGENTE_006_COMUNICACAO_VISUAL_OBRA",
        "modo_processamento": "DETERMINISTICO_MOCK",
        "id_comando": str(comando["id_comando"]),
        "correlation_id": str(comando["correlation_id"]),
        "obra_codigo": comando["obra_codigo"],
        "tipo_comando": comando["tipo_comando"],
        "titulo": titulo,
        "titulo_cabecalho": titulo,
        "mensagem_principal": mensagem_principal,
        "mensagem_secundaria": mensagem_secundaria,
        "tipo_placa": tipo_placa,
        "tipo_icone": tipo_icone,
        "cor_base": cor_base,
        "area_pictograma": area_pictograma,
        "texto_principal": mensagem_principal,
        "texto_secundario": mensagem_secundaria,
        "formato_sugerido": formato_sugerido,
        "estilo_visual_referencia": estilo_visual_referencia,
        "observacao_validacao_tecnica": observacao_validacao_tecnica,
        "local_instalacao_sugerido": local_instalacao,
        "status": "RASCUNHO_NAO_OFICIAL",
        "campos_a_confirmar": campos_a_confirmar,
        "observacao_validacao": (
            "Este conteúdo é um rascunho textual não oficial e não afirma "
            "conformidade normativa final. Deve ser validado pelo responsável "
            "técnico/segurança do trabalho antes de uso oficial."
        ),
        "controles_operacionais": {
            "gerou_pdf_real": False,
            "imprimiu": False,
            "executou_rpa": False,
            "conectou_openclaw": False,
            "alterou_rdo_oficial": False,
            "enviou_mensagem_terceiros": False,
            "requer_aprovacao_para_pdf_ou_impressao": True,
        },
        "gerado_em": datetime.now(timezone.utc).isoformat(),
    }


def montar_mensagem_resposta_executiva_comunicacao_obra(
    obra_codigo: Optional[str],
    tipo_resultado: Optional[str],
) -> Optional[str]:
    if tipo_resultado == "RASCUNHO_PLACA_AVISO":
        return (
            f"Rascunho de placa de aviso preparado para {obra_codigo}. "
            "Status: rascunho não oficial. Nenhum PDF, impressão, RPA ou envio externo foi executado. "
            "Validar com responsável técnico/segurança do trabalho antes de uso oficial."
        )

    return None


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


@app.post("/telegram/entrada")
async def receber_entrada_telegram(
    request: Request,
    x_correlation_id: Optional[str] = Header(default=None),
):
    raw_payload = await request.json()

    try:
        payload = TelegramEntradaPayload(**raw_payload)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Payload inválido para entrada Telegram.",
                "error": str(exc),
            },
        )

    correlation_id = parse_correlation_id(x_correlation_id)
    usuario_autorizado, motivo_autorizacao = avaliar_autorizacao_telegram(payload)
    instrucao_aprovacao = parse_instrucao_aprovacao_comando(payload.conteudo)
    classificacao = (
        classificar_instrucao_aprovacao(instrucao_aprovacao)
        if instrucao_aprovacao
        else classificar_intencao_executiva(payload.conteudo)
    )
    if not usuario_autorizado:
        classificacao = {
            "intencao": "USUARIO_NAO_AUTORIZADO",
            "agente_destino": "AGENTE_007_ORQUESTRADOR_EXECUTIVO",
            "tipo_comando": "BLOQUEAR_ENTRADA_NAO_AUTORIZADA",
            "requer_aprovacao": True,
            "confianca": 1.00,
            "justificativa": "Usuário não autorizado; comando registrado apenas para auditoria.",
        }

    normalized = {
        "tenant_id": payload.tenant_id or "construtora-piloto",
        "obra_codigo": payload.obra_codigo or "OBRA-CAIO",
        "canal": "telegram",
        "telegram_update_id": payload.telegram_update_id,
        "telegram_message_id": payload.telegram_message_id,
        "telegram_user_id": payload.telegram_user_id,
        "telegram_username": payload.telegram_username,
        "chat_id": payload.chat_id,
        "chat_type": payload.chat_type,
        "remetente_nome": payload.remetente_nome,
        "remetente_identificador": payload.remetente_identificador,
        "usuario_autorizado": usuario_autorizado,
        "motivo_autorizacao": motivo_autorizacao,
        "tipo_mensagem": payload.tipo_mensagem or "texto",
        "conteudo": payload.conteudo,
        "anexos": payload.anexos or [],
        "correlation_id": correlation_id,
        "intencao": classificacao["intencao"],
        "agente_destino": classificacao["agente_destino"],
    }
    if instrucao_aprovacao:
        normalized["instrucao_aprovacao"] = instrucao_aprovacao

    payload_hash = stable_hash(raw_payload)
    telegram_idempotency_parts = [
        normalized["telegram_update_id"],
        normalized["telegram_message_id"],
        normalized["chat_id"],
    ]
    if all(telegram_idempotency_parts):
        idempotency_parts = [
            normalized["obra_codigo"],
            normalized["canal"],
            *telegram_idempotency_parts,
        ]
    else:
        idempotency_parts = [
            normalized["obra_codigo"],
            normalized["canal"],
            payload_hash,
        ]
    idempotency_key = ":".join(str(part) for part in idempotency_parts)

    status_comando = (
        "AGUARDANDO_APROVACAO"
        if classificacao["requer_aprovacao"]
        else "PENDENTE"
    )

    insert_evento_sql = """
    INSERT INTO eventos_telegram (
        tenant_id,
        obra_codigo,
        canal,
        telegram_update_id,
        telegram_message_id,
        telegram_user_id,
        telegram_username,
        chat_id,
        chat_type,
        remetente_nome,
        remetente_identificador,
        usuario_autorizado,
        motivo_autorizacao,
        tipo_mensagem,
        conteudo,
        anexos,
        payload_original,
        payload_normalizado,
        payload_hash,
        idempotency_key,
        correlation_id,
        intencao,
        confianca,
        agente_destino,
        status_processamento
    )
    VALUES (
        %(tenant_id)s,
        %(obra_codigo)s,
        'telegram',
        %(telegram_update_id)s,
        %(telegram_message_id)s,
        %(telegram_user_id)s,
        %(telegram_username)s,
        %(chat_id)s,
        %(chat_type)s,
        %(remetente_nome)s,
        %(remetente_identificador)s,
        %(usuario_autorizado)s,
        %(motivo_autorizacao)s,
        %(tipo_mensagem)s,
        %(conteudo)s,
        %(anexos)s,
        %(payload_original)s,
        %(payload_normalizado)s,
        %(payload_hash)s,
        %(idempotency_key)s,
        %(correlation_id)s,
        %(intencao)s,
        %(confianca)s,
        %(agente_destino)s,
        'CLASSIFICADO'
    )
    ON CONFLICT (idempotency_key)
    DO NOTHING
    RETURNING id, status_processamento;
    """

    select_evento_sql = """
    SELECT id, 'DUPLICADO' AS status_processamento
    FROM eventos_telegram
    WHERE idempotency_key = %(idempotency_key)s;
    """

    insert_comando_sql = """
    INSERT INTO comandos_executivos (
        id_comando,
        evento_telegram_id,
        tenant_id,
        obra_codigo,
        correlation_id,
        agente_origem,
        agente_destino,
        tipo_comando,
        payload_comando,
        justificativa,
        status,
        requer_aprovacao,
        evidencias
    )
    VALUES (
        %(id_comando)s,
        %(evento_telegram_id)s,
        %(tenant_id)s,
        %(obra_codigo)s,
        %(correlation_id)s,
        'AGENTE_007_ORQUESTRADOR_EXECUTIVO',
        %(agente_destino)s,
        %(tipo_comando)s,
        %(payload_comando)s,
        %(justificativa)s,
        %(status)s,
        %(requer_aprovacao)s,
        '[]'::jsonb
    )
    ON CONFLICT (evento_telegram_id)
    WHERE evento_telegram_id IS NOT NULL
    DO NOTHING
    RETURNING id, id_comando, status;
    """

    select_comando_sql = """
    SELECT id, id_comando, status
    FROM comandos_executivos
    WHERE evento_telegram_id = %(evento_telegram_id)s
    ORDER BY id
    LIMIT 1;
    """

    update_evento_sql = """
    UPDATE eventos_telegram
    SET status_processamento = 'COMANDO_GERADO',
        atualizado_em = NOW()
    WHERE id = %(evento_telegram_id)s
      AND status_processamento <> 'COMANDO_GERADO';
    """

    update_evento_aprovacao_sql = """
    UPDATE eventos_telegram
    SET status_processamento = 'COMANDO_GERADO',
        atualizado_em = NOW()
    WHERE id = %(evento_telegram_id)s
      AND status_processamento <> 'COMANDO_GERADO';
    """

    select_comando_alvo_sql = """
    SELECT id, id_comando, status, tipo_comando, agente_destino
    FROM comandos_executivos
    WHERE (
            %(comando_id)s::bigint IS NOT NULL
            AND id = %(comando_id)s::bigint
        )
       OR (
            %(id_comando)s::uuid IS NOT NULL
            AND id_comando = %(id_comando)s::uuid
        )
    ORDER BY id
    LIMIT 1
    FOR UPDATE;
    """

    update_aprovar_comando_sql = """
    UPDATE comandos_executivos
    SET status = 'APROVADO',
        aprovado_por = %(aprovado_por)s,
        aprovado_em = NOW(),
        resultado = %(resultado)s,
        evidencias = COALESCE(evidencias, '[]'::jsonb) || %(evidencia)s::jsonb,
        mensagem_erro = NULL,
        atualizado_em = NOW()
    WHERE id = %(id)s
      AND status = 'AGUARDANDO_APROVACAO'
    RETURNING id, id_comando, status, tipo_comando, agente_destino;
    """

    update_cancelar_comando_sql = """
    UPDATE comandos_executivos
    SET status = 'CANCELADO',
        resultado = %(resultado)s,
        evidencias = COALESCE(evidencias, '[]'::jsonb) || %(evidencia)s::jsonb,
        mensagem_erro = NULL,
        atualizado_em = NOW()
    WHERE id = %(id)s
      AND status = 'AGUARDANDO_APROVACAO'
    RETURNING id, id_comando, status, tipo_comando, agente_destino;
    """

    evento_row = None
    comando_row = None
    evento_duplicado = False

    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    insert_evento_sql,
                    {
                        "tenant_id": normalized["tenant_id"],
                        "obra_codigo": normalized["obra_codigo"],
                        "telegram_update_id": normalized["telegram_update_id"],
                        "telegram_message_id": normalized["telegram_message_id"],
                        "telegram_user_id": normalized["telegram_user_id"],
                        "telegram_username": normalized["telegram_username"],
                        "chat_id": normalized["chat_id"],
                        "chat_type": normalized["chat_type"],
                        "remetente_nome": normalized["remetente_nome"],
                        "remetente_identificador": normalized["remetente_identificador"],
                        "usuario_autorizado": normalized["usuario_autorizado"],
                        "motivo_autorizacao": normalized["motivo_autorizacao"],
                        "tipo_mensagem": normalized["tipo_mensagem"],
                        "conteudo": normalized["conteudo"],
                        "anexos": Json(normalized["anexos"]),
                        "payload_original": Json(raw_payload),
                        "payload_normalizado": Json(normalized),
                        "payload_hash": payload_hash,
                        "idempotency_key": idempotency_key,
                        "correlation_id": correlation_id,
                        "intencao": classificacao["intencao"],
                        "confianca": classificacao["confianca"],
                        "agente_destino": classificacao["agente_destino"],
                    },
                )
                evento_row = cur.fetchone()

                if evento_row is None:
                    cur.execute(
                        select_evento_sql,
                        {"idempotency_key": idempotency_key},
                    )
                    evento_row = cur.fetchone()
                    evento_duplicado = True

                if evento_row is None:
                    raise RuntimeError("Evento Telegram não foi registrado nem recuperado.")

                evento_id = evento_row[0]

                if instrucao_aprovacao and usuario_autorizado:
                    cur.execute(
                        select_comando_alvo_sql,
                        {
                            "comando_id": instrucao_aprovacao["comando_id"],
                            "id_comando": instrucao_aprovacao["id_comando"],
                        },
                    )
                    comando_alvo_row = cur.fetchone()

                    if comando_alvo_row is None:
                        mensagem_resposta_executiva = (
                            f"Comando {instrucao_aprovacao['identificador']} não encontrado. "
                            "Nenhuma ação externa foi executada."
                        )
                        cur.execute(
                            update_evento_aprovacao_sql,
                            {"evento_telegram_id": evento_id},
                        )
                        conn.commit()
                        return {
                            "ok": True,
                            "evento_telegram_id": evento_row[0],
                            "status_recebimento": evento_row[1],
                            "status_evento": "COMANDO_GERADO",
                            "evento_duplicado": evento_duplicado,
                            "comando_executivo_id": None,
                            "id_comando": None,
                            "status_comando": None,
                            "tenant_id": normalized["tenant_id"],
                            "obra_codigo": normalized["obra_codigo"],
                            "correlation_id": correlation_id,
                            "idempotency_key": idempotency_key,
                            "usuario_autorizado": usuario_autorizado,
                            "motivo_autorizacao": motivo_autorizacao,
                            "intencao": classificacao["intencao"],
                            "confianca": classificacao["confianca"],
                            "agente_origem": "AGENTE_007_ORQUESTRADOR_EXECUTIVO",
                            "agente_destino": classificacao["agente_destino"],
                            "tipo_comando": classificacao["tipo_comando"],
                            "requer_aprovacao": classificacao["requer_aprovacao"],
                            "telegram_chat_id": normalized["chat_id"],
                            "telegram_user_id": normalized["telegram_user_id"],
                            "telegram_message_id": normalized["telegram_message_id"],
                            "mensagem_resposta_executiva": mensagem_resposta_executiva,
                            "acoes_externas_executadas": False,
                            "next_action": "NENHUMA_ACAO_EXTERNA_EXECUTADA",
                            "message": mensagem_resposta_executiva,
                        }

                    status_atual = comando_alvo_row[2]
                    if status_atual != "AGUARDANDO_APROVACAO":
                        mensagem_resposta_executiva = (
                            f"Comando {comando_alvo_row[0]} está com status {status_atual}. "
                            "Nenhuma alteração foi feita."
                        )
                        cur.execute(
                            update_evento_aprovacao_sql,
                            {"evento_telegram_id": evento_id},
                        )
                        conn.commit()
                        return {
                            "ok": True,
                            "evento_telegram_id": evento_row[0],
                            "status_recebimento": evento_row[1],
                            "status_evento": "COMANDO_GERADO",
                            "evento_duplicado": evento_duplicado,
                            "comando_executivo_id": comando_alvo_row[0],
                            "id_comando": str(comando_alvo_row[1]),
                            "status_comando": status_atual,
                            "tenant_id": normalized["tenant_id"],
                            "obra_codigo": normalized["obra_codigo"],
                            "correlation_id": correlation_id,
                            "idempotency_key": idempotency_key,
                            "usuario_autorizado": usuario_autorizado,
                            "motivo_autorizacao": motivo_autorizacao,
                            "intencao": classificacao["intencao"],
                            "confianca": classificacao["confianca"],
                            "agente_origem": "AGENTE_007_ORQUESTRADOR_EXECUTIVO",
                            "agente_destino": comando_alvo_row[4],
                            "tipo_comando": comando_alvo_row[3],
                            "requer_aprovacao": False,
                            "telegram_chat_id": normalized["chat_id"],
                            "telegram_user_id": normalized["telegram_user_id"],
                            "telegram_message_id": normalized["telegram_message_id"],
                            "mensagem_resposta_executiva": mensagem_resposta_executiva,
                            "acoes_externas_executadas": False,
                            "next_action": "NENHUMA_ACAO_EXTERNA_EXECUTADA",
                            "message": mensagem_resposta_executiva,
                        }

                    auditoria = {
                        "tipo_evento": "APROVACAO_EXECUTIVA_TELEGRAM"
                        if instrucao_aprovacao["acao"] == "APROVAR"
                        else "CANCELAMENTO_EXECUTIVO_TELEGRAM",
                        "acao": instrucao_aprovacao["acao"],
                        "agente": "AGENTE_007_ORQUESTRADOR_EXECUTIVO",
                        "evento_telegram_id": evento_id,
                        "telegram_user_id": normalized["telegram_user_id"],
                        "telegram_chat_id": normalized["chat_id"],
                        "telegram_message_id": normalized["telegram_message_id"],
                        "correlation_id": correlation_id,
                        "registrado_em": datetime.now(timezone.utc).isoformat(),
                        "acoes_externas_executadas": False,
                    }
                    resultado_aprovacao = {
                        "tipo_resultado": "COMANDO_EXECUTIVO_APROVADO"
                        if instrucao_aprovacao["acao"] == "APROVAR"
                        else "COMANDO_EXECUTIVO_CANCELADO",
                        "auditoria": auditoria,
                        "controles_operacionais": {
                            "executou_acao_externa": False,
                            "gerou_pdf_real": False,
                            "imprimiu": False,
                            "alterou_rdo_oficial": False,
                            "executou_rpa": False,
                            "conectou_openclaw": False,
                            "enviou_mensagem_terceiros": False,
                        },
                    }
                    update_sql = (
                        update_aprovar_comando_sql
                        if instrucao_aprovacao["acao"] == "APROVAR"
                        else update_cancelar_comando_sql
                    )
                    cur.execute(
                        update_sql,
                        {
                            "id": comando_alvo_row[0],
                            "aprovado_por": normalized["telegram_user_id"]
                            or normalized["remetente_identificador"]
                            or normalized["chat_id"],
                            "resultado": Json(resultado_aprovacao),
                            "evidencia": Json([auditoria]),
                        },
                    )
                    comando_atualizado_row = cur.fetchone()
                    if comando_atualizado_row is None:
                        raise RuntimeError("Comando alvo não foi atualizado.")

                    cur.execute(
                        update_evento_aprovacao_sql,
                        {"evento_telegram_id": evento_id},
                    )
                    mensagem_resposta_executiva = (
                        f"Comando {comando_atualizado_row[0]} aprovado. "
                        "Nenhuma ação externa foi executada."
                        if instrucao_aprovacao["acao"] == "APROVAR"
                        else f"Comando {comando_atualizado_row[0]} cancelado. "
                        "Nenhuma ação externa foi executada."
                    )
                    conn.commit()
                    return {
                        "ok": True,
                        "evento_telegram_id": evento_row[0],
                        "status_recebimento": evento_row[1],
                        "status_evento": "COMANDO_GERADO",
                        "evento_duplicado": evento_duplicado,
                        "comando_executivo_id": comando_atualizado_row[0],
                        "id_comando": str(comando_atualizado_row[1]),
                        "status_comando": comando_atualizado_row[2],
                        "tenant_id": normalized["tenant_id"],
                        "obra_codigo": normalized["obra_codigo"],
                        "correlation_id": correlation_id,
                        "idempotency_key": idempotency_key,
                        "usuario_autorizado": usuario_autorizado,
                        "motivo_autorizacao": motivo_autorizacao,
                        "intencao": classificacao["intencao"],
                        "confianca": classificacao["confianca"],
                        "agente_origem": "AGENTE_007_ORQUESTRADOR_EXECUTIVO",
                        "agente_destino": comando_atualizado_row[4],
                        "tipo_comando": comando_atualizado_row[3],
                        "requer_aprovacao": False,
                        "telegram_chat_id": normalized["chat_id"],
                        "telegram_user_id": normalized["telegram_user_id"],
                        "telegram_message_id": normalized["telegram_message_id"],
                        "mensagem_resposta_executiva": mensagem_resposta_executiva,
                        "acoes_externas_executadas": False,
                        "next_action": "COMANDO_ATUALIZADO_SEM_EXECUCAO_EXTERNA",
                        "message": mensagem_resposta_executiva,
                    }

                payload_comando = {
                    "modo": "curl_local_sem_integracoes_externas",
                    "proibicoes": [
                        "nao_conectar_telegram_real",
                        "nao_usar_openclaw",
                        "nao_executar_rpa",
                        "nao_imprimir",
                        "nao_gerar_pdf_real",
                        "nao_alterar_rdo_oficial",
                    ],
                    "entrada": normalized,
                    "classificacao": classificacao,
                }

                cur.execute(
                    insert_comando_sql,
                    {
                        "id_comando": str(uuid.uuid4()),
                        "evento_telegram_id": evento_id,
                        "tenant_id": normalized["tenant_id"],
                        "obra_codigo": normalized["obra_codigo"],
                        "correlation_id": correlation_id,
                        "agente_destino": classificacao["agente_destino"],
                        "tipo_comando": classificacao["tipo_comando"],
                        "payload_comando": Json(payload_comando),
                        "justificativa": classificacao["justificativa"],
                        "status": status_comando,
                        "requer_aprovacao": classificacao["requer_aprovacao"],
                    },
                )
                comando_row = cur.fetchone()

                if comando_row is None:
                    cur.execute(
                        select_comando_sql,
                        {"evento_telegram_id": evento_id},
                    )
                    comando_row = cur.fetchone()

                cur.execute(
                    update_evento_sql,
                    {"evento_telegram_id": evento_id},
                )

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
                "message": "Erro ao registrar entrada Telegram e comando executivo.",
                "error": str(exc),
                "idempotency_key": idempotency_key,
            },
        )

    if comando_row is None:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Falha ao registrar ou recuperar comando executivo.",
                "idempotency_key": idempotency_key,
            },
        )

    mensagem_resposta_executiva = None
    if not usuario_autorizado:
        mensagem_resposta_executiva = (
            "Usuário não autorizado para comandos executivos. "
            "Solicitação registrada para auditoria; nenhum comando foi alterado."
        )

    return {
        "ok": True,
        "evento_telegram_id": evento_row[0],
        "status_recebimento": evento_row[1],
        "status_evento": "COMANDO_GERADO",
        "evento_duplicado": evento_duplicado,
        "comando_executivo_id": comando_row[0],
        "id_comando": str(comando_row[1]),
        "status_comando": comando_row[2],
        "tenant_id": normalized["tenant_id"],
        "obra_codigo": normalized["obra_codigo"],
        "correlation_id": correlation_id,
        "idempotency_key": idempotency_key,
        "usuario_autorizado": usuario_autorizado,
        "motivo_autorizacao": motivo_autorizacao,
        "intencao": classificacao["intencao"],
        "confianca": classificacao["confianca"],
        "agente_origem": "AGENTE_007_ORQUESTRADOR_EXECUTIVO",
        "agente_destino": classificacao["agente_destino"],
        "tipo_comando": classificacao["tipo_comando"],
        "requer_aprovacao": classificacao["requer_aprovacao"],
        "telegram_chat_id": normalized["chat_id"],
        "telegram_user_id": normalized["telegram_user_id"],
        "telegram_message_id": normalized["telegram_message_id"],
        "mensagem_resposta_executiva": mensagem_resposta_executiva,
        "acoes_externas_executadas": False,
        "next_action": "COMANDO_AUDITAVEL_REGISTRADO_SEM_EXECUCAO_EXTERNA",
        "message": "Entrada Telegram registrada e classificada sem integrações externas.",
    }


@app.post("/agentes/rdo/processar-comando")
async def processar_comando_agente_rdo(
    payload: Optional[ProcessarComandoRDORequest] = None,
):
    id_comando = payload.id_comando if payload else None
    if id_comando:
        try:
            id_comando = str(uuid.UUID(id_comando))
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "id_comando inválido. Use um UUID válido.",
                    "error": str(exc),
                },
            )

    select_comando_sql = """
    SELECT
        ce.id,
        ce.id_comando,
        ce.tenant_id,
        ce.obra_codigo,
        ce.correlation_id,
        ce.agente_origem,
        ce.agente_destino,
        ce.tipo_comando,
        ce.payload_comando,
        ce.status,
        ce.requer_aprovacao,
        et.chat_id,
        et.telegram_user_id,
        et.telegram_message_id
    FROM comandos_executivos AS ce
    LEFT JOIN eventos_telegram AS et
        ON et.id = ce.evento_telegram_id
    WHERE ce.agente_destino = 'AGENTE_RDO'
      AND ce.status = 'PENDENTE'
      AND (%(id_comando)s::uuid IS NULL OR ce.id_comando = %(id_comando)s::uuid)
    ORDER BY ce.criado_em
    LIMIT 1
    FOR UPDATE OF ce;
    """

    update_resultado_sql = """
    UPDATE comandos_executivos
    SET resultado = %(resultado)s,
        executado_por = 'AGENTE_002_GERADOR_RDO',
        executado_em = NOW(),
        mensagem_erro = NULL,
        atualizado_em = NOW()
    WHERE id = %(id)s
      AND status = 'PENDENTE'
    RETURNING id;
    """

    update_status_sql = """
    UPDATE comandos_executivos
    SET status = 'CONCLUIDO',
        atualizado_em = NOW()
    WHERE id = %(id)s
      AND status = 'PENDENTE'
      AND resultado IS NOT NULL
    RETURNING id, id_comando, status, resultado;
    """

    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(select_comando_sql, {"id_comando": id_comando})
                row = cur.fetchone()

                if row is None:
                    conn.rollback()
                    return {
                        "ok": True,
                        "processado": False,
                        "agente_destino": "AGENTE_RDO",
                        "message": "Nenhum comando PENDENTE para AGENTE_RDO encontrado.",
                    }

                comando = {
                    "id": row[0],
                    "id_comando": row[1],
                    "tenant_id": row[2],
                    "obra_codigo": row[3],
                    "correlation_id": row[4],
                    "agente_origem": row[5],
                    "agente_destino": row[6],
                    "tipo_comando": row[7],
                    "payload_comando": row[8],
                    "status": row[9],
                    "requer_aprovacao": row[10],
                    "telegram_chat_id": row[11],
                    "telegram_user_id": row[12],
                    "telegram_message_id": row[13],
                }

                pendencias = listar_pendencias_rdo(conn, comando["obra_codigo"])
                eventos = listar_eventos_rdo(conn, comando["obra_codigo"])
                resultado = montar_resultado_agente_rdo(comando, pendencias, eventos)

                cur.execute(
                    update_resultado_sql,
                    {
                        "id": comando["id"],
                        "resultado": Json(resultado),
                    },
                )
                resultado_row = cur.fetchone()
                if resultado_row is None:
                    raise RuntimeError("Resultado do comando RDO não foi salvo.")

                cur.execute(update_status_sql, {"id": comando["id"]})
                concluido_row = cur.fetchone()
                if concluido_row is None:
                    raise RuntimeError("Status do comando RDO não foi atualizado para CONCLUIDO.")

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
                "message": "Erro ao processar comando executivo do Agente RDO.",
                "error": str(exc),
            },
        )

    return {
        "ok": True,
        "processado": True,
        "comando_executivo_id": concluido_row[0],
        "id_comando": str(concluido_row[1]),
        "status_comando": concluido_row[2],
        "tipo_resultado": concluido_row[3].get("tipo_resultado"),
        "agente_destino": "AGENTE_RDO",
        "agente_processador": "AGENTE_002_GERADOR_RDO",
        "telegram_chat_id": comando["telegram_chat_id"],
        "telegram_user_id": comando["telegram_user_id"],
        "telegram_message_id": comando["telegram_message_id"],
        "mensagem_resposta_executiva": montar_mensagem_resposta_executiva_rdo(
            comando["obra_codigo"],
            concluido_row[3].get("tipo_resultado"),
        ),
        "acoes_externas_executadas": False,
        "message": "Comando AGENTE_RDO processado sem ações externas.",
    }


@app.post("/agentes/comunicacao-obra/processar-comando")
async def processar_comando_agente_comunicacao_obra(
    payload: Optional[ProcessarComandoComunicacaoObraRequest] = None,
):
    id_comando = payload.id_comando if payload else None
    if id_comando:
        try:
            id_comando = str(uuid.UUID(id_comando))
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "id_comando inválido. Use um UUID válido.",
                    "error": str(exc),
                },
            )

    select_comando_sql = """
    SELECT
        ce.id,
        ce.id_comando,
        ce.tenant_id,
        ce.obra_codigo,
        ce.correlation_id,
        ce.agente_origem,
        ce.agente_destino,
        ce.tipo_comando,
        ce.payload_comando,
        ce.status,
        ce.requer_aprovacao,
        et.chat_id,
        et.telegram_user_id,
        et.telegram_message_id
    FROM comandos_executivos AS ce
    LEFT JOIN eventos_telegram AS et
        ON et.id = ce.evento_telegram_id
    WHERE ce.agente_destino = 'AGENTE_006_COMUNICACAO_VISUAL_OBRA'
      AND ce.tipo_comando = 'PREPARAR_PLACA_AVISO'
      AND ce.status = 'PENDENTE'
      AND (%(id_comando)s::uuid IS NULL OR ce.id_comando = %(id_comando)s::uuid)
    ORDER BY ce.criado_em
    LIMIT 1
    FOR UPDATE OF ce;
    """

    update_resultado_sql = """
    UPDATE comandos_executivos
    SET resultado = %(resultado)s,
        executado_por = 'AGENTE_006_COMUNICACAO_VISUAL_OBRA',
        executado_em = NOW(),
        mensagem_erro = NULL,
        atualizado_em = NOW()
    WHERE id = %(id)s
      AND status = 'PENDENTE'
      AND tipo_comando = 'PREPARAR_PLACA_AVISO'
    RETURNING id;
    """

    update_status_sql = """
    UPDATE comandos_executivos
    SET status = 'CONCLUIDO',
        atualizado_em = NOW()
    WHERE id = %(id)s
      AND status = 'PENDENTE'
      AND tipo_comando = 'PREPARAR_PLACA_AVISO'
      AND resultado IS NOT NULL
    RETURNING id, id_comando, status, resultado;
    """

    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(select_comando_sql, {"id_comando": id_comando})
                row = cur.fetchone()

                if row is None:
                    conn.rollback()
                    return {
                        "ok": True,
                        "processado": False,
                        "agente_destino": "AGENTE_006_COMUNICACAO_VISUAL_OBRA",
                        "message": (
                            "Nenhum comando PENDENTE PREPARAR_PLACA_AVISO para "
                            "AGENTE_006_COMUNICACAO_VISUAL_OBRA encontrado."
                        ),
                    }

                comando = {
                    "id": row[0],
                    "id_comando": row[1],
                    "tenant_id": row[2],
                    "obra_codigo": row[3],
                    "correlation_id": row[4],
                    "agente_origem": row[5],
                    "agente_destino": row[6],
                    "tipo_comando": row[7],
                    "payload_comando": row[8],
                    "status": row[9],
                    "requer_aprovacao": row[10],
                    "telegram_chat_id": row[11],
                    "telegram_user_id": row[12],
                    "telegram_message_id": row[13],
                }

                resultado = montar_resultado_agente_comunicacao_obra(comando)

                cur.execute(
                    update_resultado_sql,
                    {
                        "id": comando["id"],
                        "resultado": Json(resultado),
                    },
                )
                resultado_row = cur.fetchone()
                if resultado_row is None:
                    raise RuntimeError("Resultado do comando de comunicação visual não foi salvo.")

                cur.execute(update_status_sql, {"id": comando["id"]})
                concluido_row = cur.fetchone()
                if concluido_row is None:
                    raise RuntimeError(
                        "Status do comando de comunicação visual não foi atualizado para CONCLUIDO."
                    )

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
                "message": "Erro ao processar comando executivo do Agente 006 Comunicação Visual.",
                "error": str(exc),
            },
        )

    return {
        "ok": True,
        "processado": True,
        "comando_executivo_id": concluido_row[0],
        "id_comando": str(concluido_row[1]),
        "status_comando": concluido_row[2],
        "tipo_resultado": concluido_row[3].get("tipo_resultado"),
        "agente_destino": "AGENTE_006_COMUNICACAO_VISUAL_OBRA",
        "agente_processador": "AGENTE_006_COMUNICACAO_VISUAL_OBRA",
        "telegram_chat_id": comando["telegram_chat_id"],
        "telegram_user_id": comando["telegram_user_id"],
        "telegram_message_id": comando["telegram_message_id"],
        "mensagem_resposta_executiva": montar_mensagem_resposta_executiva_comunicacao_obra(
            comando["obra_codigo"],
            concluido_row[3].get("tipo_resultado"),
        ),
        "acoes_externas_executadas": False,
        "message": "Comando AGENTE_006_COMUNICACAO_VISUAL_OBRA processado sem ações externas.",
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


# -----------------------------------------------------------------------------
# Document upload / MinIO
# -----------------------------------------------------------------------------

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_DEFAULT_BUCKET = os.getenv("MINIO_DEFAULT_BUCKET", "obra-caio")


def get_minio_client() -> Minio:
    if not MINIO_ACCESS_KEY or not MINIO_SECRET_KEY:
        raise RuntimeError("Credenciais MinIO não definidas.")

    parsed = urlparse(MINIO_ENDPOINT)

    if parsed.scheme:
        endpoint = parsed.netloc
        secure = parsed.scheme == "https"
    else:
        endpoint = MINIO_ENDPOINT.replace("http://", "").replace("https://", "")
        secure = False

    return Minio(
        endpoint,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=secure,
    )


def sanitize_filename(filename: str | None) -> str:
    name = Path(filename or "anexo.bin").name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name or "anexo.bin"


def ensure_documentos_table() -> None:
    sql = """
    CREATE TABLE IF NOT EXISTS arquivos_obra (
        id SERIAL PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        obra_codigo TEXT NOT NULL,
        mensagem_id INTEGER,
        canal_origem TEXT,
        remetente_identificador TEXT,
        origem_id TEXT,
        tipo_documento TEXT,
        file_name TEXT,
        mimetype TEXT,
        storage_provider TEXT DEFAULT 'minio',
        bucket TEXT NOT NULL,
        object_key TEXT NOT NULL,
        tamanho_bytes INTEGER,
        hash_arquivo TEXT,
        status_processamento TEXT DEFAULT 'ARMAZENADO',
        payload_metadata JSONB,
        criado_em TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_arquivos_obra_codigo
        ON arquivos_obra (obra_codigo);

    CREATE INDEX IF NOT EXISTS idx_arquivos_mensagem_id
        ON arquivos_obra (mensagem_id);

    CREATE INDEX IF NOT EXISTS idx_arquivos_hash
        ON arquivos_obra (hash_arquivo);
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


@app.post("/documentos/upload")
async def upload_documento(
    file: UploadFile = File(...),
    tenant_id: str = Form(default="construtora-piloto"),
    obra_codigo: str = Form(default="OBRA-CAIO"),
    canal_origem: str = Form(default="desconhecido"),
    mensagem_id: Optional[int] = Form(default=None),
    remetente_identificador: Optional[str] = Form(default=None),
    origem_id: Optional[str] = Form(default=None),
    tipo_documento: Optional[str] = Form(default=None),
):
    ensure_documentos_table()

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail={"message": "Arquivo vazio ou não recebido."},
        )

    file_hash = hashlib.sha256(content).hexdigest()
    file_size = len(content)
    safe_name = sanitize_filename(file.filename)
    mimetype = file.content_type or "application/octet-stream"

    bucket = MINIO_DEFAULT_BUCKET
    date_path = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    object_key = (
        f"{tenant_id}/{obra_codigo}/{canal_origem}/"
        f"{date_path}/{file_hash[:12]}_{safe_name}"
    )

    try:
        client = get_minio_client()

        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)

        client.put_object(
            bucket_name=bucket,
            object_name=object_key,
            data=BytesIO(content),
            length=file_size,
            content_type=mimetype,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Erro ao salvar arquivo no MinIO.",
                "error": str(exc),
                "bucket": bucket,
                "object_key": object_key,
            },
        )

    insert_sql = """
    INSERT INTO arquivos_obra (
        tenant_id,
        obra_codigo,
        mensagem_id,
        canal_origem,
        remetente_identificador,
        origem_id,
        tipo_documento,
        file_name,
        mimetype,
        storage_provider,
        bucket,
        object_key,
        tamanho_bytes,
        hash_arquivo,
        status_processamento,
        payload_metadata
    )
    VALUES (
        %(tenant_id)s,
        %(obra_codigo)s,
        %(mensagem_id)s,
        %(canal_origem)s,
        %(remetente_identificador)s,
        %(origem_id)s,
        %(tipo_documento)s,
        %(file_name)s,
        %(mimetype)s,
        'minio',
        %(bucket)s,
        %(object_key)s,
        %(tamanho_bytes)s,
        %(hash_arquivo)s,
        'ARMAZENADO',
        %(payload_metadata)s
    )
    RETURNING id;
    """

    metadata = {
        "original_filename": file.filename,
        "content_type": mimetype,
        "hash_sha256": file_hash,
    }

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    insert_sql,
                    {
                        "tenant_id": tenant_id,
                        "obra_codigo": obra_codigo,
                        "mensagem_id": mensagem_id,
                        "canal_origem": canal_origem,
                        "remetente_identificador": remetente_identificador,
                        "origem_id": origem_id,
                        "tipo_documento": tipo_documento,
                        "file_name": safe_name,
                        "mimetype": mimetype,
                        "bucket": bucket,
                        "object_key": object_key,
                        "tamanho_bytes": file_size,
                        "hash_arquivo": file_hash,
                        "payload_metadata": Json(metadata),
                    },
                )
                row = cur.fetchone()
            conn.commit()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Arquivo salvo no MinIO, mas houve erro ao registrar no banco.",
                "error": str(exc),
                "bucket": bucket,
                "object_key": object_key,
            },
        )

    documento_id = row[0]

    return {
        "ok": True,
        "documento_id": documento_id,
        "tenant_id": tenant_id,
        "obra_codigo": obra_codigo,
        "mensagem_id": mensagem_id,
        "anexo": {
            "documento_id": documento_id,
            "tipo": tipo_documento or "documento",
            "file_name": safe_name,
            "mimetype": mimetype,
            "storage_provider": "minio",
            "bucket": bucket,
            "object_key": object_key,
            "tamanho_bytes": file_size,
            "hash_arquivo": file_hash,
            "status_processamento": "ARMAZENADO",
        },
    }
