from __future__ import annotations

# Band Finanças – Streamlit – App compartilhado
# Rodar:
#   pip install streamlit pandas numpy plotly gspread oauth2client openpyxl python-dateutil
#   streamlit run financas_rockbuzz.py
#   streamlit run "C:\Users\muril\OneDrive\01 - Projetos\07 - Streamlit\Finanças Rockbuzz\financas_rockbuzz.py"

import io
from datetime import datetime
from typing import List

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Google Sheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -----------------------------
# CONFIG GERAL
# -----------------------------
st.set_page_config(
    page_title="Band Finanças | Painel",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# HELPERS
# -----------------------------
def brl(x: float | int | str) -> str:
    """Formata em BRL sem depender de locale do SO."""
    try:
        if isinstance(x, str):
            x = float(x.replace(".", "").replace(",", "."))
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return f"R$ {x}"

def normalize_valor_series(col: pd.Series) -> pd.Series:
    """
    Converte strings no formato BR para float, de forma determinística (sem dividir por 100):
    - remove símbolos e espaços especiais
    - remove pontos de milhar
    - troca vírgula decimal por ponto
    - mantém negativos
    """
    s = (
        col.astype(str)
          .str.replace("\u00A0", "", regex=False)      # NBSP
          .str.replace(r"[^\d,\-\.]", "", regex=True)  # dígitos, vírgula, ponto, sinal
          .str.strip()
    )
    # Se tiver vírgula, tratamos como BR: remove '.' (milhar) e troca ',' por '.'
    tem_virg = s.str.contains(",", na=False)
    s_br = (
        s.str.replace(".", "", regex=False)
         .str.replace(",", ".", regex=False)
    )
    s = s.where(~tem_virg, s_br)

    # Agora converte
    f = pd.to_numeric(s, errors="coerce")
    return f

def count_shows(df: pd.DataFrame) -> int:
    """
    Conta shows do período. Regra:
      1) Se houver 'evento' preenchido, conta eventos únicos (não vazios).
      2) Senão, conta linhas cuja categoria OU descrição contenham 'show'.
    """
    evento = df.get("evento")
    if evento is not None:
        ev = evento.astype(str).str.strip()
        ev = ev[ev.ne("") & ev.ne("nan")]
        if not ev.empty:
            return int(ev.nunique())

    # fallback por categoria/descrição
    cat = df.get("categoria", pd.Series([""] * len(df))).astype(str)
    desc = df.get("descricao", pd.Series([""] * len(df))).astype(str)
    mask = cat.str.contains("show", case=False, na=False) | desc.str.contains("show", case=False, na=False)
    return int(mask.sum())

# -----------------------------
# CONEXÃO GOOGLE SHEETS
# -----------------------------
@st.cache_resource(show_spinner=False)
def get_sheet_client():
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
        return gc, cfg["sheet_id"]
    except Exception:
        return None, None

# -----------------------------
# LEITURA / ESCRITA DE DADOS
# -----------------------------
def ensure_ws_with_header(sh, title="lancamentos"):
    try:
        ws = sh.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=1000, cols=12)
        ws.append_row(["data","tipo","categoria","descricao","conta","valor","quem","evento","tags"])
    return ws

@st.cache_data(show_spinner=False, ttl=60)  # atualiza sozinho a cada 60s

def read_sheet(sheet_name: str = "lancamentos") -> pd.DataFrame:
    gc, sheet_id = get_sheet_client()
    if gc is None or not sheet_id:
        return pd.DataFrame(columns=["data","tipo","categoria","descricao","conta","valor","quem","evento","tags"])

    sh = gc.open_by_key(sheet_id)
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=12)
        ws.append_row(["data","tipo","categoria","descricao","conta","valor","quem","evento","tags"])

    # >>> LÊ TEXTO CRU, SEM COERÇÃO DO GOOGLE <<<
    rows = ws.get_all_values()  # lista de listas (strings cruas)
    if not rows:
        return pd.DataFrame(columns=["data","tipo","categoria","descricao","conta","valor","quem","evento","tags"])

    header = [c.strip() for c in rows[0]]
    data_rows = rows[1:]
    df = pd.DataFrame(data_rows, columns=header)

    # Normalizações básicas
    # Garante colunas padrão mesmo que não existam no Sheets
    for c in ["data","tipo","categoria","descricao","conta","valor","quem","evento","tags"]:
        if c not in df.columns:
            df[c] = ""

    # Datas
    df["data"] = pd.to_datetime(df["data"], errors="coerce")

    # Strings
    for c in ["tipo","categoria","descricao","conta","quem","evento","tags"]:
        df[c] = df[c].astype(str).str.strip()

    # Valor: usa parser determinístico BR
    df["valor_raw"] = df["valor"]  # mantém o texto original p/ debug
    df["valor"] = normalize_valor_series(df["valor"]).fillna(0.0)

    return df

def append_rows(sheet_name: str, rows: List[List]):
    gc, sheet_id = get_sheet_client()
    if gc is None or not sheet_id:
        raise RuntimeError("Google Sheets não configurado (secrets).")
    sh = gc.open_by_key(sheet_id)
    ws = ensure_ws_with_header(sh, sheet_name)
    ws.append_rows(rows, value_input_option="USER_ENTERED")

# -----------------------------
# IMPORTADOR (PLANILHA LEGADA)
# -----------------------------
@st.cache_data(show_spinner=False)
def parse_legacy_excel(file: bytes) -> pd.DataFrame:
    """Detecta cabeçalho e normaliza colunas da planilha antiga."""
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
                s = s.strip().lower()
                s = s.replace("descrição","descricao").replace("saída","saida")
                return s

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
                # Saída negativa, Entrada positiva
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

# -----------------------------
# RATEIO – helpers (config no Sheets)
# -----------------------------
@st.cache_data(show_spinner=False)
def read_rateio_config():
    gc, sheet_id = get_sheet_client()
    if not gc:
        return pd.DataFrame(columns=["membro","percentual","ativo","metodo"])
    sh = gc.open_by_key(sheet_id)
    try:
        ws = sh.worksheet("rateio_config")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="rateio_config", rows=100, cols=10)
        ws.append_row(["membro","percentual","ativo","metodo"])
        # valores padrão (16% cada)
        for r in [
            ["Murillo",16,True,"fixo"],["Helio",16,True,"fixo"],["Tay",16,True,"fixo"],
            ["Everton",16,True,"fixo"],["Kiko",16,True,"fixo"],["Naldo",16,True,"fixo"]
        ]:
            ws.append_row(r)
    df = pd.DataFrame(ws.get_all_records())
    if not {"membro","percentual","ativo","metodo"}.issubset(df.columns):
        df = pd.DataFrame(columns=["membro","percentual","ativo","metodo"])
    return df

def save_rateio_config(df: pd.DataFrame):
    gc, sheet_id = get_sheet_client()
    sh = gc.open_by_key(sheet_id)
    try:
        ws = sh.worksheet("rateio_config")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="rateio_config", rows=100, cols=10)
    ws.clear()
    ws.append_row(["membro","percentual","ativo","metodo"])
    for _, r in df.iterrows():
        ws.append_row([
            r.get("membro",""),
            float(pd.to_numeric(r.get("percentual"), errors="coerce") or 0),
            bool(r.get("ativo", True)),
            r.get("metodo","fixo")
        ])
    st.cache_data.clear()

@st.cache_data(show_spinner=False)
def read_centros_config():
    gc, sheet_id = get_sheet_client()
    if not gc:
        return pd.DataFrame(columns=["categoria","membro","percentual"])
    sh = gc.open_by_key(sheet_id)
    try:
        ws = sh.worksheet("rateio_centros")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="rateio_centros", rows=200, cols=10)
        ws.append_row(["categoria","membro","percentual"])
        for r in [
            ["Shows","Murillo",16],["Shows","Helio",16],["Shows","Tay",16],
            ["Shows","Everton",16],["Shows","Kiko",16],["Shows","Naldo",16]
        ]:
            ws.append_row(r)
    df = pd.DataFrame(ws.get_all_records())
    if not {"categoria","membro","percentual"}.issubset(df.columns):
        df = pd.DataFrame(columns=["categoria","membro","percentual"])
    return df

def save_centros_config(df: pd.DataFrame):
    gc, sheet_id = get_sheet_client()
    sh = gc.open_by_key(sheet_id)
    try:
        ws = sh.worksheet("rateio_centros")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="rateio_centros", rows=200, cols=10)
    ws.clear()
    ws.append_row(["categoria","membro","percentual"])
    for _, r in df.iterrows():
        ws.append_row([
            r.get("categoria",""),
            r.get("membro",""),
            float(pd.to_numeric(r.get("percentual"), errors="coerce") or 0)
        ])
    st.cache_data.clear()

# -----------------------------
# SIDEBAR – NAV + CONTROLES
# -----------------------------
with st.sidebar:
    st.markdown("## ⚙️ Navegação")
    page = st.radio("Ir para:", ["Registrar", "Lançamentos", "Dashboard", "Fechamento", "Importar (Excel)"])
    st.markdown("---")
    if st.button("🔄 Atualizar dados"):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.markdown("#### Segurança simples")
    edit_pin = st.text_input("PIN para editar (opcional)", type="password")
    st.caption("Dica: defina um PIN e compartilhe só com quem pode registrar.")

# -----------------------------
# PÁGINAS
# -----------------------------
if page == "Registrar":
    st.markdown("# 📝 Registrar lançamento")
    with st.form("form_registro", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            data = st.date_input("Data", value=datetime.today())
            tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
            valor = st.number_input("Valor (R$)", step=10.0, min_value=0.0)
        with col2:
            categoria = st.text_input("Categoria", value="Outros")
            conta = st.text_input("Conta/Pagamento", value="")
            evento = st.text_input("Evento/Show", value="")
        with col3:
            descricao = st.text_area("Descrição", height=100)
            quem = st.text_input("Quem lançou?", value="")
            tags = st.text_input("Tags (opcional)", value="")

        submitted = st.form_submit_button("✅ Salvar")

        if submitted:
            if edit_pin and edit_pin != st.secrets.get("pin", ""):
                st.error("PIN incorreto.")
            else:
                try:
                    gc, sheet_id = get_sheet_client()
                    if gc is None or not sheet_id:
                        st.error("Google Sheets não configurado. Confira o secrets.toml.")
                    else:
                        sh = gc.open_by_key(sheet_id)
                        ws = ensure_ws_with_header(sh, "lancamentos")
                        sign = 1 if tipo == "Entrada" else -1
                        row = [
                            data.strftime("%Y-%m-%d"), tipo, categoria, descricao, conta,
                            sign * float(valor or 0),
                            quem, evento, tags
                        ]
                        ws.append_row(row, value_input_option="USER_ENTERED")
                        st.cache_data.clear()
                        st.success("Lançamento salvo no Google Sheets!")
                except Exception as e:
                    import traceback
                    st.error(f"Falha ao salvar: {e}")
                    st.code(traceback.format_exc())

elif page == "Lançamentos":
    st.markdown("# 📒 Lançamentos")
    df = read_sheet("lancamentos")
    if df.empty:
        st.info("Sem registros ainda. Use a aba **Registrar** para adicionar os primeiros.")
    else:
        colf1, colf2, colf3, colf4 = st.columns(4)
        with colf1:
            dt_min = st.date_input("De", value=df["data"].min().date() if not df["data"].isna().all() else datetime.today().date())
        with colf2:
            dt_max = st.date_input("Até", value=df["data"].max().date() if not df["data"].isna().all() else datetime.today().date())
        with colf3:
            tipo_sel = st.multiselect("Tipo", options=sorted(df["tipo"].dropna().unique().tolist()))
        with colf4:
            categoria_sel = st.multiselect("Categoria", options=sorted(df["categoria"].dropna().unique().tolist()))

        m = (df["data"].dt.date >= dt_min) & (df["data"].dt.date <= dt_max)
        if tipo_sel: m &= df["tipo"].isin(tipo_sel)
        if categoria_sel: m &= df["categoria"].isin(categoria_sel)

        view = df.loc[m].copy().sort_values("data")
        view["valor_fmt"] = view["valor"].map(brl)
        cols = ["data","tipo","categoria","descricao","conta","valor_fmt","quem","evento","tags"]
        cols = [c for c in cols if c in view.columns]
        st.dataframe(view[cols], use_container_width=True)

        st.download_button(
            "Baixar filtrado (CSV)",
            data=view.to_csv(index=False).encode("utf-8"),
            file_name=f"lancamentos_filtrado_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )

elif page == "Dashboard":
    st.markdown("# 📊 Dashboard")
    df = read_sheet("lancamentos")
    if df.empty:
        st.info("Sem registros ainda.")
    else:
        df = df.dropna(subset=["data"]).copy()
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        df = df.dropna(subset=["data"])
        df["ano_mes"] = df["data"].dt.to_period("M").astype(str)

        meses = sorted(df["ano_mes"].unique().tolist())
        colf1, colf2 = st.columns([2,1])
        with colf1:
            mes_sel = st.selectbox("Mês (YYYY-MM)", options=["Todos"] + meses, index=0)
        if mes_sel != "Todos":
            df = df.loc[df["ano_mes"] == mes_sel].copy()

        # KPIs
        receitas = df.loc[df["valor"] > 0, "valor"].sum()
        despesas = -df.loc[df["valor"] < 0, "valor"].sum()
        resultado = receitas - despesas
        qtd_shows = count_shows(df)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Receitas", brl(receitas))
        c2.metric("Despesas", brl(despesas))
        c3.metric("Resultado", brl(resultado))
        c4.metric("Qtde de Shows", int(qtd_shows))

        tab1, tab2, tab3 = st.tabs(["Receitas x Despesas (mês)", "Saldo acumulado", "Por categoria"])
        with tab1:
            monthly = df.groupby(["ano_mes", "tipo"], dropna=False)["valor"].sum().reset_index()
            if monthly.empty:
                st.info("Sem dados no período.")
            else:
                fig = px.bar(monthly, x="ano_mes", y="valor", color="tipo", barmode="group", title="Receitas x Despesas por mês")
                st.plotly_chart(fig, use_container_width=True)

        with tab2:
            dd = df.groupby(df["data"].dt.date)["valor"].sum().reset_index(name="saldo_dia")
            dd = dd.sort_values("data")
            dd["saldo_acumulado"] = dd["saldo_dia"].cumsum()
            if dd.empty:
                st.info("Sem dados no período.")
            else:
                fig2 = px.line(dd, x="data", y="saldo_acumulado", markers=True, title="Saldo acumulado no período")
                st.plotly_chart(fig2, use_container_width=True)
                st.caption("Saldo diário (detalhe)")
                st.dataframe(dd.rename(columns={"data":"dia"}), use_container_width=True)

        with tab3:
            cat = df.copy()
            cat["categoria"] = cat["categoria"].astype(str).str.strip().replace({"": "Sem categoria"})
            cat_agg = cat.groupby("categoria", dropna=False)["valor"].sum().reset_index().sort_values("valor")
            if cat_agg.empty:
                st.info("Sem dados por categoria.")
            else:
                fig3 = px.bar(cat_agg, x="valor", y="categoria", orientation="h", title="Saldo por categoria (período)")
                st.plotly_chart(fig3, use_container_width=True)

elif page == "Fechamento":
    st.markdown("# 🧾 Fechamento mensal & Rateio")

    df_all = read_sheet("lancamentos")
    if df_all.empty or df_all["data"].isna().all():
        st.info("Sem registros com data. Use a aba Registrar/Importar.")
    else:
        df = df_all.dropna(subset=["data"]).copy()
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        df = df.dropna(subset=["data"])
        df["ano_mes"] = df["data"].dt.to_period("M").astype(str)

        colf1, colf2 = st.columns([2,1])
        with colf1:
            meses = sorted(df["ano_mes"].unique().tolist())
            mes_sel = st.selectbox("Mês (YYYY-MM)", options=meses, index=len(meses)-1)
        with colf2:
            if st.button("🔄 Atualizar dados"):
                st.cache_data.clear(); st.rerun()

        dfm = df.loc[df["ano_mes"] == mes_sel].copy()
        dfm["valor"] = pd.to_numeric(dfm["valor"], errors="coerce").fillna(0)

        receitas = dfm.loc[dfm["valor"] > 0, "valor"].sum()
        despesas = -dfm.loc[dfm["valor"] < 0, "valor"].sum()
        resultado = receitas - despesas

        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas (mês)", brl(receitas))
        c2.metric("Despesas (mês)", brl(despesas))
        c3.metric("Resultado (mês)", brl(resultado))

        st.markdown("---")
        st.subheader("⚙️ Configuração do rateio")
        tabs = st.tabs(["Rateio fixo (%)", "Rateio por centro de custo"])

        # -------- Rateio fixo --------
        with tabs[0]:
            cfg = read_rateio_config().copy()
            if cfg.empty:
                cfg = pd.DataFrame([
                    {"membro":"Murillo","percentual":16,"ativo":True,"metodo":"fixo"},
                    {"membro":"Helio","percentual":16,"ativo":True,"metodo":"fixo"},
                    {"membro":"Tay","percentual":16,"ativo":True,"metodo":"fixo"},
                    {"membro":"Everton","percentual":16,"ativo":True,"metodo":"fixo"},
                    {"membro":"Kiko","percentual":16,"ativo":True,"metodo":"fixo"},
                    {"membro":"Naldo","percentual":16,"ativo":True,"metodo":"fixo"}
                ])
            cfg["metodo"] = "fixo"
            edit_cfg = st.data_editor(
                cfg[["membro","percentual","ativo","metodo"]],
                num_rows="dynamic",
                use_container_width=True,
                key="rateio_fixo_editor",
            )
            total_pct = float(pd.to_numeric(edit_cfg["percentual"], errors="coerce").fillna(0).sum())
            st.write(f"**Soma dos percentuais:** {total_pct:.2f}%")
            if st.button("💾 Salvar rateio fixo"):
                if abs(total_pct - 100) <= 0.01:
                    save_rateio_config(edit_cfg)
                    st.success("Configuração de rateio fixo salva!")
                else:
                    st.error("Não foi salvo: ajuste os percentuais para totalizar 100%.")

            ativo = edit_cfg.loc[edit_cfg["ativo"] == True].copy()
            ativo["percentual"] = pd.to_numeric(ativo["percentual"], errors="coerce").fillna(0) / 100.0
            ativo["valor"] = ativo["percentual"] * resultado
            if not ativo.empty:
                ativo["valor_fmt"] = ativo["valor"].map(brl)
                st.markdown("#### 💰 Rateio (fixo) do resultado do mês")
                st.dataframe(ativo[["membro","percentual","valor_fmt"]], use_container_width=True)
                st.download_button(
                    "Baixar rateio fixo (CSV)",
                    data=ativo[["membro","percentual","valor"]].to_csv(index=False).encode("utf-8"),
                    file_name=f"rateio_fixo_{mes_sel}.csv",
                    mime="text/csv",
                )

        # -------- Rateio por centro de custo --------
        with tabs[1]:
            centros_cfg = read_centros_config().copy()
            if centros_cfg.empty:
                centros_cfg = pd.DataFrame([
                    {"categoria":"Shows","membro":"Murillo","percentual":16},
                    {"categoria":"Shows","membro":"Helio","percentual":16},
                    {"categoria":"Shows","membro":"Tay","percentual":16},
                    {"categoria":"Shows","membro":"Everton","percentual":16},
                    {"categoria":"Shows","membro":"Kiko","percentual":16},
                    {"categoria":"Shows","membro":"Naldo","percentual":16},
                ])
            st.write("**Mapa de rateio por categoria**")
            edit_centros = st.data_editor(
                centros_cfg[["categoria","membro","percentual"]],
                num_rows="dynamic",
                use_container_width=True,
                key="rateio_centro_editor",
            )
            if st.button("💾 Salvar mapa de centros"):
                ok = True
                for cat, grp in edit_centros.groupby("categoria"):
                    s = pd.to_numeric(grp["percentual"], errors="coerce").fillna(0).sum()
                    if abs(s - 100) > 0.01:
                        st.error(f"Categoria '{cat}': soma = {s:.2f}%. Ajuste para 100%.")
                        ok = False
                if ok:
                    save_centros_config(edit_centros)
                    st.success("Mapa de centros salvo!")

            dfm["categoria"] = dfm["categoria"].astype(str).str.strip()
            por_cat = dfm.groupby("categoria", dropna=False)["valor"].sum().reset_index()
            st.markdown("#### Totais por categoria (mês)")
            st.dataframe(por_cat, use_container_width=True)

            if not por_cat.empty and not edit_centros.empty:
                edit_centros["percentual"] = pd.to_numeric(edit_centros["percentual"], errors="coerce").fillna(0) / 100.0
                aloc = por_cat.merge(edit_centros, on="categoria", how="left")
                aloc["valor_membro"] = aloc["valor"] * aloc["percentual"]
                by_member = aloc.groupby("membro", dropna=False)["valor_membro"].sum().reset_index()
                by_member["valor_fmt"] = by_member["valor_membro"].map(brl)
                st.markdown("#### 💰 Rateio (por centro de custo) do mês")
                st.dataframe(by_member[["membro","valor_fmt"]], use_container_width=True)
                st.download_button(
                    "Baixar rateio por centro (CSV)",
                    data=by_member.rename(columns={"valor_membro":"valor"}).to_csv(index=False).encode("utf-8"),
                    file_name=f"rateio_centros_{mes_sel}.csv",
                    mime="text/csv",
                )

elif page == "Importar (Excel)":
    st.markdown("# ⬆️ Importar planilha antiga (Excel)")
    st.write("Faça upload do .xlsx. O app detecta o cabeçalho e normaliza os campos.")

    upl = st.file_uploader("Carregar Excel", type=["xlsx", "xls"])
    if upl is not None:
        parsed = parse_legacy_excel(upl.read())
        if parsed.empty:
            st.error("Não consegui identificar as colunas. Procure 'Data', 'Entrada/Saída', 'Descrição', 'Valor', 'Categoria'.")
        else:
            st.success(f"Foram lidas {len(parsed)} linhas.")
            st.dataframe(parsed.head(20), use_container_width=True)
            if st.button("Enviar tudo para o Google Sheets"):
                try:
                    rows = []
                    for _, r in parsed.iterrows():
                        rows.append([
                            (pd.to_datetime(r.get("data")).strftime("%Y-%m-%d") if pd.notna(r.get("data")) else ""),
                            r.get("tipo", ""), r.get("categoria", "Outros"),
                            r.get("descricao", ""), r.get("conta", ""),
                            float(r.get("valor", 0) or 0), "import", "", "legacy"
                        ])
                    append_rows("lancamentos", rows)
                    st.cache_data.clear()
                    st.success("Importação concluída no Google Sheets!")
                except Exception as e:
                    import traceback
                    st.error(f"Falha na importação: {e}")
                    st.code(traceback.format_exc())

# -----------------------------
# STATUS DA CONEXÃO – SIDEBAR
# -----------------------------
with st.sidebar:
    st.markdown("### 🔌 Status da conexão")
    try:
        gc, sheet_id = get_sheet_client()
        if gc is None or not sheet_id:
            st.error("Google Sheets **NÃO** configurado (secrets ausente ou inválido).")
        else:
            st.success(f"Conectado ao Sheets ✅\nID: {sheet_id}")
            if st.button("🧪 Inserir linha de teste"):
                try:
                    from datetime import datetime as _dt
                    sh = gc.open_by_key(sheet_id)
                    ws = ensure_ws_with_header(sh, "lancamentos")
                    ws.append_row(
                        [_dt.now().strftime("%Y-%m-%d"), "Entrada", "Debug", "Teste botão", "Pix", 1, "Murillo", "Teste", "botao"],
                        value_input_option="USER_ENTERED",
                    )
                    st.cache_data.clear()
                    st.success("Linha de teste inserida! Confira no Google Sheets.")
                except Exception as e:
                    import traceback
                    st.error(f"Falha ao inserir linha de teste: {e}")
                    st.code(traceback.format_exc())
    except Exception as e:
        import traceback
        st.error(f"Falha ao conectar: {e}")
        st.code(traceback.format_exc())
