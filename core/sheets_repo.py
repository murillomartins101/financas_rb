# core/sheets_repo.py
from __future__ import annotations
from typing import Dict, Any, Optional
import pandas as pd
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

def read_sheet_df(sheet_key: str) -> Dict[str, Any]:
    """
    Lê uma aba e retorna DataFrame.
    SEM fallback silencioso: se falhar, success=False.
    """
    err = _ensure_connected()
    if err:
        return {"success": False, "error": err, "df": None}

    try:
        ws = _ws(sheet_key)
        rows = ws.get_all_records()
        df = pd.DataFrame(rows)
        return {"success": True, "error": None, "df": df}
    except gspread.exceptions.WorksheetNotFound:
        return {"success": False, "error": f"Aba '{sheet_key}' não encontrada", "df": None}
    except Exception as e:
        return {"success": False, "error": f"Erro ao ler aba '{sheet_key}': {e}", "df": None}
