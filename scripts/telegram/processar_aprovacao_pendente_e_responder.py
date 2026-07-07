#!/usr/bin/env python3
"""Processa aprovações/cancelamentos Telegram pendentes e responde ao chat de origem."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

from capturar_updates_telegram import (
    REQUEST_TIMEOUT_SECONDS,
    TELEGRAM_API_BASE_URL,
    buscar_updates,
    carregar_offset,
    maior_update_id,
    normalizar_update,
    post_json,
    resetar_offset,
    salvar_offset,
)


DEFAULT_API_CORE_URL = "http://127.0.0.1:8000/telegram/entrada"
DEFAULT_OFFSET_FILE = Path(".runtime/telegram/agente_007_aprovacoes_offset.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Busca updates Telegram com frases de aprovação/cancelamento, chama "
            "/telegram/entrada e envia apenas a resposta retornada pela API Core "
            "ao telegram_chat_id de origem."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Processa na API Core e mostra resumo sem enviar sendMessage.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Quantidade máxima de updates a consultar/processar nesta execução.",
    )
    parser.add_argument(
        "--reset-offset",
        action="store_true",
        help="Apaga/ignora o offset local antes de consultar getUpdates.",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=None,
        help="Força manualmente o offset enviado ao getUpdates nesta execução.",
    )
    return parser.parse_args()


def parece_aprovacao_ou_cancelamento(texto: Any) -> bool:
    if not isinstance(texto, str):
        return False
    return bool(
        re.search(
            r"\b(aprovar|aprova|autorizar|confirmar|cancelar|cancela|rejeitar)\s+comando\s+[0-9a-fA-F-]+\b",
            texto.lower(),
        )
    )


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


def imprimir_evento(evento: str, payload: dict[str, Any]) -> None:
    print(json.dumps({"evento": evento, **payload}, ensure_ascii=False))


def resumo_api(status_code: int, body: dict[str, Any], enviado: bool, dry_run: bool) -> dict[str, Any]:
    return {
        "http_status": status_code,
        "ok": body.get("ok"),
        "status_evento": body.get("status_evento"),
        "status_comando": body.get("status_comando"),
        "intencao": body.get("intencao"),
        "usuario_autorizado": body.get("usuario_autorizado"),
        "comando_executivo_id": body.get("comando_executivo_id"),
        "telegram_chat_id": mascarar_identificador(body.get("telegram_chat_id")),
        "enviado": enviado,
        "dry_run": dry_run,
        "acoes_externas_executadas": body.get("acoes_externas_executadas"),
    }


def main() -> int:
    args = parse_args()
    if args.limit is not None and args.limit < 1:
        print("Erro: --limit deve ser maior que zero.", file=sys.stderr)
        return 2
    if args.offset is not None and args.offset < 0:
        print("Erro: --offset deve ser maior ou igual a zero.", file=sys.stderr)
        return 2

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Erro: TELEGRAM_BOT_TOKEN não definido no ambiente.", file=sys.stderr)
        return 2

    api_core_url = os.getenv("TELEGRAM_API_CORE_URL", DEFAULT_API_CORE_URL)
    offset_file = DEFAULT_OFFSET_FILE

    if args.reset_offset:
        try:
            resetar_offset(offset_file)
        except OSError as exc:
            print(f"Erro ao resetar offset local: {type(exc).__name__}.", file=sys.stderr)
            return 1

    offset_origem = "manual" if args.offset is not None else "local"
    offset = args.offset if args.offset is not None else carregar_offset(offset_file)
    if offset is None:
        offset_origem = "nenhum"

    try:
        updates = buscar_updates(token, args.limit, offset)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"Erro ao consultar getUpdates: {type(exc).__name__}.", file=sys.stderr)
        return 1

    if args.limit is not None:
        updates = updates[: args.limit]

    imprimir_evento(
        "processamento_aprovacoes_iniciado",
        {
            "updates_recebidos": len(updates),
            "limit": args.limit,
            "offset": offset,
            "offset_origem": offset_origem,
            "offset_file": str(offset_file),
            "api_core_url": api_core_url,
            "timeout_segundos": REQUEST_TIMEOUT_SECONDS,
            "dry_run": args.dry_run,
        },
    )

    processados = 0
    enviados = 0
    falhas = 0
    ignorados = 0

    for update in updates:
        payload = normalizar_update(update)
        if payload is None or not parece_aprovacao_ou_cancelamento(payload.get("conteudo")):
            ignorados += 1
            continue

        processados += 1
        headers = {"X-Correlation-Id": str(uuid.uuid4())}

        try:
            status_code, body = post_json(api_core_url, payload, headers=headers)
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            falhas += 1
            imprimir_evento(
                "envio_api_core_falhou",
                {
                    "telegram_update_id": payload.get("telegram_update_id"),
                    "telegram_message_id": payload.get("telegram_message_id"),
                    "erro_tipo": type(exc).__name__,
                },
            )
            continue

        enviado = False
        chat_id = body.get("telegram_chat_id")
        mensagem = body.get("mensagem_resposta_executiva")

        if 200 <= status_code < 300 and body.get("ok") is True and chat_id and mensagem:
            if args.dry_run:
                enviado = False
            else:
                try:
                    enviar_mensagem_telegram(str(token), str(chat_id), str(mensagem))
                except (URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
                    falhas += 1
                    imprimir_evento(
                        "envio_telegram_falhou",
                        {
                            "telegram_update_id": payload.get("telegram_update_id"),
                            "telegram_message_id": payload.get("telegram_message_id"),
                            "telegram_chat_id": mascarar_identificador(chat_id),
                            "erro_tipo": type(exc).__name__,
                        },
                    )
                    imprimir_evento(
                        "aprovacao_processada",
                        resumo_api(status_code, body, enviado=False, dry_run=args.dry_run),
                    )
                    continue
                enviado = True
                enviados += 1
        elif status_code < 200 or status_code >= 300:
            falhas += 1

        imprimir_evento(
            "aprovacao_processada",
            resumo_api(status_code, body, enviado=enviado, dry_run=args.dry_run),
        )

    max_update_id = maior_update_id(updates)
    next_offset = max_update_id + 1 if max_update_id is not None else None
    next_offset_salvo = None
    if falhas == 0 and next_offset is not None:
        try:
            salvar_offset(offset_file, next_offset)
        except OSError as exc:
            print(f"Erro ao salvar offset local: {type(exc).__name__}.", file=sys.stderr)
            return 1
        next_offset_salvo = next_offset

    imprimir_evento(
        "processamento_aprovacoes_concluido",
        {
            "updates_recebidos": len(updates),
            "processados": processados,
            "enviados": enviados,
            "falhas": falhas,
            "ignorados": ignorados,
            "next_offset_salvo": next_offset_salvo,
            "dry_run": args.dry_run,
        },
    )

    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
