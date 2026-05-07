#!/usr/bin/env python3
"""
Importa cronograma normalizado para OpenProject via API v3.

Uso:
  export OPENPROJECT_URL="http://localhost:8081"
  export OPENPROJECT_API_KEY="opapi-..."
  export OPENPROJECT_PROJECT_IDENTIFIER="obra-001-caio"
  python scripts/import_openproject_cronograma.py data/import/cronograma_caio_openproject_base.csv

Observações:
- Não usa login/senha do usuário; usa API token do OpenProject.
- Cria primeiro as fases e depois as tarefas filhas.
- Usa o tipo "Task" por padrão. Se existir tipo "Phase" no OpenProject, usa para as fases.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class Row:
    external_id: str
    parent_external_id: str
    kind: str
    subject: str
    description: str
    status_original: str
    owner_original: str
    start_date: str
    due_date: str
    duration_days: str
    source_line: str


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if not value:
        raise SystemExit(f"Variável de ambiente obrigatória não definida: {name}")
    return value.rstrip("/") if name.endswith("URL") else value


def get_json(session: requests.Session, url: str) -> dict[str, Any]:
    r = session.get(url, headers={"Accept": "application/hal+json"}, timeout=30)
    if not r.ok:
        raise RuntimeError(f"GET {url} falhou: {r.status_code}\n{r.text[:1000]}")
    return r.json()


def post_json(session: requests.Session, url: str, payload: dict[str, Any]) -> dict[str, Any]:
    r = session.post(
        url,
        headers={"Accept": "application/hal+json", "Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=60,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(
            f"POST {url} falhou: {r.status_code}\nPayload:\n{json.dumps(payload, indent=2, ensure_ascii=False)}\nResposta:\n{r.text[:2000]}"
        )
    return r.json()


def load_rows(csv_path: str) -> list[Row]:
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = []
        for item in reader:
            rows.append(
                Row(
                    external_id=(item.get("ID externo") or "").strip(),
                    parent_external_id=(item.get("Pai externo") or "").strip(),
                    kind=(item.get("Tipo") or "").strip(),
                    subject=(item.get("Assunto") or "").strip(),
                    description=(item.get("Descrição") or "").strip(),
                    status_original=(item.get("Status") or "").strip(),
                    owner_original=(item.get("Responsável original") or "").strip(),
                    start_date=(item.get("Data de início") or "").strip(),
                    due_date=(item.get("Data de término") or "").strip(),
                    duration_days=(item.get("Prazo dias úteis") or "").strip(),
                    source_line=(item.get("Linha origem Excel") or "").strip(),
                )
            )
    return rows


def get_project_id(session: requests.Session, base_url: str, identifier: str) -> int:
    """
    Localiza o projeto pelo identifier.

    Algumas versões do OpenProject não aceitam filtro por "identifier"
    em /api/v3/projects. Por isso, listamos os projetos e filtramos
    localmente.
    """
    url = f"{base_url}/api/v3/projects?pageSize=1000"

    while url:
        data = get_json(session, url)
        elements = data.get("_embedded", {}).get("elements", [])

        for project in elements:
            project_identifier = str(project.get("identifier", "")).strip()
            if project_identifier == identifier:
                return int(project["id"])

        next_href = (
            data.get("_links", {}).get("nextByOffset", {}).get("href")
            or data.get("_links", {}).get("next", {}).get("href")
        )

        if next_href:
            url = f"{base_url}{next_href}" if next_href.startswith("/") else next_href
        else:
            url = ""

    raise SystemExit(
        f"Projeto com identificador '{identifier}' não encontrado. "
        f"Crie-o no OpenProject antes de importar."
    )


def get_name_id_map(session: requests.Session, base_url: str, endpoint: str) -> dict[str, int]:
    data = get_json(session, f"{base_url}/api/v3/{endpoint}")
    elements = data.get("_embedded", {}).get("elements", [])
    return {str(e.get("name", "")).lower(): int(e["id"]) for e in elements if "id" in e}


def create_work_package(
    session: requests.Session,
    base_url: str,
    project_id: int,
    row: Row,
    type_id: int,
    parent_id: int | None,
) -> int:
    desc = (
        f"{row.description}\n\n"
        f"---\n"
        f"**ID externo:** {row.external_id}\n\n"
        f"**Tipo original:** {row.kind}\n\n"
        f"**Responsável original:** {row.owner_original or 'não informado'}\n\n"
        f"**Status original:** {row.status_original or 'não informado'}\n\n"
        f"**Prazo original:** {row.duration_days or 'não informado'} dias úteis\n\n"
        f"**Linha de origem no Excel:** {row.source_line or 'não informada'}\n"
    )
    payload: dict[str, Any] = {
        "subject": row.subject[:255],
        "description": {"format": "markdown", "raw": desc},
        "startDate": row.start_date or None,
        "dueDate": row.due_date or None,
        "scheduleManually": True,
        "percentageDone": 0,
        "_links": {"type": {"href": f"/api/v3/types/{type_id}"}},
    }
    if parent_id:
        payload["_links"]["parent"] = {"href": f"/api/v3/work_packages/{parent_id}"}

    created = post_json(session, f"{base_url}/api/v3/projects/{project_id}/work_packages", payload)
    return int(created["id"])


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python scripts/import_openproject_cronograma.py <arquivo_csv>")

    csv_path = sys.argv[1]
    base_url = env("OPENPROJECT_URL", "http://localhost:8081")
    api_key = env("OPENPROJECT_API_KEY")
    project_identifier = env("OPENPROJECT_PROJECT_IDENTIFIER", "obra-001-caio")

    session = requests.Session()
    session.auth = ("apikey", api_key)

    project_id = get_project_id(session, base_url, project_identifier)
    types = get_name_id_map(session, base_url, "types")

    task_type_id = types.get("task") or next(iter(types.values()))
    phase_type_id = types.get("phase") or task_type_id

    rows = load_rows(csv_path)
    created_by_external: dict[str, int] = {}

    # Primeira passada: fases/pais.
    for row in rows:
        if not row.parent_external_id:
            type_id = phase_type_id
            wp_id = create_work_package(session, base_url, project_id, row, type_id, None)
            created_by_external[row.external_id] = wp_id
            print(f"FASE criada: {row.external_id} -> WP #{wp_id} | {row.subject}")

    # Segunda passada: tarefas filhas.
    for row in rows:
        if row.parent_external_id:
            parent_id = created_by_external.get(row.parent_external_id)
            if not parent_id:
                print(f"AVISO: pai não encontrado para {row.external_id}: {row.parent_external_id}. Criando sem pai.")
            wp_id = create_work_package(session, base_url, project_id, row, task_type_id, parent_id)
            created_by_external[row.external_id] = wp_id
            print(f"TAREFA criada: {row.external_id} -> WP #{wp_id} | {row.subject}")

    print(f"Importação concluída. Total criado: {len(created_by_external)} work packages.")


if __name__ == "__main__":
    main()
