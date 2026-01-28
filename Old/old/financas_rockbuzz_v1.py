from __future__ import annotations

import io
from datetime import datetime, timedelta, date
from typing import List, Optional

import numpy as np
import pandas as pd
import re       
import plotly.express as px
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

# CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem; font-weight: bold; color: #FF4B4B;
        text-align: center; margin-bottom: 2rem;
    }
    .stAlert { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

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
    Se 'evento' estiver preenchido em >=60% das linhas, deduplica por evento (case-insensitive);
    senão, conta linhas.
    """
    if df is None or df.empty:
        return 0
    base = df.loc[_only_shows_mask(df)].copy()
    if base.empty:
        return 0

    if "evento" in base.columns:
        ev = base["evento"].astype(str).str.strip()
        filled = ev.ne("").sum()
        if len(base) > 0 and filled / len(base) >= 0.60:
            return int(ev[ev.ne("")].str.casefold().nunique())

    return int(len(base))

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
    cfg = st.secrets.get("gcp", None)
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
        ws.append_row(["data","tipo","categoria","descricao","conta","valor","quem","evento","tags"])
    return ws

# =============================================================================
# LEITURA / ESCRITA (com _row estável)
# =============================================================================
@st.cache_data(show_spinner=False, ttl=120)
def read_sheet(sheet_name: str = "lancamentos") -> pd.DataFrame:
    """
    Lê dados do Google Sheets e:
    - normaliza cabeçalhos (minúsculo/sem acento) + aliases
    - cria coluna `_row` com o índice real da linha na planilha (0-based)
    - NÃO remove linhas sem data (para não "sumirem" na tela de Lançamentos)
    """
    gc, sheet_id = get_sheet_client()
    if not (gc and sheet_id):
        return pd.DataFrame(columns=["data","tipo","categoria","descricao","conta","valor","quem","evento","tags","_row"])

    sh = gc.open_by_key(sheet_id)
    ws = ensure_ws_with_header(sh, sheet_name)
    rows = ws.get_all_values()
    if not rows:
        return pd.DataFrame(columns=["data","tipo","categoria","descricao","conta","valor","quem","evento","tags","_row"])

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
    df = coalesce(df, "tags",      [c for c in df.columns if c != "tags" and "tag" in c])

    for c in ["data","tipo","categoria","descricao","conta","valor","quem","evento","tags"]:
        if c not in df.columns:
            df[c] = ""

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    for c in ["tipo","categoria","descricao","conta","quem","evento","tags"]:
        df[c] = df[c].astype(str).str.strip()

    df["valor_raw"] = df["valor"]
    df["valor"] = normalize_valor_series(df["valor"]).fillna(0.0)

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

def update_row(sheet_name: str, row_index: int, new_data: List):
    gc, sheet_id = get_sheet_client()
    if not (gc and sheet_id):
        raise RuntimeError("Google Sheets não configurado.")
    sh = gc.open_by_key(sheet_id)
    ws = ensure_ws_with_header(sh, sheet_name)
    ws.update(f'A{row_index+2}:I{row_index+2}', [new_data], value_input_option="USER_ENTERED")

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
with st.sidebar:
    st.markdown("# 🎸 Rockbuzz")
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

            st.markdown(f"### 📊 Visão Geral: {get_periodo_descricao(dt_min, dt_max)}")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("💰 Receitas", brl(receitas))
            c2.metric("💸 Despesas", brl(despesas))
            c3.metric("📈 Resultado", brl(resultado), delta=f"{(resultado/receitas*100):.1f}%" if receitas else None)
            c4.metric("🎤 Shows", int(qtd_shows))
            c5.metric("🎫 Ticket Médio", brl(ticket_medio) if qtd_shows > 0 else "N/A")

            st.markdown("---")
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Visão Geral", "💰 Receitas vs Despesas", "📈 Evolução", "🏷️ Categorias", "🎤 Análise de Shows"
            ])

            with tab1:
                col_a, col_b = st.columns(2)
                with col_a:
                    fig_pizza = go.Figure(data=[go.Pie(
                        labels=["Receitas", "Despesas"],
                        values=[max(receitas, 0), max(despesas, 0)],
                        hole=.4
                    )])
                    fig_pizza.update_layout(title="Distribuição: Receitas vs Despesas", height=400)
                    st.plotly_chart(fig_pizza, use_container_width=True)
                with col_b:
                    top_desp = dfp.loc[dfp["valor"] < 0].copy()
                    if not top_desp.empty:
                        top_desp["categoria"] = top_desp["categoria"].replace("", "Sem categoria")
                        top_cat = top_desp.groupby("categoria")["valor"].sum().abs().sort_values(ascending=False).head(5)
                        fig_top = px.bar(
                            x=top_cat.values, y=top_cat.index, orientation='h',
                            title="Top 5 Categorias de Despesa", labels={'x':'Valor (R$)','y':'Categoria'},
                            color=top_cat.values, color_continuous_scale='Reds'
                        )
                        fig_top.update_layout(height=400, showlegend=False)
                        st.plotly_chart(fig_top, use_container_width=True)
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
                    fig = go.Figure()
                    fig.add_bar(x=monthly["ano_mes"], y=monthly["Receitas"], name="Receitas")
                    fig.add_bar(x=monthly["ano_mes"], y=monthly["Despesas"], name="Despesas")
                    fig.update_layout(title="Receitas vs Despesas por Mês", barmode='group',
                                      xaxis_title="Mês", yaxis_title="Valor (R$)", height=500, hovermode='x unified')
                    st.plotly_chart(fig, use_container_width=True)

                    monthly["Resultado"] = monthly["Receitas"] - monthly["Despesas"]
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
                    st.markdown("#### 📋 Resumo Mensal")
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
                    fig_evol = go.Figure()
                    fig_evol.add_trace(go.Scatter(
                        x=dd["data"], y=dd["saldo_acumulado"],
                        mode='lines+markers', name='Saldo Acumulado',
                        fill='tozeroy', fillcolor='rgba(52, 152, 219, 0.2)'
                    ))
                    fig_evol.update_layout(title="Evolução do Saldo Acumulado",
                                           xaxis_title="Data", yaxis_title="Saldo (R$)", height=500, hovermode='x unified')
                    st.plotly_chart(fig_evol, use_container_width=True)
                    saldo_ini = float(dd["saldo_acumulado"].iloc[0]) if len(dd) else 0.0
                    saldo_fim = float(dd["saldo_acumulado"].iloc[-1]) if len(dd) else 0.0
                    variacao = saldo_fim - saldo_ini
                    media_dia = float(dd["saldo_dia"].mean() if len(dd) else 0.0)
                    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
                    col_e1.metric("Saldo Inicial", brl(saldo_ini))
                    col_e2.metric("Saldo Final", brl(saldo_fim))
                    col_e3.metric("Variação", brl(variacao), delta=f"{(variacao/abs(saldo_ini)*100):.1f}%" if saldo_ini else None)
                    col_e4.metric("Média Diária", brl(media_dia))

            with tab4:
                cat = dfp.copy()
                cat["categoria"] = cat["categoria"].replace("", "Sem categoria")
                cat_agg = cat.groupby("categoria", dropna=False)["valor"].sum().reset_index().sort_values("valor", ascending=True)
                if cat_agg.empty:
                    st.info("Sem categorias no período.")
                else:
                    fig_cat = px.bar(
                        cat_agg, x="valor", y="categoria", orientation='h',
                        title="Saldo por Categoria", labels={'valor':'Saldo (R$)','categoria':'Categoria'},
                        color='valor', color_continuous_scale=['red','yellow','green']
                    )
                    fig_cat.update_layout(height=600)
                    st.plotly_chart(fig_cat, use_container_width=True)

                    cat_det = cat.groupby("categoria").agg(Total=("valor","sum"), Qtd=("valor","count"), Média=("valor","mean")).reset_index()
                    cat_det["Total"] = cat_det["Total"].map(brl)
                    cat_det["Média"] = cat_det["Média"].map(brl)
                    df_show = dedupe_columns(cat_det.rename(columns={"categoria":"Categoria"}).sort_values("Qtd", ascending=False))
                    st.markdown("#### 📋 Detalhes por Categoria")
                    st.dataframe(df_show, use_container_width=True, hide_index=True)

            with tab5:
                if qtd_shows > 0:
                    col_s1, col_s2 = st.columns(2)
                    col_s1.metric("Total de Shows", int(qtd_shows))
                    col_s1.metric("Receita Total de Shows", brl(
                        dfp.loc[
                            (_only_shows_mask(dfp)) &
                            (
                                (dfp.get("tipo", "").astype(str).str.strip().str.casefold() == "entrada")
                                | (dfp["valor"] > 0)
                            ),
                            "valor"
                        ].sum()
                    ))
                    col_s1.metric("Ticket Médio por Show", brl(ticket_medio))

                    # Lista de eventos (apenas categoria Shows, receitas)
                    base_shows = dfp.loc[_only_shows_mask(dfp)].copy()
                    if "tipo" in base_shows.columns:
                        t = base_shows["tipo"].astype(str).str.strip().str.casefold()
                        base_receita = base_shows.loc[t.eq("entrada")].copy()
                        if base_receita.empty:
                            base_receita = base_shows.loc[base_shows["valor"] > 0].copy()
                    else:
                        base_receita = base_shows.loc[base_shows["valor"] > 0].copy()

                    if not base_receita.empty and "evento" in base_receita.columns:
                        eventos_agg = (
                            base_receita.loc[base_receita["evento"].astype(str).str.strip().ne("")]
                            .groupby("evento", as_index=False)
                            .agg(valor=("valor", "sum"), data=("data", "min"))
                        )
                        if not eventos_agg.empty:
                            eventos_agg["Data"] = pd.to_datetime(eventos_agg["data"]).dt.strftime("%d/%m/%Y")
                            eventos_agg["Receita"] = eventos_agg["valor"].map(brl)
                            df_show = eventos_agg.sort_values("data", ascending=False)[["evento", "Data", "Receita"]]
                            df_show = df_show.rename(columns={"evento": "Evento"})
                            st.markdown("#### 🎤 Lista de Shows/Eventos (apenas categoria 'Shows')")
                            st.dataframe(df_show, use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhum show registrado no período selecionado.")

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
        
        col3, col4 = st.columns(2)
        with col3:
            evento = st.text_input("🎤 Evento/Show", placeholder="Nome do evento/show...")
        with col4:
            responsavel = st.text_input("👤 Responsável", placeholder="Quem registrou...")
        
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
        st.markdown("### 🔍 Filtros")
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
            sem_data = sem_data[sem_data["categoria"]] == categoria_sel
        if busca_texto:
            sem_data = sem_data[sem_data["descricao"].str.contains(busca_texto, case=False, na=False)]

        if inclui_sem_data and not sem_data.empty:
            view = pd.concat([view, sem_data], axis=0, ignore_index=False)

        view = view.sort_values(["data"], ascending=False)

        st.markdown("---")
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        col_r1.metric("📊 Total de Registros", len(view))
        receitas_filtro = view.loc[view["valor"] > 0, "valor"].sum()
        despesas_filtro = -view.loc[view["valor"] < 0, "valor"].sum()
        col_r2.metric("💰 Receitas", brl(receitas_filtro))
        col_r3.metric("💸 Despesas", brl(despesas_filtro))
        col_r4.metric("📈 Resultado", brl(receitas_filtro - despesas_filtro))
        st.markdown("---")

        if not view.empty:
            view_disp = view.copy()
            view_disp["Data"] = view_disp["data"].pipe(lambda s: s.dt.strftime("%d/%m/%Y")).fillna("—")
            view_disp["Valor"] = view_disp["valor"].map(brl)
            view_disp["Mov"] = view_disp["tipo"].map({"Entrada": "⬆️", "Saída": "⬇️"})

            cols_show = ["Data","Mov","tipo","categoria","descricao","conta","Valor","quem","evento"]
            cols_show = [c for c in cols_show if c in view_disp.columns]
            df_show = dedupe_columns(
                view_disp[cols_show].rename(columns={
                    "tipo":"Tipo","categoria":"Categoria","descricao":"Descrição",
                    "conta":"Pagamento","quem":"Responsável","evento":"Evento"
                })
            )
            st.markdown("### 📋 Lançamentos")
            st.dataframe(df_show, use_container_width=True, hide_index=True)

            # ---- Edição simplificada (com _row)
            st.markdown("---")
            st.markdown("### ✏️ Editar Lançamentos")

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
                        nova_linha = [
                            pd.to_datetime(nova_data).strftime("%Y-%m-%d"),
                            novoTipo, nova_categoria, nova_descricao, nova_conta,
                            novo_valor_com_sinal, novo_quem, novo_evento, novas_tags
                        ]
                        update_row("lancamentos", linha_sheets, nova_linha)
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

        st.markdown(f"### 📊 Resumo: {periodo_titulo}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 Receitas", brl(receitas))
        c2.metric("💸 Despesas", brl(despesas))
        c3.metric("📈 Resultado", brl(resultado))
        c4.metric("🎤 Shows", int(qtd_shows))
        st.markdown("---")

        # Remover a tab de Centro de Custo e manter apenas Rateio Fixo
        tab1, tab2 = st.tabs(["⚙️ Config. Rateio Fixo", "💰 Resultado Final"])

        with tab1:
            st.markdown("### ⚙️ Configuração de Rateio Fixo")
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
            st.markdown("### 💰 Cálculo do Rateio")
            
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
                
                st.markdown("#### 📊 Distribuição do Resultado")
                
                # Gráfico de pizza
                fig = px.pie(
                    ativo, 
                    values="valor", 
                    names="membro", 
                    hole=0.4,
                    title=f"Distribuição do Resultado entre Membros - {periodo_titulo}",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("#### 💵 Valores por Membro")
                
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
                
                # Resumo financeiro adicional
                st.markdown("#### 📋 Resumo Financeiro")
                col_res1, col_res2, col_res3 = st.columns(3)
                with col_res1:
                    st.metric("💵 Resultado Total", brl(resultado))
                with col_res2:
                    st.metric("👥 Membros Ativos", len(ativo))
                with col_res3:
                    st.metric("📊 Média por Membro", brl(resultado / len(ativo) if len(ativo) > 0 else 0))

# =============================================================================
# IMPORTAR EXCEL
# =============================================================================
elif page == "⬆️ Importar Excel":
    st.markdown('<p class="main-header">⬆️ Importar Planilha Excel</p>', unsafe_allow_html=True)
    st.markdown("""
    ### 📋 Instruções
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
    st.caption("Versão 2.2.0")
    st.caption("© 2025 - Todos os direitos reservados")