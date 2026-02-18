"""
Camada de acesso ao Google Sheets (gspread)
- Leitura robusta de todas as abas
- Normalização de dados
- Conversão correta de números pt-BR
- Logs explícitos de erro
- Estrutura segura para analytics

Retorno padronizado:
  { "success": bool, "error": str|None, ... }
"""

import re
import pandas as pd
from typing import Dict, Any, Optional
import gspread

from core.google_cloud import google_cloud_manager


# ==========================================
# CONFIGURAÇÃO DE ABAS
# ==========================================

SHEETS = {
    "shows": "shows",
    "transactions": "transactions",
    "payout_rules": "payout_rules",
    "show_payout_config": "show_payout_config",
    "members": "members",
    "member_shares": "member_shares",
    "merchandising": "merchandising",
}

# Defina aqui colunas numéricas por aba
NUMERIC_COLUMNS = {
    "shows": ["publico", "cache_acordado"],
    "transactions": ["valor"],
    "member_shares": ["percentual", "valor"],
}


# ==========================================
# UTILITÁRIOS
# ==========================================

def _ensure_connected() -> Optional[str]:
    status = google_cloud_manager.get_connection_status()
    if not status.get("connected"):
        return status.get("error") or "Google Sheets não conectado"
    return None


def _ws(sheet_key: str):
    sheet_name = SHEETS.get(sheet_key, sheet_key)
    return google_cloud_manager.get_worksheet(sheet_name)


def _normalize_column_name(col: str) -> str:
    return str(col).strip()


def _parse_br_number(value):
    """
    Converte número pt-BR:
    "1.234,56" -> 1234.56
    """
    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()

    if s == "":
        return 0.0

    # Remove qualquer coisa que não seja número, vírgula, ponto ou sinal
    s = re.sub(r"[^\d,.\-]", "", s)

    # pt-BR → padrão Python
    s = s.replace(".", "").replace(",", ".")

    try:
        return float(s)
    except Exception:
        return 0.0


def _worksheet_to_df(ws, sheet_key: str) -> pd.DataFrame:
    """
    Converte worksheet para DataFrame:
    - Sem depender de get_all_records()
    - Sem confiar em parse automático do gspread
    """

    values = ws.get_all_values()

    if not values or len(values) < 2:
        return pd.DataFrame()

    headers = [_normalize_column_name(h) for h in values[0]]
    rows = values[1:]

    df = pd.DataFrame(rows, columns=headers)

    # Strip geral
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # Conversão de colunas numéricas
    for col in NUMERIC_COLUMNS.get(sheet_key, []):
        if col in df.columns:
            df[col] = df[col].apply(_parse_br_number)

    return df


# ==========================================
# LEITURA COMPLETA
# ==========================================

def get_all_data() -> Dict[str, pd.DataFrame]:
    """
    Retorna todas as abas como DataFrame.
    NÃO mascara erro silenciosamente.
    """

    err = _ensure_connected()
    if err:
        raise RuntimeError(err)

    out: Dict[str, pd.DataFrame] = {}
    errors: Dict[str, str] = {}

    print("🔎 Conectado ao Google Sheets.")
    print("📄 Abas disponíveis:", list(SHEETS.values()))

    for key, sheet_name in SHEETS.items():
        try:
            ws = google_cloud_manager.get_worksheet(sheet_name)

            if ws is None:
                out[key] = pd.DataFrame()
                errors[key] = f"Aba não encontrada: {sheet_name}"
                continue

            df = _worksheet_to_df(ws, key)
            out[key] = df

            print(f"✅ {sheet_name}: {len(df)} linhas carregadas")

        except Exception as e:
            out[key] = pd.DataFrame()
            errors[key] = str(e)

    if errors:
        print("⚠ Erros detectados ao carregar abas:")
        for k, v in errors.items():
            print(f" - {k}: {v}")

    return out


# ==========================================
# ESCRITA
# ==========================================

def write_row(sheet_key: str, row_dict: Dict[str, Any]) -> dict:
    err = _ensure_connected()
    if err:
        return {"success": False, "error": err}

    try:
        ws = _ws(sheet_key)
        if ws is None:
            return {"success": False, "error": f"Aba não encontrada: {sheet_key}"}

        headers = ws.row_values(1)
        if not headers:
            headers = list(row_dict.keys())
            ws.append_row(headers, value_input_option="USER_ENTERED")

        row = [row_dict.get(h, "") for h in headers]
        ws.append_row(row, value_input_option="USER_ENTERED")

        return {"success": True, "error": None}

    except Exception as e:
        return {"success": False, "error": str(e)}


def update_row(sheet_key: str, id_value: str, id_column: str = "id", updates: Dict[str, Any] = None) -> dict:
    updates = updates or {}
    err = _ensure_connected()
    if err:
        return {"success": False, "error": err}

    try:
        ws = _ws(sheet_key)
        if ws is None:
            return {"success": False, "error": f"Aba não encontrada: {sheet_key}"}

        headers = ws.row_values(1)

        if id_column not in headers:
            return {"success": False, "error": f"Coluna '{id_column}' não existe"}

        col_idx = headers.index(id_column) + 1
        cell = ws.find(str(id_value), in_column=col_idx)

        if not cell:
            return {"success": False, "error": f"Registro não encontrado: {id_value}"}

        row_idx = cell.row
        current_row = ws.row_values(row_idx)

        current_map = {
            headers[i]: (current_row[i] if i < len(current_row) else "")
            for i in range(len(headers))
        }

        current_map.update(updates)

        new_row = [current_map.get(h, "") for h in headers]

        ws.update(
            f"A{row_idx}:{gspread.utils.rowcol_to_a1(row_idx, len(headers))}",
            [new_row]
        )

        return {"success": True, "error": None, "row": row_idx}

    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_row(sheet_key: str, id_value: str, id_column: str = "id") -> dict:
    err = _ensure_connected()
    if err:
        return {"success": False, "error": err}

    try:
        ws = _ws(sheet_key)
        if ws is None:
            return {"success": False, "error": f"Aba não encontrada: {sheet_key}"}

        headers = ws.row_values(1)

        if id_column not in headers:
            return {"success": False, "error": f"Coluna '{id_column}' não existe"}

        col_idx = headers.index(id_column) + 1
        cell = ws.find(str(id_value), in_column=col_idx)

        if not cell:
            return {"success": False, "error": f"Registro não encontrado: {id_value}"}

        ws.delete_rows(cell.row)

        return {"success": True, "error": None}

    except Exception as e:
        return {"success": False, "error": str(e)}


# ==========================================
# FUTURO
# ==========================================

def sync_all(data: Dict[str, pd.DataFrame]) -> dict:
    return {"success": False, "error": "sync_all ainda não implementado"}
