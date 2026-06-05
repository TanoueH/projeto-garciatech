import argparse
import json
from pathlib import Path
from datetime import datetime

import pandas as pd


REQUIRED_COLUMNS = [
    "codigo_atividade",
    "atividade",
    "data_inicio",
    "data_fim",
    "status",
    "percentual_concluido",
    "responsavel",
]


STATUS_MAP = {
    "não iniciada": "Não iniciada",
    "nao iniciada": "Não iniciada",
    "em andamento": "Em andamento",
    "concluída": "Concluída",
    "concluida": "Concluída",
    "paralisada": "Paralisada",
    "atrasada": "Atrasada",
}


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_status(value):
    raw = normalize_text(value).lower()
    return STATUS_MAP.get(raw, None)


def validate_excel(input_file: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(input_file)

    df.columns = [
        str(col).strip().lower().replace(" ", "_")
        for col in df.columns
    ]

    errors = []
    warnings = []

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing_columns:
        errors.append({
            "tipo": "COLUNAS_OBRIGATORIAS_AUSENTES",
            "detalhe": missing_columns
        })

    if errors:
        report = {
            "arquivo": str(input_file),
            "status": "ERRO",
            "erros": errors,
            "avisos": warnings,
        }

        report_path = output_dir / "relatorio_validacao_erro.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return report

    normalized_rows = []

    for idx, row in df.iterrows():
        row_number = idx + 2

        codigo = normalize_text(row.get("codigo_atividade"))
        atividade = normalize_text(row.get("atividade"))
        responsavel = normalize_text(row.get("responsavel"))
        status = normalize_status(row.get("status"))

        if not codigo:
            errors.append({
                "linha": row_number,
                "tipo": "CODIGO_ATIVIDADE_VAZIO",
                "detalhe": "A coluna codigo_atividade não pode estar vazia."
            })

        if not atividade:
            errors.append({
                "linha": row_number,
                "tipo": "ATIVIDADE_VAZIA",
                "detalhe": "A coluna atividade não pode estar vazia."
            })

        if status is None:
            errors.append({
                "linha": row_number,
                "tipo": "STATUS_INVALIDO",
                "valor": normalize_text(row.get("status")),
                "detalhe": "Status aceitos: Não iniciada, Em andamento, Concluída, Paralisada, Atrasada."
            })

        data_inicio = pd.to_datetime(row.get("data_inicio"), errors="coerce")
        data_fim = pd.to_datetime(row.get("data_fim"), errors="coerce")

        if pd.isna(data_inicio):
            errors.append({
                "linha": row_number,
                "tipo": "DATA_INICIO_INVALIDA",
                "valor": normalize_text(row.get("data_inicio"))
            })

        if pd.isna(data_fim):
            errors.append({
                "linha": row_number,
                "tipo": "DATA_FIM_INVALIDA",
                "valor": normalize_text(row.get("data_fim"))
            })

        percentual = row.get("percentual_concluido")

        try:
            percentual = float(percentual)
        except Exception:
            percentual = None

        if percentual is None or percentual < 0 or percentual > 100:
            errors.append({
                "linha": row_number,
                "tipo": "PERCENTUAL_INVALIDO",
                "valor": normalize_text(row.get("percentual_concluido")),
                "detalhe": "O percentual deve estar entre 0 e 100."
            })

        normalized_rows.append({
            "codigo_atividade": codigo,
            "eap": normalize_text(row.get("eap")),
            "atividade": atividade,
            "data_inicio": None if pd.isna(data_inicio) else data_inicio.strftime("%Y-%m-%d"),
            "data_fim": None if pd.isna(data_fim) else data_fim.strftime("%Y-%m-%d"),
            "status": status,
            "percentual_concluido": percentual,
            "responsavel": responsavel,
            "observacao": normalize_text(row.get("observacao")),
            "data_atualizacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    normalized_df = pd.DataFrame(normalized_rows)

    duplicated = normalized_df[
        normalized_df.duplicated(subset=["codigo_atividade"], keep=False)
    ]

    if not duplicated.empty:
        errors.append({
            "tipo": "CODIGO_ATIVIDADE_DUPLICADO",
            "codigos": duplicated["codigo_atividade"].dropna().unique().tolist(),
            "detalhe": "Existem códigos repetidos na planilha."
        })

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    staging_csv = output_dir / f"cronograma_validado_{timestamp}.csv"
    report_json = output_dir / f"relatorio_validacao_{timestamp}.json"

    normalized_df.to_csv(staging_csv, index=False, encoding="utf-8-sig")

    report = {
        "arquivo": str(input_file),
        "status": "ERRO" if errors else "OK",
        "total_linhas": len(df),
        "total_validado": len(normalized_df),
        "arquivo_validado": str(staging_csv),
        "erros": errors,
        "avisos": warnings,
    }

    report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arquivo", required=True, help="Caminho do arquivo Excel")
    parser.add_argument("--saida", default="data/staging/openproject", help="Pasta de saída")

    args = parser.parse_args()

    input_file = Path(args.arquivo)
    output_dir = Path(args.saida)

    if not input_file.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {input_file}")

    report = validate_excel(input_file, output_dir)

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
