#!/usr/bin/env python3
"""Processa uma consulta documental pendente e responde pelo Telegram."""

from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_PROCESSAR_URL = (
    "http://127.0.0.1:8000/agentes/gestao-operacional/processar-comando"
)
TELEGRAM_API_BASE_URL = "https://api.telegram.org"
REQUEST_TIMEOUT_SECONDS = 20


def post_json(url: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(body) if body else {}
        except json.JSONDecodeError:
            return exc.code, {"error": body}


def enviar_mensagem_telegram(token: str, chat_id: str, texto: str) -> dict[str, Any]:
    status_code, body = post_json(
        f"{TELEGRAM_API_BASE_URL}/bot{token}/sendMessage",
        {
            "chat_id": chat_id,
            "text": texto,
            "disable_web_page_preview": True,
        },
    )
    if not 200 <= status_code < 300 or body.get("ok") is not True:
        raise RuntimeError(f"Telegram sendMessage falhou com HTTP {status_code}.")
    return {"http_status": status_code, "ok": True}


def imprimir_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def main() -> int:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        imprimir_json(
            {
                "ok": False,
                "status_processamento": "NAO_INICIADO",
                "status_envio_telegram": "NAO_ENVIADO",
                "erro": "TELEGRAM_BOT_TOKEN não definido no ambiente.",
            }
        )
        return 2

    processar_url = os.getenv("TELEGRAM_GESTAO_PROCESSAR_URL", DEFAULT_PROCESSAR_URL)
    try:
        status_code, body = post_json(processar_url, {})
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        imprimir_json(
            {
                "ok": False,
                "status_processamento": "ERRO_API_CORE",
                "status_envio_telegram": "NAO_ENVIADO",
                "erro_tipo": type(exc).__name__,
            }
        )
        return 1

    if not 200 <= status_code < 300:
        imprimir_json(
            {
                "ok": False,
                "status_processamento": "ERRO_API_CORE",
                "http_status": status_code,
                "status_envio_telegram": "NAO_ENVIADO",
                "resposta_api": body,
            }
        )
        return 1

    if body.get("status") == "SEM_COMANDO_PENDENTE":
        imprimir_json(
            {
                **body,
                "status_processamento": "SEM_COMANDO_PENDENTE",
                "status_envio_telegram": "NAO_NECESSARIO",
            }
        )
        return 0

    resposta = body.get("resposta_telegram")
    chat_id = body.get("telegram_chat_id") or os.getenv("TELEGRAM_EXECUTIVE_CHAT_ID")
    if not resposta or not chat_id:
        imprimir_json(
            {
                "ok": False,
                "status_processamento": body.get("status_comando", "CONCLUIDO"),
                "status_envio_telegram": "NAO_ENVIADO",
                "id_comando": body.get("id_comando"),
                "erro": "resposta_telegram ou chat_id não disponível.",
            }
        )
        return 1

    try:
        envio = enviar_mensagem_telegram(str(token), str(chat_id), str(resposta))
    except (URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
        imprimir_json(
            {
                "ok": False,
                "status_processamento": body.get("status_comando"),
                "status_envio_telegram": "ERRO",
                "id_comando": body.get("id_comando"),
                "erro_tipo": type(exc).__name__,
            }
        )
        return 1

    imprimir_json(
        {
            "ok": True,
            "status_processamento": body.get("status_comando"),
            "status_envio_telegram": "ENVIADO",
            "id_comando": body.get("id_comando"),
            "tipo_comando": body.get("tipo_comando"),
            "obra_codigo": body.get("obra_codigo"),
            "telegram": envio,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
