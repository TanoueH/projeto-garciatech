#!/usr/bin/env python3
"""Executa continuamente a captura e o processamento do Telegram."""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError

from scripts.telegram.capturar_updates_telegram import (
    DEFAULT_OFFSET_FILE,
    buscar_updates,
    carregar_offset,
    maior_update_id,
    normalizar_update,
    post_json,
    salvar_offset,
)
from scripts.telegram.processar_gestao_operacional_pendente_e_responder import (
    enviar_mensagem_telegram,
)


DEFAULT_API_CORE_URL = "http://api_core:8000/telegram/entrada"
DEFAULT_PROCESSAR_URL = (
    "http://api_core:8000/agentes/gestao-operacional/processar-comando"
)
DEFAULT_BRIEFING_URL = (
    "http://api_core:8000/agentes/gestao-operacional/briefing-diario-agendado"
)
DEFAULT_BRIEFING_CONFIRM_URL = f"{DEFAULT_BRIEFING_URL}/confirmar-envio"
DEFAULT_INTERVAL_SECONDS = 5.0
BRIEFING_CHECK_INTERVAL_SECONDS = 60.0
_briefings_enviados_aguardando_confirmacao: dict[int, str] = {}


def log_json(evento: str, **campos: Any) -> None:
    print(
        json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "evento": evento,
                **campos,
            },
            ensure_ascii=False,
            default=str,
        ),
        flush=True,
    )


def carregar_intervalo() -> float:
    valor = os.getenv(
        "TELEGRAM_WORKER_INTERVAL_SECONDS",
        str(DEFAULT_INTERVAL_SECONDS),
    )
    try:
        intervalo = float(valor)
    except ValueError:
        log_json(
            "configuracao_intervalo_invalida",
            valor=valor,
            intervalo_aplicado=DEFAULT_INTERVAL_SECONDS,
        )
        return DEFAULT_INTERVAL_SECONDS

    if intervalo <= 0:
        log_json(
            "configuracao_intervalo_invalida",
            valor=valor,
            intervalo_aplicado=DEFAULT_INTERVAL_SECONDS,
        )
        return DEFAULT_INTERVAL_SECONDS
    return intervalo


def capturar_e_encaminhar(token: str, api_core_url: str) -> dict[str, int | None]:
    offset = carregar_offset(DEFAULT_OFFSET_FILE)
    updates = buscar_updates(token, limit=None, offset=offset)
    enviados = 0
    falhas = 0
    ignorados = 0

    for update in updates:
        payload = normalizar_update(update)
        if payload is None:
            ignorados += 1
            continue

        try:
            status_code, body = post_json(
                api_core_url,
                payload,
                headers={"X-Correlation-Id": str(uuid.uuid4())},
            )
            if 200 <= status_code < 300 and body.get("ok") is True:
                enviados += 1
                resposta_direta = body.get("resposta_telegram")
                chat_id = payload.get("chat_id")
                if resposta_direta and chat_id:
                    enviar_mensagem_telegram(token, str(chat_id), str(resposta_direta))
            else:
                falhas += 1
                log_json(
                    "telegram_update_rejeitado_api_core",
                    telegram_update_id=payload.get("telegram_update_id"),
                    http_status=status_code,
                    resposta_api=body,
                )
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            falhas += 1
            log_json(
                "telegram_update_erro_api_core",
                telegram_update_id=payload.get("telegram_update_id"),
                erro_tipo=type(exc).__name__,
                erro=str(exc),
            )

    next_offset = None
    max_update_id = maior_update_id(updates)
    if falhas == 0 and max_update_id is not None:
        next_offset = max_update_id + 1
        salvar_offset(DEFAULT_OFFSET_FILE, next_offset)

    return {
        "updates_recebidos": len(updates),
        "updates_enviados": enviados,
        "updates_ignorados": ignorados,
        "updates_com_falha": falhas,
        "next_offset_salvo": next_offset,
    }


def processar_e_responder(token: str, processar_url: str) -> dict[str, Any]:
    status_code, body = post_json(processar_url, {})
    if not 200 <= status_code < 300:
        return {
            "status": "ERRO_API_CORE",
            "http_status": status_code,
            "resposta_api": body,
        }

    if body.get("status") == "SEM_COMANDO_PENDENTE":
        return {"status": "SEM_COMANDO_PENDENTE"}

    resposta = body.get("resposta_telegram")
    chat_id = body.get("telegram_chat_id") or os.getenv(
        "TELEGRAM_EXECUTIVE_CHAT_ID"
    )
    if not resposta or not chat_id:
        return {
            "status": "RESPOSTA_NAO_ENVIADA",
            "id_comando": body.get("id_comando"),
            "erro": "resposta_telegram ou chat_id não disponível.",
        }

    envio = enviar_mensagem_telegram(token, str(chat_id), str(resposta))
    return {
        "status": "RESPOSTA_ENVIADA",
        "id_comando": body.get("id_comando"),
        "status_comando": body.get("status_comando"),
        "telegram": envio,
    }


def confirmar_briefing(
    confirmar_url: str,
    envio_id: int,
    status: str,
    telegram_message_id: str | None = None,
    mensagem_erro: str | None = None,
) -> dict[str, Any]:
    status_code, body = post_json(
        confirmar_url,
        {
            "envio_id": envio_id,
            "telegram_message_id": telegram_message_id,
            "status": status,
            "mensagem_erro": mensagem_erro,
        },
    )
    if not 200 <= status_code < 300:
        raise RuntimeError(f"Confirmação do briefing falhou com HTTP {status_code}.")
    return body


def processar_briefing_agendado(
    token: str,
    briefing_url: str,
    confirmar_url: str,
) -> dict[str, Any]:
    status_code, body = post_json(briefing_url, {"forcar": False})
    if not 200 <= status_code < 300:
        raise RuntimeError(f"Agendamento do briefing falhou com HTTP {status_code}.")

    status = str(body.get("status") or "ERRO")
    eventos_sem_envio = {
        "DESABILITADO": "briefing_agendado_desabilitado",
        "FORA_DO_HORARIO": "briefing_agendado_fora_do_horario",
        "JA_ENVIADO": "briefing_agendado_ja_enviado",
    }
    if status in eventos_sem_envio:
        log_json(eventos_sem_envio[status], status=status, envio_id=body.get("envio_id"))
        return {"status": status, "envio_id": body.get("envio_id")}

    envio_id = body.get("envio_id")
    chat_id = body.get("chat_id")
    resposta = body.get("resposta_telegram")
    if not body.get("deve_enviar_telegram") or not envio_id or not chat_id or not resposta:
        if status not in {"CHAT_EXECUTIVO_NAO_CONFIGURADO", "CONFIGURACAO_INVALIDA"}:
            return {"status": status}
        log_json("briefing_agendado_erro", status=status, envio_id=envio_id)
        return {"status": status}

    envio_id = int(envio_id)
    message_id_pendente = _briefings_enviados_aguardando_confirmacao.get(envio_id)
    if message_id_pendente is not None:
        try:
            confirmacao = confirmar_briefing(
                confirmar_url,
                envio_id,
                "CONCLUIDO",
                telegram_message_id=message_id_pendente,
                mensagem_erro=None,
            )
            if confirmacao.get("status") != "CONCLUIDO":
                raise RuntimeError(
                    "API Core não confirmou status CONCLUIDO para briefing já enviado."
                )
            _briefings_enviados_aguardando_confirmacao.pop(envio_id, None)
            log_json(
                "briefing_agendado_confirmado",
                envio_id=envio_id,
                telegram_message_id=message_id_pendente,
            )
            return {
                "status": "CONCLUIDO",
                "envio_id": envio_id,
                "telegram_message_id": message_id_pendente,
            }
        except Exception as exc:
            erro = f"{type(exc).__name__}: {exc}"
            log_json(
                "briefing_agendado_confirmacao_erro",
                envio_id=envio_id,
                telegram_message_id=message_id_pendente,
                erro=erro,
            )
            return {"status": "ERRO", "envio_id": envio_id, "erro": erro}

    chat_executivo = (os.getenv("TELEGRAM_EXECUTIVE_CHAT_ID") or "").strip()
    if not chat_executivo or str(chat_id) != chat_executivo:
        erro = "chat_id do agendamento não corresponde ao executivo autorizado."
        confirmar_briefing(confirmar_url, int(envio_id), "ERRO", mensagem_erro=erro)
        log_json("briefing_agendado_erro", envio_id=envio_id, erro=erro)
        return {"status": "ERRO", "envio_id": envio_id}

    try:
        envio = enviar_mensagem_telegram(token, str(chat_id), str(resposta))

        telegram_message_id = (
            envio.get("result", {}).get("message_id")
            or envio.get("message_id")
        )

        if telegram_message_id is None:
            raise RuntimeError(f"Telegram não retornou message_id. resposta={envio}")
        telegram_message_id = str(telegram_message_id)
        _briefings_enviados_aguardando_confirmacao[envio_id] = telegram_message_id
        confirmacao = confirmar_briefing(
            confirmar_url,
            envio_id,
            "CONCLUIDO",
            telegram_message_id=telegram_message_id,
            mensagem_erro=None,
        )
        if confirmacao.get("status") != "CONCLUIDO":
            raise RuntimeError(
                "API Core não confirmou status CONCLUIDO após envio do briefing."
            )
        _briefings_enviados_aguardando_confirmacao.pop(envio_id, None)
        log_json(
            "briefing_agendado_enviado",
            envio_id=envio_id,
            telegram_message_id=telegram_message_id,
        )
        return {
            "status": "CONCLUIDO",
            "envio_id": envio_id,
            "telegram_message_id": telegram_message_id,
        }
    except Exception as exc:
        erro = f"{type(exc).__name__}: {exc}"
        if envio_id not in _briefings_enviados_aguardando_confirmacao:
            try:
                confirmar_briefing(
                    confirmar_url,
                    envio_id,
                    "ERRO",
                    mensagem_erro=erro,
                )
            except Exception as confirm_exc:
                erro = f"{erro}; confirmação: {type(confirm_exc).__name__}: {confirm_exc}"
        log_json("briefing_agendado_erro", envio_id=envio_id, erro=erro)
        return {"status": "ERRO", "envio_id": envio_id}


def main() -> int:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        log_json("telegram_worker_nao_iniciado", erro="TELEGRAM_BOT_TOKEN ausente")
        return 2

    api_core_url = os.getenv("TELEGRAM_API_CORE_URL") or DEFAULT_API_CORE_URL
    processar_url = (
        os.getenv("TELEGRAM_GESTAO_PROCESSAR_URL") or DEFAULT_PROCESSAR_URL
    )
    briefing_url = os.getenv("TELEGRAM_DAILY_BRIEFING_URL") or DEFAULT_BRIEFING_URL
    confirmar_briefing_url = (
        os.getenv("TELEGRAM_DAILY_BRIEFING_CONFIRM_URL")
        or DEFAULT_BRIEFING_CONFIRM_URL
    )
    intervalo = carregar_intervalo()
    ciclo = 0
    proxima_verificacao_briefing = 0.0
    log_json(
        "telegram_worker_iniciado",
        api_core_url=api_core_url,
        processar_url=processar_url,
        intervalo_segundos=intervalo,
    )

    while True:
        ciclo += 1
        inicio = time.monotonic()
        resultado_captura: dict[str, Any]
        resultado_processamento: dict[str, Any]
        resultado_briefing: dict[str, Any] = {"status": "NAO_VERIFICADO_NESTE_CICLO"}

        try:
            resultado_captura = capturar_e_encaminhar(token, api_core_url)
        except Exception as exc:
            resultado_captura = {
                "status": "ERRO",
                "erro_tipo": type(exc).__name__,
                "erro": str(exc),
            }

        agora_monotonic = time.monotonic()
        if agora_monotonic >= proxima_verificacao_briefing:
            proxima_verificacao_briefing = agora_monotonic + BRIEFING_CHECK_INTERVAL_SECONDS
            try:
                resultado_briefing = processar_briefing_agendado(
                    token, briefing_url, confirmar_briefing_url
                )
            except Exception as exc:
                resultado_briefing = {
                    "status": "ERRO",
                    "erro_tipo": type(exc).__name__,
                    "erro": str(exc),
                }
                log_json("briefing_agendado_erro", **resultado_briefing)

        try:
            resultado_processamento = processar_e_responder(token, processar_url)
        except Exception as exc:
            resultado_processamento = {
                "status": "ERRO",
                "erro_tipo": type(exc).__name__,
                "erro": str(exc),
            }

        duracao = round(time.monotonic() - inicio, 3)
        log_json(
            "telegram_worker_ciclo_concluido",
            ciclo=ciclo,
            duracao_segundos=duracao,
            captura=resultado_captura,
            processamento=resultado_processamento,
            briefing_agendado=resultado_briefing,
        )
        time.sleep(intervalo)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log_json("telegram_worker_interrompido")
        raise SystemExit(0) from None
