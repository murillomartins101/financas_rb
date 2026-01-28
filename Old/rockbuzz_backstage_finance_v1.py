from __future__ import annotations

import io
from datetime import datetime, timedelta, date
from typing import List, Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Google Sheets (tolerante a ambientes sem dependências)
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GS_AVAILABLE = True
except Exception:
    GS_AVAILABLE = False

# -----------------------------
# CONFIG GERAL
# -----------------------------
st.set_page_config(
    page_title="Rockbuzz | Backstage Finance",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🤘"
)

# CSS - Professional Financial Dashboard Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #ffffff;
        color: #0f172a;
    }

    [data-testid="stAppViewContainer"] {
        background-color: #ffffff;
        color: #0f172a;
    }

    [data-testid="stAppViewContainer"] .stMarkdown,
    [data-testid="stAppViewContainer"] .stTextInput label,
    [data-testid="stAppViewContainer"] .stSelectbox label,
    [data-testid="stAppViewContainer"] .stDateInput label,
    [data-testid="stAppViewContainer"] .stNumberInput label,
    [data-testid="stAppViewContainer"] .stTextArea label {
        color: #0f172a;
    }
    
    /* Main Header */
    .main-header {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 1.5rem;
        padding: 0;
    }
    
    /* Dark KPI Cards - Financial Dashboard Style */
    .kpi-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    
    @media (max-width: 1200px) {
        .kpi-row {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    @media (max-width: 768px) {
        .kpi-row {
            grid-template-columns: 1fr;
        }
    }
    
    .kpi-card-dark {
        background: #1a1a2e;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        color: white;
        position: relative;
        min-height: 100px;
    }
    
    .kpi-card-dark.accent {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-left: 4px solid #fbbf24;
    }
    
    .kpi-card-dark.green {
        border-left: 4px solid #10b981;
    }
    
    .kpi-card-dark.red {
        border-left: 4px solid #ef4444;
    }
    
    .kpi-card-dark.blue {
        border-left: 4px solid #3b82f6;
    }
    
    .kpi-card-dark .kpi-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.25rem;
    }
    
    .kpi-card-dark .kpi-label {
        font-size: 0.75rem;
        font-weight: 500;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .kpi-card-dark .kpi-delta {
        font-size: 0.7rem;
        margin-top: 0.5rem;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
    }
    
    .kpi-card-dark .kpi-delta.positive {
        color: #10b981;
        background: rgba(16, 185, 129, 0.15);
    }
    
    .kpi-card-dark .kpi-delta.negative {
        color: #ef4444;
        background: rgba(239, 68, 68, 0.15);
    }
    
    /* Legacy KPI container for compatibility */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .kpi-card {
        background: #1a1a2e;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        color: white;
        border-left: 4px solid #3b82f6;
    }
    
    .kpi-card.receitas {
        border-left-color: #10b981;
    }
    
    .kpi-card.despesas {
        border-left-color: #ef4444;
    }
    
    .kpi-card.resultado {
        border-left-color: #fbbf24;
    }
    
    .kpi-card.shows {
        border-left-color: #8b5cf6;
    }
    
    .kpi-card.ticket {
        border-left-color: #f59e0b;
    }
    
    .kpi-icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    
    .kpi-label {
        font-size: 0.75rem;
        font-weight: 500;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.25rem;
    }
    
    .kpi-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.2;
    }
    
    .kpi-delta {
        font-size: 0.7rem;
        font-weight: 600;
        margin-top: 0.5rem;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
    }
    
    .kpi-delta.positive {
        color: #10b981;
        background: rgba(16, 185, 129, 0.15);
    }
    
    .kpi-delta.negative {
        color: #ef4444;
        background: rgba(239, 68, 68, 0.15);
    }
    
    /* Section Headers */
    .section-header {
        font-size: 1rem;
        font-weight: 600;
        color: #1a1a2e;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e5e7eb;
    }
    
    /* Card Container - White cards for charts */
    .card-container {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        border: 1px solid #e5e7eb;
        margin-bottom: 1rem;
    }
    
    .card-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 1rem;
    }
    
    /* Dark Sidebar */
    [data-testid="stSidebar"] {
        background: #1a1a2e !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: #1a1a2e !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e5e7eb;
    }
    
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #ffffff;
    }
    
    [data-testid="stSidebar"] .stRadio label {
        color: #e5e7eb !important;
    }
    
    [data-testid="stSidebar"] .stRadio label:hover {
        color: #fbbf24 !important;
    }
    
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.1);
    }
    
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stDateInput label {
        color: #e5e7eb !important;
    }
    
    /* Sidebar navigation items */
    .sidebar-nav-item {
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        border-radius: 8px;
        color: #9ca3af;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .sidebar-nav-item:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #ffffff;
    }
    
    .sidebar-nav-item.active {
        background: rgba(251, 191, 36, 0.15);
        color: #fbbf24;
        border-left: 3px solid #fbbf24;
    }
    
    /* Metrics Styling */
    [data-testid="stMetric"] {
        background: #1a1a2e;
        border-radius: 12px;
        padding: 1rem;
        border-left: 4px solid #3b82f6;
    }
    
    [data-testid="stMetricLabel"] {
        font-weight: 500;
        color: #9ca3af !important;
        font-size: 0.75rem;
        text-transform: uppercase;
    }
    
    [data-testid="stMetricValue"] {
        font-weight: 700;
        color: #ffffff !important;
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: transparent;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 0;
        font-weight: 500;
        font-size: 0.875rem;
        color: #6b7280;
        padding: 0.75rem 1.25rem;
        border-bottom: 2px solid transparent;
        background: transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background: transparent;
        color: #1a1a2e;
        border-bottom: 2px solid #fbbf24;
    }
    
    /* Button Styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.875rem;
        padding: 0.625rem 1.25rem;
        transition: all 0.2s ease;
    }
    
    .stButton > button[kind="primary"] {
        background: #fbbf24;
        color: #1a1a2e;
        border: none;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #f59e0b;
        transform: translateY(-1px);
    }
    
    /* DataFrames */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e5e7eb;
    }
    
    /* Form Styling */
    .stForm {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        border: 1px solid #e5e7eb;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        font-size: 0.875rem;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #fbbf24;
        box-shadow: 0 0 0 2px rgba(251, 191, 36, 0.2);
    }
    
    /* Form Labels - Fix Visibility */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stNumberInput label,
    .stDateInput label,
    .stTimeInput label,
    .stMultiSelect label {
        color: #1a1a2e !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        margin-bottom: 0.5rem !important;
        display: block !important;
    }
    
    /* Labels within forms */
    .stForm label {
        color: #1a1a2e !important;
        font-weight: 500 !important;
    }
    
    /* Ensure label contrast with data attributes */
    [data-testid="stForm"] label,
    div[data-baseweb="input"] label,
    div[data-baseweb="select"] label,
    div[data-baseweb="textarea"] label {
        color: #1a1a2e !important;
    }
    
    /* Alert Boxes */
    .stAlert {
        border-radius: 8px;
        border: none;
        font-size: 0.875rem;
    }
    
    /* Download Button */
    .stDownloadButton > button {
        border-radius: 8px;
        font-weight: 600;
        background: #1a1a2e;
        color: white;
    }
    
    .stDownloadButton > button:hover {
        background: #16213e;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1a1a2e;
        font-size: 0.875rem;
    }
    
    /* Progress indicators */
    .stProgress > div > div > div {
        background: #fbbf24;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f5f5f7;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #d1d5db;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #9ca3af;
    }
    
    /* Period Badge */
    .period-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: #1a1a2e;
        color: #fbbf24;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    /* Legend styling for charts */
    .chart-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        margin-top: 0.5rem;
        font-size: 0.75rem;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .legend-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Helper function for KPI cards HTML
def render_kpi_cards(kpis: list) -> str:
    """
    Render KPI cards with modern styling.
    kpis: list of dicts with keys: icon, label, value, delta (optional), delta_type (optional), card_type
    """
    cards_html = '<div class="kpi-container">'
    for kpi in kpis:
        card_type = kpi.get('card_type', '')
        delta_html = ''
        if kpi.get('delta'):
            delta_class = 'positive' if kpi.get('delta_type') == 'positive' else 'negative'
            delta_icon = '&#9650;' if kpi.get('delta_type') == 'positive' else '&#9660;'
            delta_html = f'<div class="kpi-delta {delta_class}">{delta_icon} {kpi["delta"]}</div>'
        cards_html += f'<div class="kpi-card {card_type}"><div class="kpi-icon">{kpi.get("icon", "")}</div><div class="kpi-label">{kpi.get("label", "")}</div><div class="kpi-value">{kpi.get("value", "")}</div>{delta_html}</div>'
    cards_html += '</div>'
    return cards_html

# =============================================================================
# HELPERS
# =============================================================================
def brl(x: float | int | str | None) -> str:
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return "R$ 0,00"
        if isinstance(x, str):
            x = float(x.replace("\u00a0", "").replace(".", "").replace(",", "."))
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def normalize_valor_series(col: pd.Series) -> pd.Series:
    s = (
        col.astype(str)
          .str.replace("\u00A0", "", regex=False)
          .str.replace(r"[^\d,\-\. ,]", "", regex=True)
          .str.strip()
    )
    tem_virg = s.str.contains(",", na=False)
    s_br = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    s = s.where(~tem_virg, s_br)
    return pd.to_numeric(s, errors="coerce")

def _only_shows_mask(df: pd.DataFrame) -> pd.Series:
    """Apenas linhas cuja categoria é exatamente 'Shows' (case-insensitive)."""
    cat = df.get("categoria", pd.Series([""]*len(df), index=df.index)).astype(str).str.strip().str.casefold()
    return cat.eq("shows")

def count_shows(df: pd.DataFrame) -> int:
    """
    Conta shows exclusivamente na categoria 'Shows'.
    - Filtra categoria 'Shows' (considera todas as linhas da categoria, não apenas receitas).
    - Usa (data, evento) como chave única para shows com evento preenchido.
    - Para linhas sem evento: usa (data, descricao) como chave única.
    - Fallback: conta linhas únicas.
    
    Isso garante que shows com o mesmo nome em datas diferentes sejam contados separadamente,
    e que múltiplos shows no mesmo dia com eventos/descrições diferentes também sejam contados.
    """
    if df is None or df.empty:
        return 0
    
    # Filtra categoria Shows
    base = df.loc[_only_shows_mask(df)].copy()
    if base.empty:
        return 0
    
    # Prepara colunas para deduplicação
    if "data" in base.columns:
        base["_data_str"] = base["data"].dt.strftime("%Y-%m-%d").fillna("")
    else:
        base["_data_str"] = ""
    
    if "evento" in base.columns:
        base["_evento_norm"] = base["evento"].astype(str).str.strip().str.casefold()
    else:
        base["_evento_norm"] = ""
    
    if "descricao" in base.columns:
        base["_descricao_norm"] = base["descricao"].astype(str).str.strip().str.casefold()
    else:
        base["_descricao_norm"] = ""
    
    # Separa linhas com e sem evento
    com_evento = base.loc[base["_evento_norm"].ne("")].copy()
    sem_evento = base.loc[base["_evento_norm"].eq("")].copy()
    
    # Para linhas com evento: conta combinações únicas de (data, evento)
    qtd_com_evento = 0
    if not com_evento.empty:
        # Cria chave única (data, evento)
        com_evento["_show_key"] = com_evento["_data_str"] + "|" + com_evento["_evento_norm"]
        qtd_com_evento = int(com_evento["_show_key"].nunique())
    
    # Para linhas sem evento: conta combinações únicas de (data, descricao)
    qtd_sem_evento = 0
    if not sem_evento.empty:
        # Separa linhas com e sem data
        sem_evento_com_data = sem_evento.loc[sem_evento["_data_str"].ne("")].copy()
        sem_evento_sem_data = sem_evento.loc[sem_evento["_data_str"].eq("")].copy()
        
        if not sem_evento_com_data.empty:
            # Cria chave única (data, descricao)
            sem_evento_com_data["_show_key"] = sem_evento_com_data["_data_str"] + "|" + sem_evento_com_data["_descricao_norm"]
            qtd_sem_evento += int(sem_evento_com_data["_show_key"].nunique())
        
        if not sem_evento_sem_data.empty:
            # Fallback: conta descrições únicas ou linhas
            if sem_evento_sem_data["_descricao_norm"].ne("").any():
                qtd_sem_evento += int(sem_evento_sem_data.loc[sem_evento_sem_data["_descricao_norm"].ne(""), "_descricao_norm"].nunique())
                qtd_sem_evento += int((sem_evento_sem_data["_descricao_norm"].eq("")).sum())
            else:
                qtd_sem_evento += len(sem_evento_sem_data)
    
    return qtd_com_evento + qtd_sem_evento

def _show_key_series(df: pd.DataFrame) -> pd.Series:
    data_str = pd.to_datetime(df.get("data"), errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    evento = df.get("evento", "").astype(str).str.strip()
    descricao = df.get("descricao", "").astype(str).str.strip()
    evento_norm = evento.str.casefold()
    descricao_norm = descricao.str.casefold()
    return pd.Series(
        np.where(evento_norm.ne(""), data_str + "|" + evento_norm, data_str + "|" + descricao_norm),
        index=df.index,
    )

def _flags_sinal_cache(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    texto = (
        df.get("descricao", "").astype(str)
        + " "
        + df.get("tags", "").astype(str)
    ).str.casefold()
    is_sinal = texto.str.contains("sinal", na=False)
    is_cache = texto.str.contains(r"cach[eê]", regex=True, na=False)
    return is_sinal, is_cache

def calcular_financas_shows(df: pd.DataFrame) -> dict:
    base = df.loc[_only_shows_mask(df)].copy()
    if base.empty:
        return {
            "receita_efetiva_total": 0.0,
            "receita_efetiva_media": 0.0,
            "cache_total": 0.0,
            "despesas_total": 0.0,
            "despesas_efetivas": 0.0,
            "percentual_caixa": 0.0,
            "shows_efetivados": 0,
            "base_efetiva": base,
        }

    base["show_key"] = _show_key_series(base)

    if "tipo" in base.columns:
        tipo = base["tipo"].astype(str).str.strip().str.casefold()
        entrada_mask = tipo.eq("entrada") | (base["valor"] > 0)
    else:
        entrada_mask = base["valor"] > 0

    is_sinal, is_cache = _flags_sinal_cache(base)
    is_cache = is_cache & entrada_mask
    is_sinal = is_sinal & entrada_mask
    show_cache_map = base.groupby("show_key").apply(lambda g: bool(is_cache.loc[g.index].any()))
    show_has_cache = base["show_key"].map(show_cache_map).fillna(False)

    efetiva_mask = entrada_mask & (~is_sinal | show_has_cache)

    receita_efetiva_total = base.loc[efetiva_mask, "valor"].sum()
    cache_total = base.loc[is_cache, "valor"].sum()
    despesas_total = -base.loc[base["valor"] < 0, "valor"].sum()
    despesas_efetivas = -base.loc[(base["valor"] < 0) & show_has_cache, "valor"].sum()
    shows_efetivados = int(base.loc[show_has_cache, "show_key"].nunique())
    receita_efetiva_media = (receita_efetiva_total / shows_efetivados) if shows_efetivados else 0.0
    percentual_caixa = (
        (receita_efetiva_total - despesas_efetivas) / receita_efetiva_total * 100
        if receita_efetiva_total > 0
        else 0.0
    )

    base_efetiva = base.loc[efetiva_mask].copy()

    return {
        "receita_efetiva_total": float(receita_efetiva_total),
        "receita_efetiva_media": float(receita_efetiva_media),
        "cache_total": float(cache_total),
        "despesas_total": float(despesas_total),
        "despesas_efetivas": float(despesas_efetivas),
        "percentual_caixa": float(percentual_caixa),
        "shows_efetivados": shows_efetivados,
        "base_efetiva": base_efetiva,
    }

def calcular_ticket_medio(df: pd.DataFrame) -> float:
    """
    Ticket médio = (somente receitas da categoria 'Shows') / quantidade de shows.
    Receita = tipo == 'Entrada' (quando existir) ou valor > 0.
    """
    if df is None or df.empty:
        return 0.0
    base = df.loc[_only_shows_mask(df)].copy()
    if base.empty:
        return 0.0

    if "tipo" in base.columns:
        tipo = base["tipo"].astype(str).str.strip().str.casefold()
        receitas = base.loc[tipo.eq("entrada"), "valor"].sum()
        if receitas == 0:
            receitas = base.loc[base["valor"] > 0, "valor"].sum()
    else:
        receitas = base.loc[base["valor"] > 0, "valor"].sum()

    qtd = count_shows(df)
    return float(receitas) / qtd if qtd else 0.0

def get_periodo_descricao(dt_min: date, dt_max: date) -> str:
    return f"{dt_min.strftime('%d/%m/%Y')} a {dt_max.strftime('%d/%m/%Y')}" if dt_min != dt_max else dt_min.strftime("%d/%m/%Y")

def ultimo_mes_calendario(ref: date) -> tuple[date, date]:
    primeiro_ref = ref.replace(day=1)
    ultimo_mes_fim = primeiro_ref - timedelta(days=1)
    ultimo_mes_ini = ultimo_mes_fim.replace(day=1)
    return ultimo_mes_ini, ultimo_mes_fim

def periodo_selecionado(df_dates: pd.Series, periodo_sel: str, dmin_custom: Optional[date]=None, dmax_custom: Optional[date]=None) -> tuple[date, date]:
    hoje = datetime.now().date()
    if df_dates.dropna().empty:
        return hoje, hoje
    data_min_df = pd.to_datetime(df_dates).dropna().min().date()
    data_max_df = pd.to_datetime(df_dates).dropna().max().date()
    if periodo_sel == "Último mês":
        return ultimo_mes_calendario(hoje)
    if periodo_sel == "Últimos 3 meses":
        return hoje - timedelta(days=90), hoje
    if periodo_sel == "Últimos 6 meses":
        return hoje - timedelta(days=180), hoje
    if periodo_sel == "Ano atual":
        return date(hoje.year, 1, 1), hoje
    if periodo_sel == "Todo período":
        return data_min_df, data_max_df
    return (dmin_custom or data_min_df), (dmax_custom or data_max_df)

def fmt_brdate(s: pd.Series | pd.DatetimeIndex | pd.Timestamp) -> pd.Series:
    return pd.to_datetime(s, errors="coerce").dt.strftime("%d/%m/%Y")

def dedupe_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, ~df.columns.duplicated(keep="first")]

def read_rateio_config() -> pd.DataFrame:
    """Lê configuração de rateio fixo do session state ou retorna vazio."""
    if "rateio_config" not in st.session_state:
        st.session_state.rateio_config = pd.DataFrame()
    return st.session_state.rateio_config.copy()

def save_rateio_config(cfg: pd.DataFrame):
    """Salva configuração de rateio fixo no session state."""
    st.session_state.rateio_config = cfg.copy()

def read_centros_config() -> pd.DataFrame:
    """Lê configuração de centros de custo do session state ou retorna vazio."""
    if "centros_config" not in st.session_state:
        st.session_state.centros_config = pd.DataFrame()
    return st.session_state.centros_config.copy()

def save_centros_config(cfg: pd.DataFrame):
    """Salva configuração de centros de custo no session state."""
    st.session_state.centros_config = cfg.copy()

# =============================================================================
# CONEXÃO GOOGLE SHEETS
# =============================================================================
@st.cache_resource(show_spinner=False)
def get_sheet_client():
    if not GS_AVAILABLE:
        return None, None
    try:
        cfg = st.secrets.get("gcp", None)
    except Exception:
        return None, None
    if cfg is None:
        return None, None
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(cfg, scope)
        gc = gspread.authorize(creds)
        return gc, cfg.get("sheet_id")
    except Exception:
        return None, None

def ensure_ws_with_header(sh, title="lancamentos"):
    try:
        ws = sh.worksheet(title)
    except Exception:
        ws = sh.add_worksheet(title=title, rows=2000, cols=12)
        ws.append_row(["data","tipo","categoria","descricao","conta","valor","quem","evento","publico","tags"])
    return ws

# =============================================================================
# LEITURA / ESCRITA (com _row estável)
# =============================================================================
@st.cache_data(show_spinner=False)
def read_sheet(sheet_name: str = "lancamentos") -> pd.DataFrame:
    """
    Lê dados do Google Sheets e:
    - normaliza cabeçalhos (minúsculo/sem acento) + aliases
    - cria coluna `_row` com o índice real da linha na planilha (0-based)
    - NÃO remove linhas sem data (para não "sumirem" na tela de Lançamentos)
    """
    gc, sheet_id = get_sheet_client()
    if not (gc and sheet_id):
        return pd.DataFrame(columns=["data","tipo","categoria","descricao","conta","valor","quem","evento","publico","tags","_row"])

    sh = gc.open_by_key(sheet_id)
    ws = ensure_ws_with_header(sh, sheet_name)
    rows = ws.get_all_values()
    if not rows:
        return pd.DataFrame(columns=["data","tipo","categoria","descricao","conta","valor","quem","evento","publico","tags","_row"])

    raw_header = [str(c).strip() for c in rows[0]]

    def norm_col(s: str) -> str:
        s = s.strip()
        t = (s.lower()
               .replace("ã","a").replace("á","a").replace("à","a").replace("â","a")
               .replace("é","e").replace("ê","e").replace("í","i")
               .replace("ó","o").replace("ô","o").replace("õ","o")
               .replace("ú","u").replace("ç","c"))
        return " ".join(t.split())

    alias = {
        "data":"data","data do lancamento":"data","data do lançamento":"data","dt":"data",
        "tipo":"tipo","entrada/saida":"tipo","entrada/saída":"tipo",
        "categoria":"categoria",
        "descricao":"descricao","descrição":"descricao",
        "conta":"conta","forma de pagamento":"conta","pagamento":"conta",
        "valor":"valor",
        "quem":"quem","responsavel":"quem","responsável":"quem",
        "evento":"evento","show":"evento",
        "publico":"publico","público":"publico","publico total":"publico",
        "tags":"tags",
    }

    normalized = [alias.get(norm_col(c), norm_col(c)) for c in raw_header]
    data_rows = rows[1:]
    df = pd.DataFrame(data_rows, columns=normalized)

    # linha real do Sheets (0-based; Sheets = _row + 2 por causa do cabeçalho)
    df["_row"] = np.arange(len(df), dtype=int)

    # Coalesce para duplicatas
    def coalesce(df, target, candidates):
        if target not in df.columns:
            df[target] = ""
        for c in candidates:
            if c in df.columns and c != target:
                df[target] = df[target].mask(df[target].astype(str).str.strip().eq(""), df[c])
        keep = [c for c in df.columns if (c not in candidates) or (c == target)]
        return df[keep]

    df = coalesce(df, "data",      [c for c in df.columns if c != "data" and c.startswith("data")])
    df = coalesce(df, "tipo",      [c for c in df.columns if c != "tipo" and c.startswith("tipo")])
    df = coalesce(df, "categoria", [c for c in df.columns if c != "categoria" and c.startswith("categoria")])
    df = coalesce(df, "descricao", [c for c in df.columns if c != "descricao" and c.startswith("descricao")])
    df = coalesce(df, "conta",     [c for c in df.columns if c != "conta" and ("conta" in c or "pagamento" in c)])
    df = coalesce(df, "valor",     [c for c in df.columns if c != "valor" and c.startswith("valor")])
    df = coalesce(df, "quem",      [c for c in df.columns if c != "quem" and ("responsavel" in c or "responsável" in c or "quem" in c)])
    df = coalesce(df, "evento",    [c for c in df.columns if c != "evento" and ("evento" in c or "show" in c)])
    df = coalesce(df, "publico",   [c for c in df.columns if c != "publico" and ("publico" in c or "público" in c)])
    df = coalesce(df, "tags",      [c for c in df.columns if c != "tags" and "tag" in c])

    for c in ["data","tipo","categoria","descricao","conta","valor","quem","evento","publico","tags"]:
        if c not in df.columns:
            df[c] = ""

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    for c in ["tipo","categoria","descricao","conta","quem","evento","tags"]:
        df[c] = df[c].astype(str).str.strip()

    df["valor_raw"] = df["valor"]
    df["valor"] = normalize_valor_series(df["valor"]).fillna(0.0)
    df["publico"] = pd.to_numeric(df["publico"], errors="coerce").fillna(0).astype(int)

    return df.sort_values("_row").reset_index(drop=True)

def append_rows(sheet_name: str, rows: List[List]):
    gc, sheet_id = get_sheet_client()
    if not (gc and sheet_id):
        raise RuntimeError("Google Sheets não configurado.")
    sh = gc.open_by_key(sheet_id)
    ws = ensure_ws_with_header(sh, sheet_name)
    try:
        ws.append_rows(rows, value_input_option="USER_ENTERED")
    except AttributeError:
        for r in rows:
            ws.append_row(r, value_input_option="USER_ENTERED")

def update_row(sheet_name: str, row_index: int, new_data: List, field_names: List[str] = None):
    """
    Atualiza uma linha no Google Sheets.
    
    Args:
        sheet_name: Nome da planilha
        row_index: Índice da linha (0-based, será convertido para row_index+2 no Sheets)
        new_data: Lista de valores a serem salvos
        field_names: Lista de nomes de campos correspondentes aos valores em new_data.
                    Se fornecido, os valores serão mapeados para as colunas corretas
                    baseado no cabeçalho real da planilha.
                    Se não fornecido, usa a ordem padrão: 
                    ["data","tipo","categoria","descricao","conta","valor","quem","evento","publico","tags"]
    """
    gc, sheet_id = get_sheet_client()
    if not (gc and sheet_id):
        raise RuntimeError("Google Sheets não configurado.")
    sh = gc.open_by_key(sheet_id)
    ws = ensure_ws_with_header(sh, sheet_name)
    
    # Ordem padrão dos campos (deve corresponder ao cabeçalho criado em ensure_ws_with_header)
    default_field_order = ["data","tipo","categoria","descricao","conta","valor","quem","evento","publico","tags"]
    
    if field_names is None:
        field_names = default_field_order
    
    # Lê o cabeçalho real da planilha para mapear corretamente
    header_row = ws.row_values(1)
    if not header_row:
        # Se não há cabeçalho, usa a ordem padrão
        ws.update(f'A{row_index+2}:I{row_index+2}', [new_data], value_input_option="USER_ENTERED")
        return
    
    # Normaliza o cabeçalho para comparação (minúsculo, sem acentos)
    def norm_header(s: str) -> str:
        s = s.strip().lower()
        s = (s.replace("ã","a").replace("á","a").replace("à","a").replace("â","a")
              .replace("é","e").replace("ê","e").replace("í","i")
              .replace("ó","o").replace("ô","o").replace("õ","o")
              .replace("ú","u").replace("ç","c"))
        return s
    
    # Mapeamento de aliases para nomes canônicos
    alias_map = {
        "data":"data","data do lancamento":"data","data do lançamento":"data","dt":"data",
        "tipo":"tipo","entrada/saida":"tipo","entrada/saída":"tipo",
        "categoria":"categoria",
        "descricao":"descricao","descrição":"descricao",
        "conta":"conta","forma de pagamento":"conta","pagamento":"conta",
        "valor":"valor",
        "quem":"quem","responsavel":"quem","responsável":"quem",
        "evento":"evento","show":"evento",
        "publico":"publico","público":"publico","publico total":"publico",
        "tags":"tags",
    }
    
    # Cria mapeamento: nome do campo -> índice da coluna no sheet
    header_normalized = [alias_map.get(norm_header(h), norm_header(h)) for h in header_row]
    col_index_map = {name: idx for idx, name in enumerate(header_normalized)}
    
    # Cria a linha de dados com valores nas posições corretas
    row_data = [""] * len(header_row)
    for field_name, value in zip(field_names, new_data):
        field_normalized = alias_map.get(norm_header(field_name), norm_header(field_name))
        if field_normalized in col_index_map:
            row_data[col_index_map[field_normalized]] = value
    
    # Determina o range a ser atualizado (de A até a última coluna com dados)
    last_col = len(header_row)
    last_col_letter = chr(ord('A') + last_col - 1) if last_col <= 26 else 'Z'
    
    ws.update(f'A{row_index+2}:{last_col_letter}{row_index+2}', [row_data], value_input_option="USER_ENTERED")

def delete_row(sheet_name: str, row_index: int):
    gc, sheet_id = get_sheet_client()
    if not (gc and sheet_id):
        raise RuntimeError("Google Sheets não configurado.")
    sh = gc.open_by_key(sheet_id)
    ws = ensure_ws_with_header(sh, sheet_name)
    ws.delete_rows(row_index + 2)

# =============================================================================
# IMPORTADOR EXCEL
# =============================================================================
@st.cache_data(show_spinner=False)
def parse_legacy_excel(file: bytes) -> pd.DataFrame:
    raw = pd.read_excel(io.BytesIO(file), sheet_name=None, header=None)
    for _, df in raw.items():
        mask = df.apply(lambda r: r.astype(str).str.contains("Data", case=False, na=False)).any(axis=1)
        header_idx = np.where(mask)[0]
        if header_idx.size:
            hi = int(header_idx[0])
            header = df.iloc[hi].astype(str).tolist()
            body = df.iloc[hi + 1:].copy()
            body.columns = [str(c).strip() for c in header]

            def norm(s: str) -> str:
                return s.strip().lower().replace("descrição","descricao").replace("saída","saida")

            colmap = {
                "data":"data","tipo":"tipo","entrada":"tipo","saida":"tipo",
                "categoria":"categoria","descricao":"descricao","valor":"valor","conta":"conta"
            }
            new_cols = [colmap.get(norm(c), norm(c)) for c in body.columns]
            body.columns = new_cols
            body = body.loc[:, ~pd.Index(body.columns).duplicated(keep="first")]

            keep = [c for c in ["data","tipo","categoria","descricao","conta","valor"] if c in body.columns]
            out = body[keep].copy()

            if "data" in out.columns:
                out["data"] = pd.to_datetime(out["data"], errors="coerce")
            if "valor" in out.columns:
                out["valor"] = normalize_valor_series(out["valor"])
            if "tipo" in out.columns and "valor" in out.columns:
                out["tipo"] = out["tipo"].astype(str).str.strip().str.title()
                saida_mask = out["tipo"].str.contains("Sa[ií]d", case=False, regex=True, na=False)
                entr_mask  = out["tipo"].str.contains("Entrad", case=False, regex=True, na=False)
                out.loc[saida_mask, "valor"] = -out["valor"].abs()
                out.loc[entr_mask,  "valor"] =  out["valor"].abs()

            if "conta" not in out.columns: out["conta"] = ""
            if "categoria" not in out.columns: out["categoria"] = "Outros"

            out = out.dropna(how="all")
            out = out.dropna(subset=[c for c in ["data","valor"] if c in out.columns])
            return out

    return pd.DataFrame(columns=["data","tipo","categoria","descricao","conta","valor"])

# =============================================================================
# SIDEBAR
# =============================================================================
import os
# Logo - só exibe se o arquivo existir  
logo_path = "LOGO DEFINITIVO FUNDO ESCURO.png"
with st.sidebar:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("### 🎸 Rockbuzz")
        st.markdown("### Gestão Financeira")
    st.markdown("---")
    page = st.radio(
        "Navegação:",
        ["📊 Dashboard", "📝 Registrar", "📒 Lançamentos", "🧾 Fechamento", "⬆️ Importar Excel"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# =============================================================================
# DASHBOARD
# =============================================================================
if page == "📊 Dashboard":
    st.markdown('<p class="main-header">🎸 Dashboard Rockbuzz</p>', unsafe_allow_html=True)
    df = read_sheet("lancamentos")

    if df.empty or df["data"].isna().all():
        st.info("📭 Sem registros ainda. Use **Registrar** para adicionar lançamentos.")
    else:
        df = df.copy()
        df["ano_mes"] = df["data"].dt.to_period("M").astype(str)
        df["ano"] = df["data"].dt.year

        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            periodos = ["Último mês", "Últimos 3 meses", "Últimos 6 meses", "Ano atual", "Todo período", "Personalizado"]
            periodo_sel = st.selectbox("📅 Período", periodos, index=0)

        dmin_custom, dmax_custom = None, None
        if periodo_sel == "Personalizado":
            with col2:
                dmin_custom = st.date_input("De", value=pd.to_datetime(df["data"]).dropna().min().date(), format="DD/MM/YYYY")
            with col3:
                dmax_custom = st.date_input("Até", value=pd.to_datetime(df["data"]).dropna().max().date(), format="DD/MM/YYYY")

        df_com_data = df.dropna(subset=["data"]).copy()
        dt_min, dt_max = periodo_selecionado(df_com_data["data"], periodo_sel, dmin_custom, dmax_custom)
        if dt_min > dt_max:
            dt_min, dt_max = dt_max, dt_min

        mask = (df_com_data["data"].dt.date >= dt_min) & (df_com_data["data"].dt.date <= dt_max)
        dfp = df_com_data.loc[mask].copy()

        if dfp.empty:
            st.warning("Nenhum registro no período selecionado.")
        else:
            receitas = dfp.loc[dfp["valor"] > 0, "valor"].sum()
            despesas = -dfp.loc[dfp["valor"] < 0, "valor"].sum()
            resultado = receitas - despesas
            qtd_shows = count_shows(dfp)
            ticket_medio = calcular_ticket_medio(dfp) if qtd_shows > 0 else 0.0
            financas_shows = calcular_financas_shows(dfp)
            
            # Novos indicadores avançados
            margem_lucro = (resultado / receitas * 100) if receitas > 0 else 0.0
            roi = (resultado / despesas * 100) if despesas > 0 else 0.0
            qtd_transacoes = len(dfp)
            media_transacao = dfp["valor"].abs().mean() if not dfp.empty else 0.0
            
            # Calcular período anterior para comparação
            dias_periodo = (dt_max - dt_min).days + 1
            dt_ant_max = dt_min - timedelta(days=1)
            dt_ant_min = dt_ant_max - timedelta(days=dias_periodo - 1)
            mask_ant = (df_com_data["data"].dt.date >= dt_ant_min) & (df_com_data["data"].dt.date <= dt_ant_max)
            dfp_ant = df_com_data.loc[mask_ant].copy()
            
            receitas_ant = dfp_ant.loc[dfp_ant["valor"] > 0, "valor"].sum() if not dfp_ant.empty else 0
            despesas_ant = -dfp_ant.loc[dfp_ant["valor"] < 0, "valor"].sum() if not dfp_ant.empty else 0
            resultado_ant = receitas_ant - despesas_ant
            
            # Taxas de crescimento
            cresc_receitas = ((receitas - receitas_ant) / receitas_ant * 100) if receitas_ant > 0 else None
            cresc_despesas = ((despesas - despesas_ant) / despesas_ant * 100) if despesas_ant > 0 else None
            cresc_resultado = ((resultado - resultado_ant) / abs(resultado_ant) * 100) if resultado_ant != 0 else None

            # Period badge
            st.markdown(f'<div class="period-badge">📅 {get_periodo_descricao(dt_min, dt_max)}</div>', unsafe_allow_html=True)
            
            # Main KPI Cards - Modern Corporate Style
            main_kpis = [
                {
                    'icon': '💰',
                    'label': 'Receitas',
                    'value': brl(receitas),
                    'delta': f"{cresc_receitas:+.1f}%" if cresc_receitas is not None else None,
                    'delta_type': 'positive' if cresc_receitas and cresc_receitas > 0 else 'negative',
                    'card_type': 'receitas'
                },
                {
                    'icon': '💸',
                    'label': 'Despesas',
                    'value': brl(despesas),
                    'delta': f"{cresc_despesas:+.1f}%" if cresc_despesas is not None else None,
                    'delta_type': 'negative' if cresc_despesas and cresc_despesas > 0 else 'positive',
                    'card_type': 'despesas'
                },
                {
                    'icon': '📈',
                    'label': 'Resultado',
                    'value': brl(resultado),
                    'delta': f"{cresc_resultado:+.1f}%" if cresc_resultado is not None else None,
                    'delta_type': 'positive' if cresc_resultado and cresc_resultado > 0 else 'negative',
                    'card_type': 'resultado'
                },
                {
                    'icon': '🎤',
                    'label': 'Shows',
                    'value': str(int(qtd_shows)),
                    'card_type': 'shows'
                },
                {
                    'icon': '🎫',
                    'label': 'Ticket Médio',
                    'value': brl(ticket_medio) if qtd_shows > 0 else "N/A",
                    'card_type': 'ticket'
                }
            ]
            st.markdown(render_kpi_cards(main_kpis), unsafe_allow_html=True)
            
            # Secondary KPI Cards - Performance Indicators
            st.markdown('<div class="section-header">📈 Indicadores de Performance</div>', unsafe_allow_html=True)
            perf_kpis = [
                {
                    'icon': '📊',
                    'label': 'Margem de Lucro',
                    'value': f"{margem_lucro:.1f}%",
                    'card_type': ''
                },
                {
                    'icon': '💹',
                    'label': 'ROI',
                    'value': f"{roi:.1f}%",
                    'card_type': ''
                },
                {
                    'icon': '📋',
                    'label': 'Transações',
                    'value': str(qtd_transacoes),
                    'card_type': ''
                },
                {
                    'icon': '💵',
                    'label': 'Média/Transação',
                    'value': brl(media_transacao),
                    'card_type': ''
                }
            ]
            st.markdown(render_kpi_cards(perf_kpis), unsafe_allow_html=True)

            st.markdown("---")
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "📊 Visão Geral", "💰 Receitas vs Despesas", "📈 Evolução", "🏷️ Categorias", "🎤 Análise de Shows", "📉 Analytics Avançados"
            ])

            # Professional Financial Dashboard color palette
            colors_corporate = {
                'primary': '#1a1a2e',
                'secondary': '#16213e',
                'success': '#10b981',
                'danger': '#ef4444',
                'warning': '#fbbf24',
                'info': '#3b82f6',
                'purple': '#8b5cf6',
                'accent': '#fbbf24',
                'navy': '#1a1a2e',
                'gradient': ['#1a1a2e', '#16213e', '#0f3460', '#3b82f6', '#fbbf24']
            }
            
            chart_layout = dict(
                font=dict(family="Inter, sans-serif", size=11, color="#4b5563"),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=40, r=20, t=60, b=40),
                title_font=dict(size=16, color='#0f172a', family="Inter, sans-serif"),
                hoverlabel=dict(
                    bgcolor='#1a1a2e',
                    font_size=11,
                    font_family="Inter, sans-serif",
                    font_color='white'
                )
            )
            
            axis_style = dict(
                showgrid=True,
                gridcolor='#e5e7eb',
                linecolor='#e5e7eb',
                tickfont=dict(size=10, color='#4b5563')
            )
            
            legend_base = dict(
                bgcolor='rgba(255,255,255,0.95)',
                bordercolor='#e5e7eb',
                borderwidth=1,
                font=dict(size=10, color='#4b5563')
            )

            with tab1:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown('<div class="card-container">', unsafe_allow_html=True)
                    fig_pizza = go.Figure(data=[go.Pie(
                        labels=["Receitas", "Despesas"],
                        values=[max(receitas, 0), max(despesas, 0)],
                        hole=.5,
                        marker=dict(colors=[colors_corporate['success'], colors_corporate['danger']]),
                        textinfo='label+percent',
                        textfont=dict(size=13, family="Inter, sans-serif"),
                        hovertemplate="<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Percentual: %{percent}<extra></extra>"
                    )])
                    fig_pizza.update_layout(
                        **chart_layout,
                        title=dict(text="Distribuição: Receitas vs Despesas", x=0.5, xanchor='center'),
                        height=420,
                        showlegend=True,
                        legend={**legend_base, 'orientation': 'h', 'yanchor': 'bottom', 'y': -0.1, 'xanchor': 'center', 'x': 0.5}
                    )
                    # Display financial result in center (Receitas - Despesas)
                    # Shows positive/negative balance instead of incorrect sum
                    resultado = receitas - despesas
                    fig_pizza.add_annotation(
                        text=f"<b>Resultado</b><br>{brl(resultado)}",
                        x=0.5, y=0.5, font_size=14, showarrow=False,
                        font=dict(family="Inter, sans-serif", color="#1e293b")
                    )
                    st.plotly_chart(fig_pizza, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                with col_b:
                    top_desp = dfp.loc[dfp["valor"] < 0].copy()
                    if not top_desp.empty:
                        st.markdown('<div class="card-container">', unsafe_allow_html=True)
                        top_desp["categoria"] = top_desp["categoria"].replace("", "Sem categoria")
                        top_cat = top_desp.groupby("categoria")["valor"].sum().abs().sort_values(ascending=False).head(5)
                        
                        fig_top = go.Figure(data=[go.Bar(
                            x=top_cat.values,
                            y=top_cat.index,
                            orientation='h',
                            marker=dict(
                                color=top_cat.values,
                                colorscale=[[0, '#fecaca'], [0.5, '#f87171'], [1, '#dc2626']],
                                line=dict(color='#b91c1c', width=1)
                            ),
                            text=[brl(v) for v in top_cat.values],
                            textposition='outside',
                            textfont=dict(size=11, family="Inter, sans-serif"),
                            hovertemplate="<b>%{y}</b><br>Valor: %{text}<extra></extra>"
                        )])
                        fig_top.update_layout(
                            **chart_layout,
                            title=dict(text="Top 5 Categorias de Despesa", x=0.5, xanchor='center'),
                            height=420,
                            showlegend=False,
                            xaxis={**axis_style, 'showgrid': True, 'title': ''},
                            yaxis={**axis_style, 'showgrid': False, 'title': ''}
                        )
                        st.plotly_chart(fig_top, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.info("Sem despesas no período")

            with tab2:
                monthly = dfp.groupby("ano_mes", dropna=False).apply(
                    lambda x: pd.Series({
                        "Receitas": x.loc[x["valor"] > 0, "valor"].sum(),
                        "Despesas": -x.loc[x["valor"] < 0, "valor"].sum()
                    })
                ).reset_index()

                if not monthly.empty:
                    st.markdown('<div class="card-container">', unsafe_allow_html=True)
                    fig = go.Figure()
                    fig.add_bar(
                        x=monthly["ano_mes"], y=monthly["Receitas"], name="Receitas",
                        marker=dict(color=colors_corporate['success'], line=dict(color='#059669', width=1)),
                        hovertemplate="<b>%{x}</b><br>Receitas: R$ %{y:,.2f}<extra></extra>"
                    )
                    fig.add_bar(
                        x=monthly["ano_mes"], y=monthly["Despesas"], name="Despesas",
                        marker=dict(color=colors_corporate['danger'], line=dict(color='#dc2626', width=1)),
                        hovertemplate="<b>%{x}</b><br>Despesas: R$ %{y:,.2f}<extra></extra>"
                    )
                    # Add result line
                    monthly["Resultado"] = monthly["Receitas"] - monthly["Despesas"]
                    fig.add_trace(go.Scatter(
                        x=monthly["ano_mes"], y=monthly["Resultado"],
                        mode='lines+markers', name='Resultado',
                        line=dict(color=colors_corporate['info'], width=3),
                        marker=dict(size=8, symbol='diamond'),
                        hovertemplate="<b>%{x}</b><br>Resultado: R$ %{y:,.2f}<extra></extra>"
                    ))
                    fig.update_layout(
                        **chart_layout,
                        title=dict(text="Receitas vs Despesas por Mês", x=0.5, xanchor='center'),
                        barmode='group',
                        xaxis={**axis_style, 'title': 'Mês', 'showgrid': False},
                        yaxis={**axis_style, 'title': 'Valor (R$)', 'showgrid': True},
                        height=500,
                        hovermode='x unified',
                        legend={**legend_base, 'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'center', 'x': 0.5}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    monthly["Margem (%)"] = np.where(
                        monthly["Receitas"] > 0,
                        ((monthly["Resultado"]) / monthly["Receitas"] * 100).round(1),
                        0.0
                    )
                    view_month = monthly.assign(
                        Receitas_fmt=monthly["Receitas"].map(brl),
                        Despesas_fmt=monthly["Despesas"].map(brl),
                        Resultado_fmt=monthly["Resultado"].map(brl)
                    )
                    st.markdown('<div class="section-header">📋 Resumo Mensal</div>', unsafe_allow_html=True)
                    df_show = dedupe_columns(
                        view_month[["ano_mes","Receitas_fmt","Despesas_fmt","Resultado_fmt","Margem (%)"]]
                            .rename(columns={"ano_mes":"Mês","Receitas_fmt":"Receitas","Despesas_fmt":"Despesas","Resultado_fmt":"Resultado"})
                    )
                    st.dataframe(df_show, use_container_width=True, hide_index=True)

            with tab3:
                dd = dfp.groupby(dfp["data"].dt.date)["valor"].sum().reset_index(name="saldo_dia").sort_values("data")
                if dd.empty:
                    st.info("Sem dados diários no período.")
                else:
                    dd["saldo_acumulado"] = dd["saldo_dia"].cumsum()
                    st.markdown('<div class="card-container">', unsafe_allow_html=True)
                    fig_evol = go.Figure()
                    
                    # Add area fill with gradient effect
                    fig_evol.add_trace(go.Scatter(
                        x=dd["data"], y=dd["saldo_acumulado"],
                        mode='lines', name='Saldo Acumulado',
                        fill='tozeroy',
                        fillcolor='rgba(59, 130, 246, 0.15)',
                        line=dict(color=colors_corporate['info'], width=3),
                        hovertemplate="<b>%{x}</b><br>Saldo: R$ %{y:,.2f}<extra></extra>"
                    ))
                    
                    # Add markers on top
                    fig_evol.add_trace(go.Scatter(
                        x=dd["data"], y=dd["saldo_acumulado"],
                        mode='markers', name='',
                        marker=dict(color=colors_corporate['info'], size=6, line=dict(color='white', width=2)),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
                    
                    fig_evol.update_layout(
                        **chart_layout,
                        title=dict(text="Evolução do Saldo Acumulado", x=0.5, xanchor='center'),
                        xaxis={**axis_style, 'title': 'Data', 'showgrid': False},
                        yaxis={**axis_style, 'title': 'Saldo (R$)', 'showgrid': True},
                        height=500,
                        hovermode='x unified',
                        showlegend=False
                    )
                    st.plotly_chart(fig_evol, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    saldo_ini = float(dd["saldo_acumulado"].iloc[0]) if len(dd) else 0.0
                    saldo_fim = float(dd["saldo_acumulado"].iloc[-1]) if len(dd) else 0.0
                    variacao = saldo_fim - saldo_ini
                    media_dia = float(dd["saldo_dia"].mean() if len(dd) else 0.0)
                    
                    # KPI cards for evolution metrics
                    evol_kpis = [
                        {'icon': '📍', 'label': 'Saldo Inicial', 'value': brl(saldo_ini), 'card_type': ''},
                        {'icon': '🎯', 'label': 'Saldo Final', 'value': brl(saldo_fim), 'card_type': ''},
                        {
                            'icon': '📊', 'label': 'Variação', 'value': brl(variacao),
                            'delta': f"{(variacao/abs(saldo_ini)*100):.1f}%" if saldo_ini else None,
                            'delta_type': 'positive' if variacao > 0 else 'negative',
                            'card_type': ''
                        },
                        {'icon': '📈', 'label': 'Média Diária', 'value': brl(media_dia), 'card_type': ''}
                    ]
                    st.markdown(render_kpi_cards(evol_kpis), unsafe_allow_html=True)

            with tab4:
                cat = dfp.copy()
                cat["categoria"] = cat["categoria"].replace("", "Sem categoria")
                cat_agg = cat.groupby("categoria", dropna=False)["valor"].sum().reset_index().sort_values("valor", ascending=True)
                if cat_agg.empty:
                    st.info("Sem categorias no período.")
                else:
                    st.markdown('<div class="card-container">', unsafe_allow_html=True)
                    
                    # Create color based on positive/negative values
                    colors_cat = [colors_corporate['success'] if v >= 0 else colors_corporate['danger'] for v in cat_agg['valor']]
                    
                    fig_cat = go.Figure(data=[go.Bar(
                        x=cat_agg['valor'],
                        y=cat_agg['categoria'],
                        orientation='h',
                        marker=dict(
                            color=colors_cat,
                            line=dict(color='rgba(0,0,0,0.1)', width=1)
                        ),
                        text=[brl(v) for v in cat_agg['valor']],
                        textposition='outside',
                        textfont=dict(size=11, family="Inter, sans-serif"),
                        hovertemplate="<b>%{y}</b><br>Saldo: %{text}<extra></extra>"
                    )])
                    
                    fig_cat.update_layout(
                        **chart_layout,
                        title=dict(text="Saldo por Categoria", x=0.5, xanchor='center'),
                        height=max(400, len(cat_agg) * 40),
                        xaxis={**axis_style, 'title': 'Saldo (R$)', 'showgrid': True, 'zeroline': True, 'zerolinecolor': '#94a3b8', 'zerolinewidth': 2},
                        yaxis={**axis_style, 'title': '', 'showgrid': False}
                    )
                    st.plotly_chart(fig_cat, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    cat_det = cat.groupby("categoria").agg(Total=("valor","sum"), Qtd=("valor","count"), Média=("valor","mean")).reset_index()
                    cat_det["Total"] = cat_det["Total"].map(brl)
                    cat_det["Média"] = cat_det["Média"].map(brl)
                    df_show = dedupe_columns(cat_det.rename(columns={"categoria":"Categoria"}).sort_values("Qtd", ascending=False))
                    st.markdown('<div class="section-header">📋 Detalhes por Categoria</div>', unsafe_allow_html=True)
                    st.dataframe(df_show, use_container_width=True, hide_index=True)

            with tab5:
                if qtd_shows > 0:
                    receita_efetiva_total = financas_shows["receita_efetiva_total"]
                    receita_efetiva_media = financas_shows["receita_efetiva_media"]
                    cache_total = financas_shows["cache_total"]
                    despesas_total = financas_shows["despesas_total"]
                    percentual_caixa = financas_shows["percentual_caixa"]
                    shows_efetivados = financas_shows["shows_efetivados"]
                    
                    # KPI cards for shows
                    shows_kpis = [
                        {'icon': '🎤', 'label': 'Total de Shows', 'value': str(int(qtd_shows)), 'card_type': 'shows'},
                        {'icon': '✅', 'label': 'Shows Efetivados', 'value': str(int(shows_efetivados)), 'card_type': 'shows'},
                        {'icon': '💰', 'label': 'Valor Efetivo Total', 'value': brl(receita_efetiva_total), 'card_type': 'receitas'},
                        {'icon': '💵', 'label': 'Valor Efetivo por Show', 'value': brl(receita_efetiva_media), 'card_type': 'receitas'},
                        {'icon': '🎫', 'label': 'Ticket Médio', 'value': brl(ticket_medio), 'card_type': 'ticket'},
                        {'icon': '💼', 'label': 'Cachê Recebido', 'value': brl(cache_total), 'card_type': 'receitas'},
                        {'icon': '💸', 'label': 'Despesas de Shows', 'value': brl(despesas_total), 'card_type': 'despesas'},
                        {'icon': '📥', 'label': '% Caixa por Show', 'value': f"{percentual_caixa:.1f}%", 'card_type': 'resultado'}
                    ]
                    st.markdown(render_kpi_cards(shows_kpis), unsafe_allow_html=True)

                    # Lista de eventos (apenas categoria Shows, receitas)
                    base_receita = financas_shows["base_efetiva"].copy()

                    if not base_receita.empty and "evento" in base_receita.columns:
                        eventos_agg = (
                            base_receita.loc[base_receita["evento"].astype(str).str.strip().ne("")]
                            .groupby("evento", as_index=False)
                            .agg(valor=("valor", "sum"), data=("data", "min"), publico=("publico", "max"))
                        )
                        if not eventos_agg.empty:
                            # Create bar chart for shows
                            st.markdown('<div class="card-container">', unsafe_allow_html=True)
                            eventos_sorted = eventos_agg.sort_values("valor", ascending=True).tail(10)
                            fig_shows = go.Figure(data=[go.Bar(
                                x=eventos_sorted['valor'],
                                y=eventos_sorted['evento'],
                                orientation='h',
                                marker=dict(
                                    color=colors_corporate['purple'],
                                    line=dict(color='#7c3aed', width=1)
                                ),
                                text=[brl(v) for v in eventos_sorted['valor']],
                                textposition='outside',
                                textfont=dict(size=11, family="Inter, sans-serif"),
                                hovertemplate="<b>%{y}</b><br>Receita: %{text}<extra></extra>"
                            )])
                            fig_shows.update_layout(
                                **chart_layout,
                                title=dict(text="Top 10 Shows por Receita", x=0.5, xanchor='center'),
                                height=max(350, len(eventos_sorted) * 40),
                                xaxis={**axis_style, 'title': 'Receita (R$)', 'showgrid': True},
                                yaxis={**axis_style, 'title': '', 'showgrid': False}
                            )
                            st.plotly_chart(fig_shows, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                            eventos_agg["Data"] = pd.to_datetime(eventos_agg["data"]).dt.strftime("%d/%m/%Y")
                            eventos_agg["Receita"] = eventos_agg["valor"].map(brl)
                            df_show = eventos_agg.sort_values("data", ascending=False)[["evento", "Data", "Receita", "publico"]]
                            df_show = df_show.rename(columns={"evento": "Evento", "publico": "Público"})
                            st.markdown('<div class="section-header">🎤 Lista de Shows/Eventos</div>', unsafe_allow_html=True)
                            st.dataframe(df_show, use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhum show registrado no período selecionado.")
                else:
                    st.info("Nenhum show encontrado no período selecionado.")

            with tab6:
                st.markdown('<div class="section-header">📉 Analytics Avançados</div>', unsafe_allow_html=True)
                
                # Calcular métricas específicas do Analytics
                qtd_shows_analytics = count_shows(dfp)
                ticket_medio_analytics = calcular_ticket_medio(dfp)
                
                # Seção 1: Comparação com Período Anterior
                st.markdown('<div class="card-container">', unsafe_allow_html=True)
                st.markdown("**📊 Comparação com Período Anterior**")
                
                col_comp1, col_comp2 = st.columns(2)
                
                with col_comp1:
                    st.markdown(f'<div class="period-badge">📅 Período Atual: {get_periodo_descricao(dt_min, dt_max)}</div>', unsafe_allow_html=True)
                    atual_kpis = [
                        {'icon': '💰', 'label': 'Receitas', 'value': brl(receitas), 'card_type': 'receitas'},
                        {'icon': '💸', 'label': 'Despesas', 'value': brl(despesas), 'card_type': 'despesas'},
                        {'icon': '📈', 'label': 'Resultado', 'value': brl(resultado), 'card_type': 'resultado'},
                        {'icon': '🎤', 'label': 'Shows (Analytics)', 'value': str(int(qtd_shows_analytics)), 'card_type': 'shows'},
                        {'icon': '🎫', 'label': 'Ticket Médio', 'value': brl(ticket_medio_analytics) if qtd_shows_analytics > 0 else "N/A", 'card_type': 'ticket'}
                    ]
                    st.markdown(render_kpi_cards(atual_kpis), unsafe_allow_html=True)
                
                with col_comp2:
                    st.markdown(f'<div class="period-badge">📅 Período Anterior: {get_periodo_descricao(dt_ant_min, dt_ant_max)}</div>', unsafe_allow_html=True)
                    ant_kpis = [
                        {
                            'icon': '💰', 'label': 'Receitas', 'value': brl(receitas_ant),
                            'delta': f"{cresc_receitas:+.1f}%" if cresc_receitas is not None else None,
                            'delta_type': 'positive' if cresc_receitas and cresc_receitas > 0 else 'negative',
                            'card_type': ''
                        },
                        {
                            'icon': '💸', 'label': 'Despesas', 'value': brl(despesas_ant),
                            'delta': f"{cresc_despesas:+.1f}%" if cresc_despesas is not None else None,
                            'delta_type': 'negative' if cresc_despesas and cresc_despesas > 0 else 'positive',
                            'card_type': ''
                        },
                        {
                            'icon': '📈', 'label': 'Resultado', 'value': brl(resultado_ant),
                            'delta': f"{cresc_resultado:+.1f}%" if cresc_resultado is not None else None,
                            'delta_type': 'positive' if cresc_resultado and cresc_resultado > 0 else 'negative',
                            'card_type': ''
                        }
                    ]
                    st.markdown(render_kpi_cards(ant_kpis), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Seção 2: Tendência do Ticket Médio por Show
                st.markdown('<div class="section-header">🎫 Tendência do Ticket Médio por Show</div>', unsafe_allow_html=True)
                base_shows_trend = df_com_data.loc[_only_shows_mask(df_com_data)].copy()
                if not base_shows_trend.empty:
                    base_shows_trend["ano_mes"] = base_shows_trend["data"].dt.to_period("M").astype(str)
                    
                    # Calcular ticket médio por mês usando funções unificadas
                    ticket_por_mes = []
                    for mes in sorted(base_shows_trend["ano_mes"].unique()):
                        df_mes = base_shows_trend[base_shows_trend["ano_mes"] == mes]
                        qtd_mes = count_shows(df_mes)
                        if qtd_mes > 0:
                            ticket_mes = calcular_ticket_medio(df_mes)
                            ticket_por_mes.append({"Mês": mes, "Ticket Médio": ticket_mes, "Shows": qtd_mes})
                    
                    if ticket_por_mes:
                        df_ticket = pd.DataFrame(ticket_por_mes)
                        st.markdown('<div class="card-container">', unsafe_allow_html=True)
                        fig_ticket = go.Figure()
                        fig_ticket.add_trace(go.Scatter(
                            x=df_ticket["Mês"], y=df_ticket["Ticket Médio"],
                            mode='lines+markers', name='Ticket Médio',
                            line=dict(color=colors_corporate['warning'], width=3),
                            marker=dict(size=10, color=colors_corporate['warning'], line=dict(color='white', width=2)),
                            fill='tozeroy',
                            fillcolor='rgba(245, 158, 11, 0.1)',
                            hovertemplate="<b>%{x}</b><br>Ticket Médio: R$ %{y:,.2f}<extra></extra>"
                        ))
                        fig_ticket.update_layout(
                            **chart_layout,
                            title=dict(text="Evolução do Ticket Médio por Show", x=0.5, xanchor='center'),
                            xaxis={**axis_style, 'title': 'Mês', 'showgrid': False},
                            yaxis={**axis_style, 'title': 'Ticket Médio (R$)', 'showgrid': True},
                            height=400, hovermode='x unified',
                            showlegend=False
                        )
                        st.plotly_chart(fig_ticket, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Tabela de detalhes
                        df_ticket["Ticket Médio Fmt"] = df_ticket["Ticket Médio"].map(brl)
                        st.dataframe(
                            df_ticket[["Mês", "Shows", "Ticket Médio Fmt"]].rename(columns={"Ticket Médio Fmt": "Ticket Médio"}),
                            use_container_width=True, hide_index=True
                        )
                    else:
                        st.info("Dados insuficientes para análise de tendência de ticket médio.")
                else:
                    st.info("Nenhum show encontrado para análise de tendência.")
                
                # Seção 3: Projeção de Fluxo de Caixa
                st.markdown('<div class="section-header">💰 Projeção de Fluxo de Caixa (próximos 3 meses)</div>', unsafe_allow_html=True)
                
                # Calcular médias mensais para projeção
                monthly_data = df_com_data.groupby(df_com_data["data"].dt.to_period("M")).agg(
                    receitas=("valor", lambda x: x[x > 0].sum()),
                    despesas=("valor", lambda x: -x[x < 0].sum())
                ).reset_index()
                monthly_data["data"] = monthly_data["data"].astype(str)
                
                if len(monthly_data) >= 2:
                    # Usar média dos últimos 3 meses para projeção
                    ultimos_meses = monthly_data.tail(3)
                    media_receitas = ultimos_meses["receitas"].mean()
                    media_despesas = ultimos_meses["despesas"].mean()
                    media_resultado = media_receitas - media_despesas
                    
                    # Criar projeção para próximos 3 meses
                    hoje = datetime.now()
                    projecao = []
                    saldo_acum = resultado  # Começar do resultado atual
                    
                    for i in range(1, 4):
                        mes_futuro = (hoje + timedelta(days=30*i)).strftime("%Y-%m")
                        saldo_acum += media_resultado
                        projecao.append({
                            "Mês": mes_futuro,
                            "Receitas Proj.": media_receitas,
                            "Despesas Proj.": media_despesas,
                            "Resultado Proj.": media_resultado,
                            "Saldo Acumulado": saldo_acum
                        })
                    
                    df_proj = pd.DataFrame(projecao)
                    
                    # Gráfico de projeção
                    st.markdown('<div class="card-container">', unsafe_allow_html=True)
                    fig_proj = go.Figure()
                    fig_proj.add_trace(go.Bar(
                        x=df_proj["Mês"], y=df_proj["Receitas Proj."],
                        name="Receitas Projetadas",
                        marker=dict(color=colors_corporate['success'], line=dict(color='#059669', width=1)),
                        hovertemplate="<b>%{x}</b><br>Receitas: R$ %{y:,.2f}<extra></extra>"
                    ))
                    fig_proj.add_trace(go.Bar(
                        x=df_proj["Mês"], y=df_proj["Despesas Proj."],
                        name="Despesas Projetadas",
                        marker=dict(color=colors_corporate['danger'], line=dict(color='#dc2626', width=1)),
                        hovertemplate="<b>%{x}</b><br>Despesas: R$ %{y:,.2f}<extra></extra>"
                    ))
                    fig_proj.add_trace(go.Scatter(
                        x=df_proj["Mês"], y=df_proj["Saldo Acumulado"],
                        mode='lines+markers', name='Saldo Acumulado',
                        line=dict(color=colors_corporate['info'], width=3),
                        marker=dict(size=10, color=colors_corporate['info'], line=dict(color='white', width=2)),
                        yaxis='y2',
                        hovertemplate="<b>%{x}</b><br>Saldo: R$ %{y:,.2f}<extra></extra>"
                    ))
                    fig_proj.update_layout(
                        **chart_layout,
                        title=dict(text="Projeção Financeira (baseada na média dos últimos 3 meses)", x=0.5, xanchor='center'),
                        xaxis={**axis_style, 'title': 'Mês', 'showgrid': False},
                        yaxis={**axis_style, 'title': 'Valor (R$)', 'showgrid': True},
                        yaxis2={**axis_style, 'title': 'Saldo Acumulado (R$)', 'overlaying': 'y', 'side': 'right', 'showgrid': False},
                        barmode='group',
                        height=450,
                        hovermode='x unified',
                        legend={**legend_base, 'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'center', 'x': 0.5}
                    )
                    st.plotly_chart(fig_proj, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Tabela de projeção
                    df_proj_display = df_proj.copy()
                    df_proj_display["Receitas Proj."] = df_proj_display["Receitas Proj."].map(brl)
                    df_proj_display["Despesas Proj."] = df_proj_display["Despesas Proj."].map(brl)
                    df_proj_display["Resultado Proj."] = df_proj_display["Resultado Proj."].map(brl)
                    df_proj_display["Saldo Acumulado"] = df_proj_display["Saldo Acumulado"].map(brl)
                    st.dataframe(df_proj_display, use_container_width=True, hide_index=True)
                    
                    st.caption("⚠️ Projeção baseada na média histórica dos últimos 3 meses. Valores reais podem variar.")
                else:
                    st.info("Dados históricos insuficientes para projeção. São necessários pelo menos 2 meses de dados.")
                
                # Seção 4: Análise de Sazonalidade
                st.markdown('<div class="section-header">📅 Análise de Sazonalidade</div>', unsafe_allow_html=True)
                if len(df_com_data) > 0:
                    df_com_data_copy = df_com_data.copy()
                    df_com_data_copy["mes_nome"] = df_com_data_copy["data"].dt.month_name()
                    df_com_data_copy["mes_num"] = df_com_data_copy["data"].dt.month
                    
                    sazonalidade = df_com_data_copy.groupby(["mes_num", "mes_nome"]).agg(
                        receitas=("valor", lambda x: x[x > 0].sum()),
                        despesas=("valor", lambda x: -x[x < 0].sum()),
                        transacoes=("valor", "count")
                    ).reset_index().sort_values("mes_num")
                    
                    sazonalidade["resultado"] = sazonalidade["receitas"] - sazonalidade["despesas"]
                    
                    st.markdown('<div class="card-container">', unsafe_allow_html=True)
                    fig_saz = go.Figure()
                    fig_saz.add_trace(go.Bar(
                        x=sazonalidade["mes_nome"], y=sazonalidade["receitas"],
                        name="Receitas",
                        marker=dict(color=colors_corporate['success'], line=dict(color='#059669', width=1)),
                        hovertemplate="<b>%{x}</b><br>Receitas: R$ %{y:,.2f}<extra></extra>"
                    ))
                    fig_saz.add_trace(go.Bar(
                        x=sazonalidade["mes_nome"], y=sazonalidade["despesas"],
                        name="Despesas",
                        marker=dict(color=colors_corporate['danger'], line=dict(color='#dc2626', width=1)),
                        hovertemplate="<b>%{x}</b><br>Despesas: R$ %{y:,.2f}<extra></extra>"
                    ))
                    fig_saz.update_layout(
                        **chart_layout,
                        title=dict(text="Receitas e Despesas por Mês do Ano (Sazonalidade)", x=0.5, xanchor='center'),
                        xaxis={**axis_style, 'title': 'Mês', 'showgrid': False},
                        yaxis={**axis_style, 'title': 'Valor (R$)', 'showgrid': True},
                        barmode='group',
                        height=400,
                        legend={**legend_base, 'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'center', 'x': 0.5}
                    )
                    st.plotly_chart(fig_saz, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Identificar melhor e pior mês
                    melhor_mes = sazonalidade.loc[sazonalidade["resultado"].idxmax()]
                    pior_mes = sazonalidade.loc[sazonalidade["resultado"].idxmin()]
                    
                    # KPI cards for best and worst months
                    saz_kpis = [
                        {'icon': '📈', 'label': f'Melhor Mês: {melhor_mes["mes_nome"]}', 'value': brl(melhor_mes['resultado']), 'card_type': 'receitas'},
                        {'icon': '📉', 'label': f'Pior Mês: {pior_mes["mes_nome"]}', 'value': brl(pior_mes['resultado']), 'card_type': 'despesas'}
                    ]
                    st.markdown(render_kpi_cards(saz_kpis), unsafe_allow_html=True)

# =============================================================================
# REGISTRAR NOVO LANÇAMENTO
# =============================================================================
elif page == "📝 Registrar":
    st.markdown('<p class="main-header">📝 Registrar Novo Lançamento</p>', unsafe_allow_html=True)
    
    with st.form("novo_lancamento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            data_lancamento = st.date_input("📅 Data do Lançamento", value=datetime.today(), format="DD/MM/YYYY")
            tipo = st.selectbox("💵 Tipo", ["Entrada", "Saída"])
            valor = st.number_input("💰 Valor (R$)", value=0.0, step=10.0, min_value=0.0, format="%.2f")
            
        with col2:
            categorias = ["Investimento Pessoal", "Shows", "Vendas Merchandising", "Rendimentos", "Ensaios", 
                         "Aluguel de equipamentos", "Equipe Técnica", "Produção", "Músico Freelancer", 
                         "Merchandising", "Fotografia", "Marketing Digital", "Logistica", "Equipamentos", 
                         "Alimentação", "Cachês – Músicos", "Outros"]
            categoria = st.selectbox("🏷️ Categoria", categorias)
            contas = ["Dinheiro", "Pix", "Cartão de Crédito", "Cartão de Débito", "Transferência", "Boleto", "Nota Fiscal", "Outros"]
            conta = st.selectbox("💳 Forma de Pagamento", contas)
        
        descricao = st.text_area("📝 Descrição", placeholder="Descreva o lançamento...")
        
        col3, col4, col5 = st.columns(3)
        with col3:
            evento = st.text_input("🎤 Evento/Show", placeholder="Nome do evento/show...")
        with col4:
            responsavel = st.text_input("👤 Responsável", placeholder="Quem registrou...")
        with col5:
            publico = st.number_input("👥 Público", value=0, step=1, min_value=0)
        
        tags = st.text_input("🏷️ Tags", placeholder="tags, separadas, por, vírgula")
        
        submitted = st.form_submit_button("💾 Salvar Lançamento", type="primary", use_container_width=True)
        
        if submitted:
            try:
                # Aplicar sinal ao valor baseado no tipo
                valor_final = valor if tipo == "Entrada" else -valor
                
                nova_linha = [
                    data_lancamento.strftime("%Y-%m-%d"),
                    tipo,
                    categoria,
                    descricao,
                    conta,
                    valor_final,
                    responsavel,
                    evento,
                    int(publico),
                    tags
                ]
                
                append_rows("lancamentos", [nova_linha])
                st.cache_data.clear()
                st.success("✅ Lançamento registrado com sucesso!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erro ao registrar lançamento: {e}")

# =============================================================================
# LANÇAMENTOS (com _row para editar/excluir)
# =============================================================================
elif page == "📒 Lançamentos":
    st.markdown('<p class="main-header">📒 Histórico de Lançamentos</p>', unsafe_allow_html=True)
    df = read_sheet("lancamentos")
    if df.empty:
        st.info("📭 Sem registros ainda. Use a aba **Registrar** para adicionar os primeiros.")
    else:
        st.markdown('<div class="section-header">🔍 Filtros</div>', unsafe_allow_html=True)
        colf1, colf2, colf3, colf4, colf5 = st.columns(5)
        with colf1:
            base_data = pd.to_datetime(df["data"])
            base_min = base_data.dropna().min().date() if base_data.notna().any() else datetime.today().date()
            base_max = base_data.dropna().max().date() if base_data.notna().any() else datetime.today().date()
            dt_min = st.date_input("📅 De", value=base_min, format="DD/MM/YYYY")
        with colf2:
            dt_max = st.date_input("📅 Até", value=base_max, format="DD/MM/YYYY")
        with colf3:
            tipo_options = ["Todos"] + sorted(df["tipo"].dropna().unique().tolist())
            tipo_sel = st.selectbox("💵 Tipo", options=tipo_options)
        with colf4:
            cat_options = ["Todas"] + sorted(df["categoria"].dropna().unique().tolist())
            categoria_sel = st.selectbox("🏷️ Categoria", options=cat_options)
        with colf5:
            busca_texto = st.text_input("🔎 Buscar", placeholder="Buscar na descrição...")

        inclui_sem_data = st.checkbox("Incluir linhas sem data", value=True)

        if dt_min > dt_max:
            dt_min, dt_max = dt_max, dt_min

        base = df.copy()
        com_data = base[base["data"].notna()]
        sem_data = base[base["data"].isna()]

        m = (com_data["data"].dt.date >= dt_min) & (com_data["data"].dt.date <= dt_max)
        if tipo_sel != "Todos":
            m &= com_data["tipo"] == tipo_sel
        if categoria_sel != "Todas":
            m &= com_data["categoria"] == categoria_sel
        if busca_texto:
            m &= com_data["descricao"].str.contains(busca_texto, case=False, na=False)

        view = com_data.loc[m]

        if tipo_sel != "Todos":
            sem_data = sem_data[sem_data["tipo"] == tipo_sel]
        if categoria_sel != "Todas":
            sem_data = sem_data[sem_data["categoria"] == categoria_sel]
        if busca_texto:
            sem_data = sem_data[sem_data["descricao"].str.contains(busca_texto, case=False, na=False)]

        if inclui_sem_data and not sem_data.empty:
            view = pd.concat([view, sem_data], axis=0, ignore_index=False)

        view = view.sort_values(["data"], ascending=False)

        receitas_filtro = view.loc[view["valor"] > 0, "valor"].sum()
        despesas_filtro = -view.loc[view["valor"] < 0, "valor"].sum()
        resultado_filtro = receitas_filtro - despesas_filtro
        
        lancamentos_kpis = [
            {'icon': '📊', 'label': 'Total de Registros', 'value': str(len(view)), 'card_type': ''},
            {'icon': '💰', 'label': 'Receitas', 'value': brl(receitas_filtro), 'card_type': 'receitas'},
            {'icon': '💸', 'label': 'Despesas', 'value': brl(despesas_filtro), 'card_type': 'despesas'},
            {'icon': '📈', 'label': 'Resultado', 'value': brl(resultado_filtro), 'card_type': 'resultado' if resultado_filtro >= 0 else 'despesas'}
        ]
        st.markdown(render_kpi_cards(lancamentos_kpis), unsafe_allow_html=True)

        if not view.empty:
            view_disp = view.copy()
            view_disp["Data"] = view_disp["data"].pipe(lambda s: s.dt.strftime("%d/%m/%Y")).fillna("—")
            view_disp["Valor"] = view_disp["valor"].map(brl)
            view_disp["Mov"] = view_disp["tipo"].map({"Entrada": "⬆️", "Saída": "⬇️"})

            cols_show = ["Data","Mov","tipo","categoria","descricao","conta","Valor","quem","evento","publico"]
            cols_show = [c for c in cols_show if c in view_disp.columns]
            df_show = dedupe_columns(
                view_disp[cols_show].rename(columns={
                    "tipo":"Tipo","categoria":"Categoria","descricao":"Descrição",
                    "conta":"Pagamento","quem":"Responsável","evento":"Evento","publico":"Público"
                })
            )
            st.markdown('<div class="section-header">📋 Lançamentos</div>', unsafe_allow_html=True)
            st.dataframe(df_show, use_container_width=True, hide_index=True)

            # ---- Edição simplificada (com _row)
            st.markdown('<div class="section-header">✏️ Editar Lançamentos</div>', unsafe_allow_html=True)

            lancamentos_lista = []
            for idx, row in view.iterrows():
                desc = (row['descricao'][:30] + "...") if isinstance(row['descricao'], str) and len(row['descricao']) > 30 else str(row['descricao'])
                data_txt = row["data"].strftime('%d/%m/%Y') if pd.notna(row["data"]) else "—"
                texto = f"{data_txt} | {row['tipo']} | {row['categoria']} | {brl(abs(row['valor']))} | {desc}"
                lancamentos_lista.append((idx, texto))

            if lancamentos_lista:
                opcoes = [f"{i}: {texto}" for i, (idx, texto) in enumerate(lancamentos_lista)]
                selecao = st.selectbox("Escolha um lançamento:", options=opcoes, index=0, key="sel_lcto")
                indice_selecionado = int(selecao.split(":")[0])
                idx_original, texto_lancamento = lancamentos_lista[indice_selecionado]
                lancamento = view.loc[idx_original]

                st.markdown("---")
                st.markdown(f"#### Editando: {texto_lancamento}")

                with st.form(f"editar_{idx_original}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        default_date = lancamento["data"].date() if pd.notna(lancamento["data"]) else datetime.today().date()
                        nova_data = st.date_input("Data", value=default_date, format="DD/MM/YYYY")
                        novoTipo = st.selectbox("Tipo", ["Entrada","Saída"], index=0 if lancamento["tipo"]=="Entrada" else 1)
                        valor_abs = float(abs(lancamento["valor"]))
                        novo_valor = st.number_input("Valor (R$)", value=valor_abs, step=10.0, min_value=0.0, format="%.2f")
                        categorias_sugeridas = ["Investimento Pessoal","Shows","Vendas Merchandising","Rendimentos","Ensaios","Aluguel de equipamentos","Equipe Técnica","Produção","Músico Freelancer","Merchandising","Fotografia","Marketing Digital","Logistica","Equipamentos","Alimentação","Cachês – Músicos","Outros"]
                        categoria_atual = lancamento["categoria"] if lancamento["categoria"] in categorias_sugeridas else "Outros"
                        nova_categoria = st.selectbox("Categoria",categorias_sugeridas,
                        index=categorias_sugeridas.index(categoria_atual) if categoria_atual in categorias_sugeridas else categorias_sugeridas.index("Outros")
)
                    with col2:
                        contas_sugeridas = ["Dinheiro","Pix","Cartão de Crédito","Cartão de Débito","Transferência","Boleto", "Nota Fiscal","Outros"]
                        conta_atual = lancamento["conta"] if lancamento["conta"] in contas_sugeridas else "Outros"
                        nova_conta = st.selectbox("Forma de Pagamento", contas_sugeridas, index=(contas_sugeridas.index(conta_atual) if conta_atual in contas_sugeridas else 0))
                        novo_evento = st.text_input("Evento/Show", value=lancamento.get("evento",""))
                        novo_quem = st.text_input("Responsável", value=lancamento.get("quem",""))
                        novo_publico = st.number_input("Público", value=int(lancamento.get("publico", 0) or 0), step=1, min_value=0)

                    nova_descricao = st.text_area("Descrição", value=lancamento.get("descricao",""), height=80)
                    novas_tags = st.text_input("Tags", value=lancamento.get("tags",""))

                    col_btn1, col_btn2 = st.columns(2)
                    salvar_edicao = col_btn1.form_submit_button("💾 Salvar Alterações", type="primary", use_container_width=True)
                    excluir = col_btn2.form_submit_button("🗑️ Excluir", use_container_width=True)

                if salvar_edicao:
                    try:
                        sign = 1 if novoTipo == "Entrada" else -1
                        novo_valor_com_sinal = sign * float(novo_valor)
                        linha_sheets = int(lancamento["_row"])  # <— linha real no Sheets
                        
                        # Define os nomes dos campos e seus valores correspondentes
                        # Isso garante que os valores sejam mapeados para as colunas corretas
                        # independentemente da ordem das colunas na planilha
                        field_names = ["data", "tipo", "categoria", "descricao", "conta", "valor", "quem", "evento", "publico", "tags"]
                        nova_linha = [
                            pd.to_datetime(nova_data).strftime("%Y-%m-%d"),
                            novoTipo, nova_categoria, nova_descricao, nova_conta,
                            novo_valor_com_sinal, novo_quem, novo_evento, int(novo_publico), novas_tags
                        ]
                        update_row("lancamentos", linha_sheets, nova_linha, field_names=field_names)
                        st.cache_data.clear()
                        st.success("✅ Lançamento atualizado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao atualizar: {e}")

                if excluir:
                    st.session_state["confirm_delete_idx"] = idx_original

                if st.session_state.get("confirm_delete_idx") == idx_original:
                    st.warning("⚠️ Confirmar exclusão deste lançamento?")
                    col_c1, col_c2 = st.columns(2)
                    if col_c1.button("✅ Sim, excluir", key=f"confirm_excluir_{idx_original}", use_container_width=True):
                        try:
                            linha_sheets = int(lancamento["_row"])
                            delete_row("lancamentos", linha_sheets)
                            st.cache_data.clear()
                            st.success("✅ Lançamento excluído com sucesso!")
                            st.session_state.pop("confirm_delete_idx", None)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro ao excluir: {e}")
                    if col_c2.button("❌ Cancelar", key=f"cancel_excluir_{idx_original}", use_container_width=True):
                        st.info("Exclusão cancelada.")
                        st.session_state.pop("confirm_delete_idx", None)

            # Exportações
            st.markdown("---")
            st.markdown("### 📤 Exportar Dados")
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.download_button(
                    "📥 Baixar CSV",
                    data=view.to_csv(index=False).encode("utf-8"),
                    file_name=f"lancamentos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_a2:
                # Excel export requires openpyxl engine (added to requirements.txt)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    view.to_excel(writer, index=False, sheet_name='Lancamentos')
                st.download_button(
                    "📥 Baixar Excel",
                    data=output.getvalue(),
                    file_name=f"lancamentos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.info("🔍 Nenhum registro encontrado com os filtros aplicados.")

# =============================================================================
# FECHAMENTO
# =============================================================================
elif page == "🧾 Fechamento":
    st.markdown('<p class="main-header">🧾 Fechamento Mensal & Rateio</p>', unsafe_allow_html=True)
    df_all = read_sheet("lancamentos")

    if df_all.empty or df_all["data"].isna().all():
        st.info("📭 Sem registros com data. Use a aba Registrar/Importar.")
    else:
        df = df_all.dropna(subset=["data"]).copy()
        df["ano_mes"] = df["data"].dt.to_period("M").astype(str)

        colf1, colf2 = st.columns([3,1])
        with colf1:
            # Adicionar "Todo período" como opção
            meses = ["Todo período"] + sorted(df["ano_mes"].unique().tolist(), reverse=True)
            mes_sel = st.selectbox("📅 Selecione o Período", options=meses, index=0)
        with colf2:
            if st.button("🔄 Atualizar", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        # Filtrar por período selecionado
        if mes_sel == "Todo período":
            dfm = df.copy()
            periodo_titulo = "Todo Período"
        else:
            dfm = df.loc[df["ano_mes"] == mes_sel].copy()
            periodo_titulo = mes_sel

        dfm["valor"] = pd.to_numeric(dfm["valor"], errors="coerce").fillna(0)

        receitas = dfm.loc[dfm["valor"] > 0, "valor"].sum()
        despesas = -dfm.loc[dfm["valor"] < 0, "valor"].sum()
        resultado = receitas - despesas
        qtd_shows = count_shows(dfm)

        st.markdown(f'<div class="period-badge">📅 {periodo_titulo}</div>', unsafe_allow_html=True)
        
        fechamento_kpis = [
            {'icon': '💰', 'label': 'Receitas', 'value': brl(receitas), 'card_type': 'receitas'},
            {'icon': '💸', 'label': 'Despesas', 'value': brl(despesas), 'card_type': 'despesas'},
            {'icon': '📈', 'label': 'Resultado', 'value': brl(resultado), 'card_type': 'resultado' if resultado >= 0 else 'despesas'},
            {'icon': '🎤', 'label': 'Shows', 'value': str(int(qtd_shows)), 'card_type': 'shows'}
        ]
        st.markdown(render_kpi_cards(fechamento_kpis), unsafe_allow_html=True)

        # Remover a tab de Centro de Custo e manter apenas Rateio Fixo
        tab1, tab2 = st.tabs(["⚙️ Config. Rateio Fixo", "💰 Resultado Final"])

        with tab1:
            st.markdown('<div class="section-header">⚙️ Configuração de Rateio Fixo</div>', unsafe_allow_html=True)
            st.info("💡 **Rateio fixo:** Cada membro recebe um percentual fixo do resultado total da banda.")
            
            # Lê configuração de rateio; se estiver vazia, será sobrescrita com valores padrão
            cfg = read_rateio_config()
            if cfg.empty:
                cfg = pd.DataFrame([
                    {"membro":"Murillo","percentual":16.66,"ativo":True,"metodo":"fixo"},
                    {"membro":"Helio","percentual":16.67,"ativo":True,"metodo":"fixo"},
                    {"membro":"Tay","percentual":16.66,"ativo":True,"metodo":"fixo"},
                    {"membro":"Everton","percentual":16.67,"ativo":True,"metodo":"fixo"},
                    {"membro":"Kiko","percentual":16.67,"ativo":True,"metodo":"fixo"},
                    {"membro":"Naldo","percentual":16.67,"ativo":True,"metodo":"fixo"}
                ])
            
            # Garantir que a coluna 'ativo' existe
            if 'ativo' not in cfg.columns:
                cfg['ativo'] = True
            
            cfg["metodo"] = "fixo"
            edit_cfg = st.data_editor(
                cfg[["membro","percentual","ativo","metodo"]],
                num_rows="dynamic", use_container_width=True, key="rateio_fixo_editor",
                column_config={
                    "membro": st.column_config.TextColumn("👤 Membro", required=True),
                    "percentual": st.column_config.NumberColumn("📊 Percentual (%)", min_value=0, max_value=100, format="%.2f"),
                    "ativo": st.column_config.CheckboxColumn("✅ Ativo"),
                    "metodo": st.column_config.TextColumn("Método", disabled=True)
                }
            )
            
            total_pct = float(pd.to_numeric(edit_cfg["percentual"], errors="coerce").fillna(0).sum())
            col_pct1, col_pct2 = st.columns([1,3])
            
            if abs(total_pct-100) <= 0.01:
                col_pct1.success(f"✅ Total: {total_pct:.2f}%")
            else:
                col_pct1.error(f"⚠️ Total: {total_pct:.2f}% (deve ser 100%)")
                
            if col_pct2.button("💾 Salvar Configuração de Rateio Fixo", use_container_width=True, type="primary"):
                if abs(total_pct-100) <= 0.01:
                    save_rateio_config(edit_cfg)
                    st.success("✅ Configuração salva com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Ajuste os percentuais para totalizar 100%!")

        with tab2:
            st.markdown('<div class="section-header">💰 Cálculo do Rateio</div>', unsafe_allow_html=True)
            
            # Lê a configuração atualizada
            cfg = read_rateio_config().copy()
            
            # Garantir que a coluna 'ativo' existe e tratar valores nulos
            if 'ativo' not in cfg.columns:
                cfg['ativo'] = True
            cfg['ativo'] = cfg['ativo'].fillna(True)
            
            ativo = cfg.loc[cfg["ativo"] == True].copy()
            
            if ativo.empty:
                st.warning("⚠️ Nenhum membro ativo configurado. Configure os membros na aba 'Config. Rateio Fixo'.")
            else:
                ativo["percentual"] = pd.to_numeric(ativo["percentual"], errors="coerce").fillna(0) / 100.0
                ativo["valor"] = ativo["percentual"] * resultado
                
                # Formatar para exibição
                ativo["valor_fmt"] = ativo["valor"].map(brl)
                ativo["percentual_fmt"] = (ativo["percentual"] * 100).map(lambda x: f"{x:.2f}%")
                
                st.markdown('<div class="section-header">📊 Distribuição do Resultado</div>', unsafe_allow_html=True)
                
                # Gráfico de pizza com estilo corporativo moderno
                st.markdown('<div class="card-container">', unsafe_allow_html=True)
                colors_rateio = ['#1e3a5f', '#2d5a87', '#3b82f6', '#60a5fa', '#93c5fd', '#8b5cf6', '#a78bfa', '#10b981']
                fig = go.Figure(data=[go.Pie(
                    labels=ativo["membro"],
                    values=ativo["valor"],
                    hole=0.5,
                    marker=dict(colors=colors_rateio[:len(ativo)]),
                    textinfo='label+percent',
                    textfont=dict(size=12, family="Inter, sans-serif"),
                    hovertemplate="<b>%{label}</b><br>Valor: R$ %{value:,.2f}<br>Percentual: %{percent}<extra></extra>"
                )])
                fig.update_layout(
                    font=dict(family="Inter, sans-serif", size=12, color="#1e293b"),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    title=dict(text=f"Distribuição do Resultado - {periodo_titulo}", x=0.5, xanchor='center', font=dict(size=16, color='#1e3a5f')),
                    height=420,
                    showlegend=True,
                    legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5, bgcolor='rgba(255,255,255,0.8)')
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="section-header">💵 Valores por Membro</div>', unsafe_allow_html=True)
                
                # Tabela com valores
                df_display = dedupe_columns(
                    ativo[["membro","percentual_fmt","valor_fmt"]].rename(
                        columns={
                            "membro":"👤 Membro",
                            "percentual_fmt":"📊 Percentual",
                            "valor_fmt":"💰 Valor"
                        }
                    )
                )
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                # Botão de download
                st.download_button(
                    "📥 Baixar Rateio (CSV)",
                    data=ativo[["membro","percentual","valor"]].to_csv(index=False).encode("utf-8"),
                    file_name=f"rateio_fixo_{mes_sel.replace('/', '-')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                # Resumo financeiro adicional com KPI cards
                st.markdown('<div class="section-header">📋 Resumo Financeiro</div>', unsafe_allow_html=True)
                resumo_kpis = [
                    {'icon': '💵', 'label': 'Resultado Total', 'value': brl(resultado), 'card_type': 'resultado' if resultado >= 0 else 'despesas'},
                    {'icon': '👥', 'label': 'Membros Ativos', 'value': str(len(ativo)), 'card_type': ''},
                    {'icon': '📊', 'label': 'Média por Membro', 'value': brl(resultado / len(ativo) if len(ativo) > 0 else 0), 'card_type': ''}
                ]
                st.markdown(render_kpi_cards(resumo_kpis), unsafe_allow_html=True)

# =============================================================================
# IMPORTAR EXCEL
# =============================================================================
elif page == "⬆️ Importar Excel":
    st.markdown('<p class="main-header">⬆️ Importar Planilha Excel</p>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📋 Instruções</div>', unsafe_allow_html=True)
    st.markdown("""
    - Faça upload de um arquivo Excel (.xlsx ou .xls)
    - O sistema detectará automaticamente as colunas
    - Colunas esperadas: **Data**, **Entrada/Saída**, **Descrição**, **Valor**, **Categoria**
    """)

    upl = st.file_uploader("📂 Selecione o arquivo Excel", type=["xlsx","xls"])
    if upl is not None:
        with st.spinner("🔄 Processando arquivo..."):
            parsed = parse_legacy_excel(upl.read())

        if parsed.empty:
            st.error("❌ Não foi possível identificar as colunas. Verifique o formato do arquivo.")
        else:
            st.success(f"✅ Foram lidas **{len(parsed)}** linhas do arquivo!")
            st.markdown("### 👀 Preview dos Dados")
            st.dataframe(parsed.head(20), use_container_width=True)

            st.markdown("### 📊 Estatísticas da Importação")
            col_i1, col_i2, col_i3, col_i4 = st.columns(4)
            receitas_imp = parsed.loc[parsed["valor"] > 0, "valor"].sum()
            despesas_imp = -parsed.loc[parsed["valor"] < 0, "valor"].sum()
            col_i1.metric("Total de Linhas", len(parsed))
            col_i2.metric("Receitas", brl(receitas_imp))
            col_i3.metric("Despesas", brl(despesas_imp))
            col_i4.metric("Resultado", brl(receitas_imp - despesas_imp))

            st.markdown("---")
            st.warning("⚠️ Esta ação adicionará todos os registros ao Google Sheets.")
            col_btn1, col_btn2 = st.columns([1,1])

            if col_btn1.button("✅ Confirmar Importação", use_container_width=True, type="primary"):
                try:
                    with st.spinner("📤 Enviando dados para o Google Sheets..."):
                        rows = []
                        for _, r in parsed.iterrows():
                            rows.append([
                                (pd.to_datetime(r.get("data")).strftime("%Y-%m-%d") if pd.notna(r.get("data")) else ""),
                                r.get("tipo", ""), 
                                r.get("categoria", "Outros"),
                                r.get("descricao", ""), 
                                r.get("conta", ""),
                                float(r.get("valor", 0) or 0), 
                                "import", 
                                "", 
                                "", 
                                "legacy"
                            ])
                        append_rows("lancamentos", rows)
                        st.cache_data.clear()
                    st.success(f"🎉 Importação concluída! {len(parsed)} registros foram adicionados.")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Falha na importação: {e}")

            csv_preview = parsed.to_csv(index=False).encode("utf-8")
            col_btn2.download_button(
                "📥 Baixar Preview (CSV)", data=csv_preview,
                file_name=f"preview_importacao_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv", use_container_width=True
            )

# =============================================================================
# RODAPÉ / STATUS
# =============================================================================
st.markdown("---")
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔌 Status da Conexão")
    try:
        gc, sheet_id = get_sheet_client()
        if not (gc and sheet_id):
            st.error("❌ Google Sheets não configurado")
            st.caption("Configure em secrets.toml → [gcp] com credenciais e sheet_id")
        else:
            st.success("✅ Conectado ao Sheets")
            st.caption(f"ID: {str(sheet_id)[:20]}...")

            if st.button("🧪 Teste de Conexão", use_container_width=True):
                try:
                    sh = gc.open_by_key(sheet_id)
                    ws = ensure_ws_with_header(sh, "lancamentos")
                    ws.append_row(
                        [datetime.now().strftime("%Y-%m-%d"), "Entrada", "Debug", "Teste", "Pix", 0.01, "Sistema", "Teste", "conexao"],
                        value_input_option="USER_ENTERED",
                    )
                    st.cache_data.clear()
                    st.success("✅ Teste realizado com sucesso!")
                except Exception as e:
                    st.error(f"❌ Falha no teste: {e}")
    except Exception as e:
        st.error(f"❌ Erro: {e}")

    st.markdown("---")
    st.markdown("### ℹ️ Sobre")
    st.caption("**Rockbuzz - Gestão Financeira**")
    st.caption("Versão 2.3.0")
    st.caption("© 2025 - Todos os direitos reservados")