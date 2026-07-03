#!/usr/bin/env python3
"""Captura updates Telegram e encaminha mensagens de texto para a API Core."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_API_CORE_URL = "http://127.0.0.1:8000/telegram/entrada"
DEFAULT_OFFSET_FILE = Path(".runtime/telegram/agente_007_getupdates_offset.json")
TELEGRAM_API_BASE_URL = "https://api.telegram.org"
REQUEST_TIMEOUT_SECONDS = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Captura updates pendentes do Telegram via getUpdates e encaminha "
            "message.text para /telegram/entrada."
        )
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
        help=(
            "Apaga/ignora o offset local antes de consultar getUpdates, permitindo "
            "buscar novamente updates disponíveis."
        ),
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=None,
        help="Força manualmente o offset enviado ao getUpdates nesta execução.",
    )
    return parser.parse_args()


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            **(headers or {}),
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


def carregar_offset(path: Path) -> int | None:
    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "evento": "offset_local_invalido",
                    "arquivo": str(path),
                    "erro_tipo": type(exc).__name__,
                    "acao": "offset_ignorado",
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return None

    offset = payload.get("next_offset") if isinstance(payload, dict) else None
    if not isinstance(offset, int) or offset < 0:
        print(
            json.dumps(
                {
                    "evento": "offset_local_invalido",
                    "arquivo": str(path),
                    "erro_tipo": "ValorInvalido",
                    "acao": "offset_ignorado",
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return None

    return offset


def salvar_offset(path: Path, next_offset: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"next_offset": next_offset}
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def resetar_offset(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return


def buscar_updates(token: str, limit: int | None, offset: int | None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"timeout": 0}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset

    url = f"{TELEGRAM_API_BASE_URL}/bot{token}/getUpdates?{urlencode(params)}"
    request = Request(url, headers={"Accept": "application/json"}, method="GET")

    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        body = response.read().decode("utf-8")

    payload = json.loads(body)
    if not payload.get("ok"):
        raise RuntimeError("Telegram getUpdates retornou ok=false.")

    result = payload.get("result", [])
    if not isinstance(result, list):
        raise RuntimeError("Telegram getUpdates retornou result em formato inválido.")

    return result


def build_remetente_nome(user: dict[str, Any]) -> str | None:
    name_parts = [
        str(user.get("first_name") or "").strip(),
        str(user.get("last_name") or "").strip(),
    ]
    full_name = " ".join(part for part in name_parts if part)
    return full_name or None


def normalizar_update(update: dict[str, Any]) -> dict[str, Any] | None:
    message = update.get("message")
    if not isinstance(message, dict):
        return None

    text = message.get("text")
    if not isinstance(text, str) or not text.strip():
        return None

    user = message.get("from") if isinstance(message.get("from"), dict) else {}
    chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
    user_id = user.get("id")
    chat_id = chat.get("id")
    username = user.get("username")

    return {
        "tenant_id": "construtora-piloto",
        "obra_codigo": "OBRA-CAIO",
        "telegram_update_id": str(update.get("update_id")) if update.get("update_id") is not None else None,
        "telegram_message_id": str(message.get("message_id")) if message.get("message_id") is not None else None,
        "telegram_user_id": str(user_id) if user_id is not None else None,
        "telegram_username": str(username) if username else None,
        "chat_id": str(chat_id) if chat_id is not None else None,
        "chat_type": str(chat.get("type")) if chat.get("type") else None,
        "remetente_nome": build_remetente_nome(user),
        "remetente_identificador": str(user_id or chat_id) if user_id or chat_id else None,
        "tipo_mensagem": "texto",
        "conteudo": text,
        "anexos": [],
        "payload_original": update,
    }


def resumo_resposta_api(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "http_status": status_code,
        "ok": body.get("ok"),
        "status_evento": body.get("status_evento"),
        "status_comando": body.get("status_comando"),
        "intencao": body.get("intencao"),
        "usuario_autorizado": body.get("usuario_autorizado"),
        "evento_duplicado": body.get("evento_duplicado"),
    }


def maior_update_id(updates: list[dict[str, Any]]) -> int | None:
    update_ids = [
        update.get("update_id")
        for update in updates
        if isinstance(update.get("update_id"), int)
    ]
    return max(update_ids) if update_ids else None


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
            print(f"Erro ao resetar offset local: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1

    offset_origem = "manual" if args.offset is not None else "local"
    offset = args.offset if args.offset is not None else carregar_offset(offset_file)
    if offset is None:
        offset_origem = "nenhum"

    try:
        updates = buscar_updates(token, args.limit, offset)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"Erro ao consultar getUpdates: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.limit is not None:
        updates = updates[: args.limit]

    total_updates = len(updates)
    mensagens_texto = 0
    enviados = 0
    falhas = 0
    ignorados = 0

    print(
        json.dumps(
            {
                "evento": "captura_telegram_iniciada",
                "updates_recebidos": total_updates,
                "limit": args.limit,
                "offset": offset,
                "offset_origem": offset_origem,
                "offset_file": str(offset_file),
                "api_core_url": api_core_url,
            },
            ensure_ascii=False,
        )
    )

    for update in updates:
        payload = normalizar_update(update)
        if payload is None:
            ignorados += 1
            continue

        mensagens_texto += 1
        headers = {"X-Correlation-Id": str(uuid.uuid4())}

        try:
            status_code, response_body = post_json(api_core_url, payload, headers=headers)
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            falhas += 1
            print(
                json.dumps(
                    {
                        "evento": "envio_api_core_falhou",
                        "telegram_update_id": payload["telegram_update_id"],
                        "telegram_message_id": payload["telegram_message_id"],
                        "erro_tipo": type(exc).__name__,
                        "erro": str(exc),
                    },
                    ensure_ascii=False,
                )
            )
            continue

        if 200 <= status_code < 300 and response_body.get("ok") is True:
            enviados += 1
        else:
            falhas += 1

        print(
            json.dumps(
                {
                    "evento": "envio_api_core_processado",
                    "telegram_update_id": payload["telegram_update_id"],
                    "telegram_message_id": payload["telegram_message_id"],
                    "resultado": resumo_resposta_api(status_code, response_body),
                },
                ensure_ascii=False,
            )
        )

    max_update_id = maior_update_id(updates)
    next_offset = max_update_id + 1 if max_update_id is not None else None
    next_offset_salvo = None
    if falhas == 0 and next_offset is not None:
        try:
            salvar_offset(offset_file, next_offset)
        except OSError as exc:
            print(f"Erro ao salvar offset local: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        next_offset_salvo = next_offset
    elif falhas > 0:
        print(
            json.dumps(
                {
                    "evento": "offset_nao_avancado",
                    "motivo": "falhas_no_envio_api_core",
                    "falhas": falhas,
                    "next_offset_calculado": next_offset,
                    "offset_file": str(offset_file),
                },
                ensure_ascii=False,
            )
        )

    print(
        json.dumps(
            {
                "evento": "captura_telegram_concluida",
                "updates_recebidos": total_updates,
                "mensagens_texto": mensagens_texto,
                "enviados_com_sucesso": enviados,
                "falhas": falhas,
                "ignorados_sem_texto": ignorados,
                "next_offset_salvo": next_offset_salvo,
            },
            ensure_ascii=False,
        )
    )

    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
