"""
Camada de acesso ao Google Sheets (gspread)
- Leitura de todas as abas necessárias
- Escrita/atualização/exclusão de linhas
Padroniza retornos SEMPRE como dict:
  { "success": bool, "error": str|None, ... }
"""

import pandas as pd
from typing import Dict, Any, Optional, List
import gspread

from core.google_cloud import google_cloud_manager


SHEETS = {
    "shows": "shows",
    "transactions": "transactions",
    "payout_rules": "payout_rules",
    "show_payout_config": "show_payout_config",
    "members": "members",
    "member_shares": "member_shares",
    "merchandising": "merchandising",
}


def _ensure_connected() -> Optional[str]:
    status = google_cloud_manager.get_connection_status()
    if not status.get("connected"):
        return status.get("error") or "Google Sheets não conectado"
    return None


def _ws(sheet_key: str):
    sheet_name = SHEETS.get(sheet_key, sheet_key)
    return google_cloud_manager.get_worksheet(sheet_name)


def _to_dataframe(records: List[dict]) -> pd.DataFrame:
    return pd.DataFrame(records) if records else pd.DataFrame()


def get_all_data() -> Dict[str, pd.DataFrame]:
    err = _ensure_connected()
    if err:
        raise RuntimeError(err)

    out: Dict[str, pd.DataFrame] = {}
    for key, sheet_name in SHEETS.items():
        try:
            ws = google_cloud_manager.get_worksheet(sheet_name)
            if ws is None:
                out[key] = pd.DataFrame()
                continue
            out[key] = _to_dataframe(ws.get_all_records())
        except Exception:
            out[key] = pd.DataFrame()

    return out


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
        if not headers:
            return {"success": False, "error": "Aba sem cabeçalho (linha 1 vazia)"}

        if id_column not in headers:
            return {"success": False, "error": f"Coluna '{id_column}' não existe na aba"}

        col_idx = headers.index(id_column) + 1
        cell = ws.find(str(id_value), in_column=col_idx)
        if not cell:
            return {"success": False, "error": f"Registro não encontrado: {id_value}"}

        row_idx = cell.row
        current_row = ws.row_values(row_idx)
        current_map = {headers[i]: (current_row[i] if i < len(current_row) else "") for i in range(len(headers))}
        current_map.update(updates)

        new_row = [current_map.get(h, "") for h in headers]
        ws.update(f"A{row_idx}:{gspread.utils.rowcol_to_a1(row_idx, len(headers))}", [new_row])
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
        if not headers:
            return {"success": False, "error": "Aba sem cabeçalho"}

        if id_column not in headers:
            return {"success": False, "error": f"Coluna '{id_column}' não existe na aba"}

        col_idx = headers.index(id_column) + 1
        cell = ws.find(str(id_value), in_column=col_idx)
        if not cell:
            return {"success": False, "error": f"Registro não encontrado: {id_value}"}

        ws.delete_rows(cell.row)
        return {"success": True, "error": None}
    except Exception as e:
        return {"success": False, "error": str(e)}


def sync_all(data: Dict[str, pd.DataFrame]) -> dict:
    return {"success": False, "error": "sync_all ainda não implementado"}
