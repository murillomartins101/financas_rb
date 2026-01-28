from __future__ import annotations

from pathlib import Path
import tempfile
import shutil
import pandas as pd
import streamlit as st

from .constants import norm_str, PAYMENT_STATUS_MAP, SHOW_STATUS_MAP, TX_TYPE_MAP
from .validators import validate_all  # opcional


# ============================================================
# NORMALIZAÇÃO — SHOWS
# ============================================================
def normalize_shows(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    rename = {
        "data_shd": "data_show",
        "data": "data_show",
        "publi": "publico",
        "cache_acordado": "cache_acordado",
        "show_id": "show_id",
        "casa": "casa",
        "cidade": "cidade",
        "status": "status",
        "observacao": "observacao",
    }
    df.rename(columns={k: v for k, v in rename.items() if k in df.columns}, inplace=True)

    # show_id
    df["show_id"] = df.get("show_id", "").astype(str).str.strip()

    # status
    df["status_raw"] = df.get("status", "").map(norm_str)
    df["status"] = df["status_raw"].map(SHOW_STATUS_MAP).fillna(df["status_raw"])

    # datas
    df["data_show"] = pd.to_datetime(df.get("data_show", None), errors="coerce").dt.date

    # público
    df["publico"] = (
        pd.to_numeric(df.get("publico", 0), errors="coerce")
        .fillna(0)
        .astype(int)
    )

    # cache
    df["cache_acordado"] = (
        pd.to_numeric(df.get("cache_acordado", 0), errors="coerce")
        .fillna(0.0)
        .astype(float)
    )

    # strings
    for c in ["casa", "cidade", "observacao"]:
        if c in df.columns:
            df[c] = df[c].astype(str).fillna("").str.strip()

    return df


# ============================================================
# NORMALIZAÇÃO — TRANSACTIONS
# ============================================================
def normalize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    rename = {
        "id": "id",
        "data": "data",
        "tipo": "tipo",
        "categoria": "categoria",
        "subcategoria": "subcategoria",
        "descricao": "descricao",
        "valor": "valor",
        "show_id": "show_id",
        "payment_status": "payment_status",
        "conta": "conta",
    }
    df.rename(columns={k: v for k, v in rename.items() if k in df.columns}, inplace=True)

    # id
    df["id"] = df.get("id", "").astype(str).str.strip()

    # data
    df["data"] = pd.to_datetime(df.get("data", None), errors="coerce").dt.date

    # tipo
    df["tipo_raw"] = df.get("tipo", "").map(norm_str)
    df["tipo"] = df["tipo_raw"].map(TX_TYPE_MAP).fillna(df["tipo_raw"])

    # categoria / subcategoria
    df["categoria"] = df.get("categoria", "").map(norm_str)
    df["subcategoria"] = df.get("subcategoria", "").map(norm_str)

    # descricao
    df["descricao"] = df.get("descricao", "").astype(str).fillna("").str.strip()

    # valor
    df["valor"] = (
        pd.to_numeric(df.get("valor", 0), errors="coerce")
        .fillna(0.0)
        .astype(float)
        .abs()
    )

    # show_id
    df["show_id"] = df.get("show_id", "").astype(str).str.strip()

    # payment_status
    df["payment_status_raw"] = df.get("payment_status", "").map(norm_str)
    df["payment_status"] = (
        df["payment_status_raw"].map(PAYMENT_STATUS_MAP).fillna(df["payment_status_raw"])
    )

    # conta
    df["conta"] = df.get("conta", "").astype(str).fillna("").str.strip()

    return df


# ============================================================
# CARREGAMENTO — EXCEL
# ============================================================
@st.cache_data(show_spinner=False)
def load_data(path: str):
    """
    Carrega o Excel completo, normaliza todas as abas e retorna
    um dicionário com DataFrames prontos para uso.
    """

    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {p}")

    # Workaround Windows/Excel/OneDrive
    with tempfile.NamedTemporaryFile(delete=False, suffix=p.suffix) as tmp:
        tmp_path = Path(tmp.name)

    try:
        shutil.copy2(p, tmp_path)
        xls = pd.ExcelFile(tmp_path)

        # Abas obrigatórias
        required_sheets = [
            "shows",
            "transactions",
            "payout_rules",
            "show_payout_config",
            "members",
            "member_shares",
        ]

        missing = [s for s in required_sheets if s not in xls.sheet_names]
        if missing:
            raise ValueError(f"Aba(s) ausente(s) no Excel: {missing}")

        # Leitura
        shows = pd.read_excel(xls, "shows")
        transactions = pd.read_excel(xls, "transactions")
        payout_rules = pd.read_excel(xls, "payout_rules")
        show_payout_config = pd.read_excel(xls, "show_payout_config")
        members = pd.read_excel(xls, "members")
        member_shares = pd.read_excel(xls, "member_shares")

    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    # Normalização
    shows = normalize_shows(shows)
    transactions = normalize_transactions(transactions)

    return {
        "shows": shows,
        "transactions": transactions,
        "payout_rules": payout_rules,
        "show_payout_config": show_payout_config,
        "members": members,
        "member_shares": member_shares,
    }