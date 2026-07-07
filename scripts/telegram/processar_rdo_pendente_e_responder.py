#!/usr/bin/env python3
"""Processa um comando RDO pendente e responde ao chat Telegram de origem."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_RDO_PROCESSAR_URL = "http://127.0.0.1:8000/agentes/rdo/processar-comando"
TELEGRAM_API_BASE_URL = "https://api.telegram.org"
REQUEST_TIMEOUT_SECONDS = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Chama /agentes/rdo/processar-comando e, quando houver resposta "
            "executiva, envia sendMessage ao chat Telegram retornado pela API Core."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Processa o comando e mostra o resumo sem enviar mensagem ao Telegram.",
    )
    return parser.parse_args()


def post_json(url: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            response_body = response.read().decode("utf-8")
            parsed_body = json.loads(response_body) if response_body else {}
            return response.status, parsed_body
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed_error = json.loads(error_body) if error_body else {}
        except json.JSONDecodeError:
            parsed_error = {"error": error_body}
        return exc.code, parsed_error


def enviar_mensagem_telegram(token: str, chat_id: str, texto: str) -> None:
    url = f"{TELEGRAM_API_BASE_URL}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "disable_web_page_preview": True,
    }
    status_code, body = post_json(url, payload)
    if status_code < 200 or status_code >= 300 or body.get("ok") is not True:
        raise RuntimeError(f"Telegram sendMessage falhou com HTTP {status_code}.")


def mascarar_identificador(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value)
    if len(text) <= 4:
        return "*" * len(text)

    return f"{text[:2]}***{text[-2:]}"


def imprimir_resumo(body: dict[str, Any], enviado: bool, dry_run: bool) -> None:
    resumo = {
        "comando_executivo_id": body.get("comando_executivo_id"),
        "tipo_resultado": body.get("tipo_resultado"),
        "telegram_chat_id": mascarar_identificador(body.get("telegram_chat_id")),
        "enviado": enviado,
        "dry_run": dry_run,
    }
    print(json.dumps(resumo, ensure_ascii=False))


def main() -> int:
    args = parse_args()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    processar_url = os.getenv("TELEGRAM_RDO_PROCESSAR_URL", DEFAULT_RDO_PROCESSAR_URL)

    if not token and not args.dry_run:
        print("Erro: TELEGRAM_BOT_TOKEN não definido no ambiente.", file=sys.stderr)
        return 2

    try:
        status_code, body = post_json(processar_url, {})
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Erro ao chamar API Core: {type(exc).__name__}.", file=sys.stderr)
        return 1

    if status_code < 200 or status_code >= 300:
        print(f"Erro: API Core retornou HTTP {status_code}.", file=sys.stderr)
        return 1

    if body.get("processado") is not True:
        imprimir_resumo(body, enviado=False, dry_run=args.dry_run)
        return 0

    chat_id = body.get("telegram_chat_id")
    mensagem = body.get("mensagem_resposta_executiva")
    enviado = False

    if chat_id and mensagem:
        if args.dry_run:
            enviado = False
        else:
            try:
                enviar_mensagem_telegram(str(token), str(chat_id), str(mensagem))
            except (URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
                imprimir_resumo(body, enviado=False, dry_run=args.dry_run)
                print(f"Erro ao enviar mensagem Telegram: {type(exc).__name__}.", file=sys.stderr)
                return 1
            enviado = True

    imprimir_resumo(body, enviado=enviado, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
