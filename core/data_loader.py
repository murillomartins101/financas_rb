"""
Carregamento de dados com fallback para Excel
Prioridade: Google Sheets > Excel local

Inclui parsing robusto:
- Datas do Sheets podem vir como string (dd/mm) OU serial number
- Valores podem vir como 'R$ 1.200,00' / '1.200,00' etc.

FIXES IMPORTANTES:
- Normaliza nomes de colunas (ID/id, Data/data, etc.)
- Normaliza tipos (ids como string, valores como float, datas como datetime)
- Evita "sumir" registros por mismatch de coluna/ID
"""

import re
import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import streamlit as st

from core.google_sheets import get_all_data
from core.google_cloud import google_cloud_manager

warnings.filterwarnings("ignore")


# -----------------------------
# Normalização de colunas
# -----------------------------
COLUMN_ALIASES = {
    # IDs
    "ID": "id",
    "Id": "id",
    "TRANSACTION_ID": "id",
    "Transacao_ID": "id",
    "SHOW_ID": "show_id",
    "Show_ID": "show_id",

    # datas
    "Data": "data",
    "DATA": "data",
    "DATA_SHOW": "data_show",
    "Data_Show": "data_show",

    # valor
    "Valor": "valor",
    "VALOR": "valor",
    "CACHE_ACORDADO": "cache_acordado",
    "Cache_Acordado": "cache_acordado",

    # comuns
    "Tipo": "tipo",
    "TIPO": "tipo",
    "Categoria": "categoria",
    "CATEGORIA": "categoria",
    "Subcategoria": "subcategoria",
    "SUBCATEGORIA": "subcategoria",
    "Descricao": "descricao",
    "DESCRICAO": "descricao",
    "Payment_Status": "payment_status",
    "PAYMENT_STATUS": "payment_status",
}


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.replace("\ufeff", "", regex=False)
        .str.strip()
    )
    # aplica aliases (case-sensitive + tentativa case-insensitive)
    new_cols = []
    for c in df.columns:
        if c in COLUMN_ALIASES:
            new_cols.append(COLUMN_ALIASES[c])
            continue
        # tentativa case-insensitive
        cu = str(c).strip()
        if cu.upper() in COLUMN_ALIASES:
            new_cols.append(COLUMN_ALIASES[cu.upper()])
        else:
            new_cols.append(c)
    df.columns = new_cols
    return df


def _ensure_column(df: pd.DataFrame, col: str, default=np.nan) -> pd.DataFrame:
    if col not in df.columns:
        df[col] = default
    return df


# -----------------------------
# Parsing robusto (Sheets/Excel)
# -----------------------------
def _parse_sheet_date(series: pd.Series) -> pd.Series:
    """
    Converte datas vindas do Google Sheets / Excel:
    - strings dd/mm/yyyy (dayfirst=True)
    - serial numbers (dias desde 1899-12-30)
    - strings com hora
    """
    s = series.copy()

    # normaliza vazios
    s = s.replace(["", "None", "nan", "NaN", "NaT"], np.nan)

    numeric = pd.to_numeric(s, errors="coerce")
    is_serial = numeric.notna() & (numeric > 20000) & (numeric < 60000)

    out = pd.Series([pd.NaT] * len(s), index=s.index, dtype="datetime64[ns]")

    # serial
    out.loc[is_serial] = pd.to_datetime(
        numeric.loc[is_serial],
        unit="D",
        origin="1899-12-30",
        errors="coerce",
    )

    # resto: strings e datetime
    rest = ~is_serial
    # tenta parse com dayfirst e depois padrão
    parsed = pd.to_datetime(s.loc[rest], errors="coerce", dayfirst=True)
    out.loc[rest] = parsed

    return out


def _parse_brl_number(series: pd.Series) -> pd.Series:
    """
    Converte valores tipo:
    'R$ 1.200,00' / '1.200,00' / '1200.00' / 1200
    em float.
    """
    s = series.copy()

    def norm(x):
        if x is None:
            return np.nan
        if isinstance(x, (int, float, np.integer, np.floating)):
            # mantém nan
            if isinstance(x, float) and np.isnan(x):
                return np.nan
            return float(x)

        txt = str(x).strip().replace("\xa0", " ")
        txt = re.sub(r"[R$\s]", "", txt)

        # "1.200,00" -> "1200.00"
        if "," in txt and "." in txt:
            txt = txt.replace(".", "").replace(",", ".")
        else:
            # "1200,00" -> "1200.00"
            if "," in txt:
                txt = txt.replace(".", "").replace(",", ".")

        txt = re.sub(r"[^0-9\.\-]", "", txt)

        try:
            return float(txt) if txt != "" else np.nan
        except Exception:
            return np.nan

    return s.apply(norm)


def _normalize_id(series: pd.Series) -> pd.Series:
    s = series.copy()
    s = s.astype(str).str.strip()
    s = s.replace(["", "None", "nan", "NaN"], "")
    return s


# -----------------------------
# DataLoader
# -----------------------------
class DataLoader:
    def __init__(self):
        self.excel_path = Path("data/Financas_RB.xlsx")
        self.use_excel_fallback = False
        self.last_load_time = None
        self._load_data_config()

    def _load_data_config(self):
        try:
            if "data_config" in st.secrets:
                self.primary_source = st.secrets["data_config"].get("primary_source", "google")
                self.allow_fallback = st.secrets["data_config"].get("allow_fallback", False)
            else:
                self.primary_source = "google"
                self.allow_fallback = False
        except Exception as e:
            logging.warning(f"[DATA_LOADER] erro ao carregar secrets: {e}")
            self.primary_source = "google"
            self.allow_fallback = False

        self.primary_source = (self.primary_source or "google").strip().lower()
        self.allow_fallback = bool(self.allow_fallback)

    def load_all_data(self, force_refresh: bool = False) -> Dict[str, pd.DataFrame]:
        needs_refresh = force_refresh or self._should_refresh_cache()
        if not needs_refresh and hasattr(st.session_state, "all_data"):
            return st.session_state.all_data

        if self.primary_source == "excel":
            data = self._load_from_excel()
            self.use_excel_fallback = False
            data_source = "Excel local"

        elif self.primary_source == "google":
            status = google_cloud_manager.get_connection_status()
            if not status.get("connected"):
                err = status.get("error", "Credenciais não configuradas")
                logging.error(f"[DATA_LOADER] Google não conectado: {err}")

                if self.allow_fallback:
                    st.warning(
                        f"⚠️ **Modo fallback**\n\n"
                        f"Falha ao conectar no Google Sheets.\n\n"
                        f"Detalhes: {err}\n\n"
                        f"Usando Excel local."
                    )
                    data = self._load_from_excel()
                    self.use_excel_fallback = True
                    data_source = "Excel local (fallback)"
                else:
                    st.error(
                        f"❌ **Falha na autenticação com Google Sheets**\n\n"
                        f"Config: primary_source='google' e allow_fallback=false\n\n"
                        f"Problema: {err}"
                    )
                    raise RuntimeError(f"Google Sheets não disponível: {err}")

            else:
                try:
                    data = get_all_data()
                    if not self._validate_data(data):
                        raise RuntimeError("Dados incompletos no Google Sheets (abas vazias ou ausentes).")
                    self.use_excel_fallback = False
                    data_source = "Google Sheets"
                except Exception as e:
                    logging.error(f"[DATA_LOADER] erro ao carregar do Google: {e}")
                    if self.allow_fallback:
                        st.warning(f"⚠️ Erro no Google Sheets. Usando Excel. Erro: {e}")
                        data = self._load_from_excel()
                        self.use_excel_fallback = True
                        data_source = "Excel local (fallback)"
                    else:
                        st.error(f"❌ Erro ao carregar do Google Sheets: {e}")
                        raise

        else:
            st.error(f"Fonte de dados desconhecida: {self.primary_source}")
            return {}

        data = self._process_data(data)

        st.session_state.all_data = data
        st.session_state.data_source = data_source
        st.session_state.last_cache_update = datetime.now()
        self.last_load_time = datetime.now()

        if self.use_excel_fallback:
            st.sidebar.warning(f"⚠️ Fonte: {data_source}")
        else:
            st.sidebar.info(f"📊 Fonte: {data_source}")

        return data

    def _load_from_excel(self) -> Dict[str, pd.DataFrame]:
        data: Dict[str, pd.DataFrame] = {}
        if not self.excel_path.exists():
            return data

        sheet_mapping = {
            "shows": "shows",
            "transactions": "transactions",
            "payout_rules": "payout_rules",
            "show_payout_config": "show_payout_config",
            "members": "members",
            "member_shares": "member_shares",
            "merchandising": "merchandising",
        }

        try:
            for key, sheet in sheet_mapping.items():
                try:
                    data[key] = pd.read_excel(self.excel_path, sheet_name=sheet)
                except Exception:
                    data[key] = pd.DataFrame()
        except Exception as e:
            st.error(f"Erro ao ler Excel: {e}")

        return data

    def _validate_data(self, data: Dict[str, pd.DataFrame]) -> bool:
        required = ["shows", "transactions"]
        for s in required:
            if s not in data or data[s] is None or data[s].empty:
                return False
        return True

    def _process_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        processed: Dict[str, pd.DataFrame] = {}

        for key, df in (data or {}).items():
            if df is None or df.empty:
                processed[key] = pd.DataFrame() if df is None else df
                continue

            dfp = _clean_columns(df)

            if key == "shows":
                dfp = self._process_shows(dfp)
            elif key == "transactions":
                dfp = self._process_transactions(dfp)
            elif key == "payout_rules":
                dfp = self._process_payout_rules(dfp)
            else:
                # default: só limpa colunas e mantém
                dfp = dfp.copy()

            processed[key] = dfp

        return processed

    # --------------------
    # processors
    # --------------------
    def _process_shows(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # garante colunas críticas
        df = _ensure_column(df, "show_id", "")
        df = _ensure_column(df, "data_show", pd.NaT)
        df = _ensure_column(df, "cache_acordado", np.nan)

        df["show_id"] = _normalize_id(df["show_id"])

        df["data_show"] = _parse_sheet_date(df["data_show"])

        df["cache_acordado"] = _parse_brl_number(df["cache_acordado"])

        if "publico" in df.columns:
            df["publico"] = pd.to_numeric(df["publico"], errors="coerce").fillna(0).astype(int)

        # remove duplicados por ID (mantém mais recente)
        if "show_id" in df.columns:
            df = df.drop_duplicates(subset=["show_id"], keep="last")

        return df

    def _process_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # garante colunas críticas
        df = _ensure_column(df, "id", "")
        df = _ensure_column(df, "data", pd.NaT)
        df = _ensure_column(df, "valor", np.nan)
        df = _ensure_column(df, "payment_status", "")

        df["id"] = _normalize_id(df["id"])

        df["data"] = _parse_sheet_date(df["data"])

        df["valor"] = _parse_brl_number(df["valor"])

        # IMPORTANTE:
        # Se você remover ESTORNADO aqui, ele "some" de telas (CRUD e análises).
        # Mantive seu comportamento, mas recomendo filtrar no dashboard e não no loader.
        if "payment_status" in df.columns:
            df = df[df["payment_status"].astype(str).str.strip() != "ESTORNADO"]

        # remove duplicados por ID
        if "id" in df.columns:
            df = df.drop_duplicates(subset=["id"], keep="last")

        return df

    def _process_payout_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        for col in ["vigencia_inicio", "vigencia_fim"]:
            if col in df.columns:
                df[col] = _parse_sheet_date(df[col])

        for col in ["pct_caixa", "pct_musicos"]:
            if col in df.columns:
                s = _parse_brl_number(df[col])
                # aceita 20, 20%, 0.2 -> converte para 0-1 quando necessário
                s = np.where(s > 1, s / 100.0, s)
                df[col] = s

        return df

    def _should_refresh_cache(self) -> bool:
        if not hasattr(st.session_state, "last_cache_update"):
            return True
        last = st.session_state.last_cache_update
        if not last:
            return True
        diff = (datetime.now() - last).total_seconds()
        return diff > 300  # 5 min


data_loader = DataLoader()
