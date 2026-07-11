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
DEFAULT_INTERVAL_SECONDS = 5.0


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


def main() -> int:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        log_json("telegram_worker_nao_iniciado", erro="TELEGRAM_BOT_TOKEN ausente")
        return 2

    api_core_url = os.getenv("TELEGRAM_API_CORE_URL") or DEFAULT_API_CORE_URL
    processar_url = (
        os.getenv("TELEGRAM_GESTAO_PROCESSAR_URL") or DEFAULT_PROCESSAR_URL
    )
    intervalo = carregar_intervalo()
    ciclo = 0
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

        try:
            resultado_captura = capturar_e_encaminhar(token, api_core_url)
        except Exception as exc:
            resultado_captura = {
                "status": "ERRO",
                "erro_tipo": type(exc).__name__,
                "erro": str(exc),
            }

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
        )
        time.sleep(intervalo)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log_json("telegram_worker_interrompido")
        raise SystemExit(0) from None
