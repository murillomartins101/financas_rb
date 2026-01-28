from __future__ import annotations

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

# =========================
# CONFIG GERAL
# =========================
st.set_page_config(
    page_title="Band Finanças | Painel",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================
# HELPERS
# =========================
def brl(x: float | int | str) -> str:
    """Formata em BRL sem depender de locale do SO."""
    try:
        if isinstance(x, str):
            # Remove caracteres não numéricos exceto ponto, vírgula e sinal negativo
            x_clean = ''.join(c for c in x if c.isdigit() or c in ',.-')
            if ',' in x_clean and '.' in x_clean:
                # Se tem ambos, assume que vírgula é decimal e remove ponto (milhar)
                if x_clean.find(',') < x_clean.find('.'):
                    x_clean = x_clean.replace(',', '')
                else:
                    x_clean = x_clean.replace('.', '').replace(',', '.')
            elif ',' in x_clean:
                # Se só tem vírgula, substitui por ponto
                x_clean = x_clean.replace(',', '.')
            
            # Remove múltiplos pontos decimais
            parts = x_clean.split('.')
            if len(parts) > 2:
                x_clean = parts[0] + '.' + ''.join(parts[1:])
            
            x = float(x_clean)
        
        # Formatação final
        if x >= 0:
            return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            return f"-R$ {abs(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return f"R$ {x}"

def normalize_valor_series(col: pd.Series) -> pd.Series:
    """
    Converte strings no formato BR para float (determinístico, sem /100):
    - remove símbolos/espacos especiais
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
    
    # Processa cada valor individualmente
    def convert_value(val):
        if not val or val in ['', 'nan', 'None']:
            return np.nan
        
        # Remove espaços e caracteres especiais
        val = str(val).strip()
        
        # Verifica se é negativo
        is_negative = val.startswith('-')
        if is_negative:
            val = val[1:]
        
        # Processa formato brasileiro
        if ',' in val and '.' in val:
            # Se tem ambos, determina qual é o decimal
            if val.find(',') > val.find('.'):
                # Vírgula é decimal, ponto é milhar: 1.234,56
                val = val.replace('.', '').replace(',', '.')
            else:
                # Ponto é decimal, vírgula é milhar: 1,234.56
                val = val.replace(',', '')
        elif ',' in val:
            # Só tem vírgula - verifica se há 3 dígitos após vírgula (provavelmente milhar)
            parts = val.split(',')
            if len(parts) == 2 and len(parts[1]) == 3 and len(parts[0].replace('.', '')) > 0:
                # Provavelmente formato europeu: 1,234 -> 1.234
                val = val.replace(',', '.')
            else:
                # Formato brasileiro: 1234,56 -> 1234.56
                val = val.replace(',', '.')
        
        try:
            result = float(val)
            return -result if is_negative else result
        except (ValueError, TypeError):
            return np.nan
    
    return pd.Series([convert_value(x) for x in s])

def count_shows(df: pd.DataFrame) -> int:
    """
    Conta shows do período:
      1) Se houver 'evento' preenchido, conta eventos únicos (não vazios).
      2) Senão, conta linhas cuja categoria OU descrição contenham 'show'.
    """
    if df.empty:
        return 0
        
    evento = df.get("evento")
    if evento is not None:
        ev = evento.astype(str).str.strip()
        ev = ev[ev.ne("") & ~ev.isin(["nan", "None"])]
        if not ev.empty:
            return int(ev.nunique())
    
    cat = df.get("categoria", pd.Series([""] * len(df))).astype(str)
    desc = df.get("descricao", pd.Series([""] * len(df))).astype(str)
    mask = cat.str.contains("show", case=False, na=False) | desc.str.contains("show", case=False, na=False)
    return int(mask.sum())

# =========================
# CONEXÃO GOOGLE SHEETS
# =========================
@st.cache_resource(show_spinner=False)
def get_sheet_client():
    cfg = st.secrets.get("gcp", None)
    if cfg is None:
        st.warning("Configuração do Google Sheets não encontrada. Verifique o arquivo secrets.toml")
        return None, None
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(cfg, scope)
        gc = gspread.authorize(creds)
        return gc, cfg["sheet_id"]
    except Exception as e:
        st.error(f"Erro na autenticação do Google Sheets: {e}")
        return None, None

def ensure_ws_with_header(sh, title="lancamentos"):
    """Garante worksheet com cabeçalho padrão."""
    try:
        ws = sh.worksheet(title)
        # Verifica se tem cabeçalho básico
        header = ws.row_values(1)
        expected_cols = ["data", "tipo", "categoria", "descricao", "conta", "valor", "quem", "evento", "tags"]
        if not all(col in header for col in expected_cols):
            # Se não tem todas as colunas, adiciona as faltantes
            for col in expected_cols:
                if col not in header:
                    ws.update_cell(1, len(header) + 1, col)
                    header = ws.row_values(1)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=1000, cols=12)
        ws.append_row(["data","tipo","categoria","descricao","conta","valor","quem","evento","tags"])
    except Exception as e:
        st.error(f"Erro ao acessar worksheet: {e}")
        return None
    return ws

# =========================
# LEITURA / ESCRITA
# =========================
@st.cache_data(show_spinner=False, ttl=60)
def read_sheet(sheet_name: str = "lancamentos") -> pd.DataFrame:
    """Lê a planilha como TEXTO CRU (get_all_values) e aplica nosso parser."""
    gc, sheet_id = get_sheet_client()
    if gc is None or not sheet_id:
        return pd.DataFrame(columns=["data","tipo","categoria","descricao","conta","valor","quem","evento","tags"])

    try:
        sh = gc.open_by_key(sheet_id)
        ws = ensure_ws_with_header(sh, sheet_name)
        if ws is None:
            return pd.DataFrame(columns=["data","tipo","categoria","descricao","conta","valor","quem","evento","tags"])

        rows = ws.get_all_values()  # texto cru
        if not rows or len(rows) <= 1:
            return pd.DataFrame(columns=["data","tipo","categoria","descricao","conta","valor","quem","evento","tags"])

        header = [c.strip().lower() for c in rows[0]]
        data_rows = rows[1:]
        df = pd.DataFrame(data_rows, columns=header)

        # Garante colunas padrão
        expected_cols = ["data","tipo","categoria","descricao","conta","valor","quem","evento","tags"]
        for c in expected_cols:
            if c not in df.columns:
                df[c] = ""

        # Normalizações
        df["data"] = pd.to_datetime(df["data"], errors="coerce", dayfirst=True)
        for c in ["tipo","categoria","descricao","conta","quem","evento","tags"]:
            df[c] = df[c].astype(str).str.strip().replace({"nan": "", "None": ""})

        df["valor_raw"] = df["valor"]  # útil para debug
        df["valor"] = normalize_valor_series(df["valor"]).fillna(0.0)

        return df
        
    except Exception as e:
        st.error(f"Erro ao ler planilha: {e}")
        return pd.DataFrame(columns=["data","tipo","categoria","descricao","conta","valor","quem","evento","tags"])

def append_rows(sheet_name: str, rows: List[List]):
    gc, sheet_id = get_sheet_client()
    if gc is None or not sheet_id:
        raise RuntimeError("Google Sheets não configurado (secrets).")
    sh = gc.open_by_key(sheet_id)
    ws = ensure_ws_with_header(sh, sheet_name)
    
    # Formata os valores adequadamente
    formatted_rows = []
    for row in rows:
        formatted_row = []
        for cell in row:
            if isinstance(cell, float):
                # Para valores float, usa ponto como separador decimal
                formatted_row = f"{cell:.2f}"
            else:
                formatted_row.append(str(cell))
        formatted_rows.append(formatted_row)
    
    ws.append_rows(formatted_rows, value_input_option="USER_ENTERED")

@st.cache_data(show_spinner=False)
def parse_legacy_excel(file: bytes) -> pd.DataFrame:
    """Importador simples para planilha antiga (detecta cabeçalho e normaliza)."""
    try:
        raw = pd.read_excel(io.BytesIO(file), sheet_name=None, header=None)
        for _, df in raw.items():
            if df.empty:
                continue
                
            # Procura linha do cabeçalho
            mask = df.apply(lambda r: r.astype(str).str.contains("data", case=False, na=False)).any(axis=1)
            idx = np.where(mask)[0]
            if idx.size:
                hi = int(idx[0])
                header = df.iloc[hi].astype(str).tolist()
                body = df.iloc[hi+1:].copy()
                body.columns = [str(c).strip() for c in header]

                def norm(s: str) -> str:
                    s = s.strip().lower().replace("descrição","descricao").replace("saída","saida")
                    return s

                # Mapeamento de colunas
                col_mapping = {}
                for i, col in enumerate(body.columns):
                    col_norm = norm(col)
                    if "data" in col_norm:
                        col_mapping[col] = "data"
                    elif "tipo" in col_norm or "entrada" in col_norm or "saida" in col_norm:
                        col_mapping[col] = "tipo"
                    elif "categoria" in col_norm:
                        col_mapping[col] = "categoria"
                    elif "descricao" in col_norm:
                        col_mapping[col] = "descricao"
                    elif "conta" in col_norm:
                        col_mapping[col] = "conta"
                    elif "valor" in col_norm:
                        col_mapping[col] = "valor"

                # Renomeia colunas
                body = body.rename(columns=col_mapping)
                
                # Seleciona apenas colunas mapeadas
                keep = [c for c in ["data","tipo","categoria","descricao","conta","valor"] if c in body.columns]
                if not keep:
                    continue
                    
                out = body[keep].copy()

                # Processa dados
                if "data" in out.columns:
                    out["data"] = pd.to_datetime(out["data"], errors="coerce", dayfirst=True)
                if "valor" in out.columns:
                    out["valor"] = normalize_valor_series(out["valor"])

                if "tipo" in out.columns and "valor" in out.columns:
                    out["tipo"] = out["tipo"].astype(str).str.strip().str.title()
                    saida_mask = out["tipo"].str.contains("Sa[ií]d", case=False, regex=True, na=False)
                    entr_mask  = out["tipo"].str.contains("Entrad", case=False, regex=True, na=False)
                    out.loc[saida_mask, "valor"] = -out.loc[saida_mask, "valor"].abs()
                    out.loc[entr_mask,  "valor"] =  out.loc[entr_mask, "valor"].abs()

                # Preenche colunas faltantes
                if "conta" not in out.columns: 
                    out["conta"] = ""
                if "categoria" not in out.columns: 
                    out["categoria"] = "Outros"
                if "descricao" not in out.columns:
                    out["descricao"] = ""

                # Remove linhas completamente vazias
                out = out.dropna(how='all')
                # Remove linhas sem data ou valor
                out = out.dropna(subset=[c for c in ["data","valor"] if c in out.columns])
                
                if not out.empty:
                    return out

    except Exception as e:
        st.error(f"Erro ao processar Excel: {e}")

    return pd.DataFrame(columns=["data","tipo","categoria","descricao","conta","valor"])

# =========================
# UI: SIDEBAR
# =========================
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

# =========================
# PÁGINAS
# =========================
if page == "Registrar":
    st.markdown("# 📝 Registrar lançamento")
    with st.form("form_registro", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            data = st.date_input("Data", value=datetime.today())
            tipo = st.selectbox("Tipo", ["Entrada", "Saída"])
            valor = st.number_input("Valor (R$)", step=10.0, min_value=0.0, format="%.2f")
        with c2:
            categoria = st.text_input("Categoria", value="Outros")
            conta = st.text_input("Conta/Pagamento", value="")
            evento = st.text_input("Evento/Show", value="")
        with c3:
            descricao = st.text_area("Descrição", height=100)
            quem = st.text_input("Quem lançou?", value="")
            tags = st.text_input("Tags (opcional)", value="")

        submitted = st.form_submit_button("✅ Salvar")

        if submitted:
            if not descricao.strip():
                st.error("Descrição é obrigatória.")
            elif not categoria.strip():
                st.error("Categoria é obrigatória.")
            elif valor <= 0:
                st.error("Valor deve ser maior que zero.")
            else:
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
                                data.strftime("%Y-%m-%d"), 
                                tipo, 
                                categoria.strip(), 
                                descricao.strip(), 
                                conta.strip(),
                                sign * float(valor),
                                quem.strip(), 
                                evento.strip(), 
                                tags.strip()
                            ]
                            ws.append_row(row, value_input_option="USER_ENTERED")
                            st.cache_data.clear()
                            st.success("Lançamento salvo no Google Sheets!")
                    except Exception as e:
                        st.error(f"Falha ao salvar: {e}")

elif page == "Lançamentos":
    st.markdown("# 📒 Lançamentos")
    df = read_sheet("lancamentos")

    if df.empty or df["data"].isna().all():
        st.info("Sem registros ainda. Use a aba **Registrar** para adicionar os primeiros.")
    else:
        # garante tipo datetime e remove NaT antes de filtrar
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        df = df.dropna(subset=["data"])

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            dt_min = st.date_input(
                "De",
                value=df["data"].min().date() if not df["data"].isna().all() else datetime.today().date()
            )
        with c2:
            dt_max = st.date_input(
                "Até",
                value=df["data"].max().date() if not df["data"].isna().all() else datetime.today().date()
            )
        with c3:
            tipo_sel = st.multiselect("Tipo", options=sorted(df["tipo"].dropna().unique().tolist()))
        with c4:
            categoria_sel = st.multiselect("Categoria", options=sorted(df["categoria"].dropna().unique().tolist()))

        m = (df["data"].dt.date >= dt_min) & (df["data"].dt.date <= dt_max)
        if tipo_sel:
            m &= df["tipo"].isin(tipo_sel)
        if categoria_sel:
            m &= df["categoria"].isin(categoria_sel)

        # usa a versão parseada (numérica) e formata para exibição
        view = df.loc[m].copy().sort_values("data", ascending=False)
        view["valor_fmt"] = view["valor"].map(brl)

        # remove o texto cru vindo do Sheets (se existir)
        if "valor_raw" in view.columns:
            view = view.drop(columns=["valor_raw"], errors="ignore")

        # exibição
        display_cols = ["data", "tipo", "categoria", "descricao", "conta", "valor_fmt", "quem", "evento", "tags"]
        display_cols = [c for c in display_cols if c in view.columns]
        
        if view.empty:
            st.info("Nenhum lançamento encontrado com os filtros selecionados.")
        else:
            st.dataframe(
                view[display_cols], 
                use_container_width=True,
                column_config={
                    "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                    "valor_fmt": "Valor"
                }
            )

            # download (usa o valor numérico correto)
            csv_cols = ["data", "tipo", "categoria", "descricao", "conta", "valor", "quem", "evento", "tags"]
            csv_cols = [c for c in csv_cols if c in view.columns]
            csv_df = view[csv_cols].copy()
            if "data" in csv_df.columns:
                csv_df["data"] = pd.to_datetime(csv_df["data"], errors="coerce").dt.strftime("%Y-%m-%d")
            st.download_button(
                "Baixar filtrado (CSV)",
                data=csv_df.to_csv(index=False, sep=';').encode("utf-8-sig"),
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
        df["ano_mes"] = df["data"].dt.to_period("M").astype(str)

        meses = sorted(df["ano_mes"].unique().tolist())
        c1, c2 = st.columns([2,1])
        with c1:
            mes_sel = st.selectbox("Mês (YYYY-MM)", options=["Todos"] + meses, index=0)
        with c2:
            st.write("")  # Espaçamento
            
        if mes_sel != "Todos":
            df = df.loc[df["ano_mes"] == mes_sel].copy()

        receitas = df.loc[df["valor"] > 0, "valor"].sum()
        despesas = -df.loc[df["valor"] < 0, "valor"].sum()
        resultado = receitas - despesas
        qtd_shows = count_shows(df)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Receitas", brl(receitas))
        k2.metric("Despesas", brl(despesas))
        k3.metric("Resultado", brl(resultado), delta_color="inverse" if resultado < 0 else "normal")
        k4.metric("Qtde de Shows", int(qtd_shows))

        tab1, tab2, tab3 = st.tabs(["Receitas x Despesas (mês)", "Saldo acumulado", "Por categoria"])
        with tab1:
            monthly = df.groupby(["ano_mes", "tipo"], dropna=False)["valor"].sum().reset_index()
            if monthly.empty:
                st.info("Sem dados no período.")
            else:
                fig = px.bar(
                    monthly, 
                    x="ano_mes", 
                    y="valor", 
                    color="tipo", 
                    barmode="group", 
                    title="Receitas x Despesas por mês",
                    labels={"ano_mes": "Mês", "valor": "Valor (R$)", "tipo": "Tipo"}
                )
                st.plotly_chart(fig, use_container_width=True)

        with tab2:
            dd = df.groupby(df["data"].dt.date)["valor"].sum().reset_index(name="saldo_dia")
            dd = dd.sort_values("data")
            dd["saldo_acumulado"] = dd["saldo_dia"].cumsum()
            if dd.empty:
                st.info("Sem dados no período.")
            else:
                fig2 = px.line(
                    dd, 
                    x="data", 
                    y="saldo_acumulado", 
                    markers=True, 
                    title="Saldo acumulado no período",
                    labels={"data": "Data", "saldo_acumulado": "Saldo Acumulado (R$)"}
                )
                st.plotly_chart(fig2, use_container_width=True)
                st.caption("Saldo diário (detalhe)")
                st.dataframe(
                    dd.rename(columns={"data":"dia", "saldo_dia": "Saldo Dia", "saldo_acumulado": "Saldo Acumulado"}),
                    use_container_width=True
                )

        with tab3:
            cat = df.copy()
            cat["categoria"] = cat["categoria"].astype(str).str.strip().replace({"": "Sem categoria"})
            cat_agg = cat.groupby("categoria", dropna=False)["valor"].sum().reset_index().sort_values("valor", ascending=False)
            if cat_agg.empty:
                st.info("Sem dados por categoria.")
            else:
                fig3 = px.bar(
                    cat_agg.head(20),  # Limita a 20 categorias para melhor visualização
                    x="valor", 
                    y="categoria", 
                    orientation="h", 
                    title="Saldo por categoria (período - Top 20)",
                    labels={"valor": "Valor (R$)", "categoria": "Categoria"}
                )
                st.plotly_chart(fig3, use_container_width=True)

elif page == "Fechamento":
    st.markdown("# 🧾 Fechamento mensal & Rateio")
    df_all = read_sheet("lancamentos")
    if df_all.empty or df_all["data"].isna().all():
        st.info("Sem registros com data. Use a aba Registrar/Importar.")
    else:
        df = df_all.dropna(subset=["data"]).copy()
        df["ano_mes"] = df["data"].dt.to_period("M").astype(str)

        c1, c2 = st.columns([2,1])
        with c1:
            meses = sorted(df["ano_mes"].unique().tolist())
            mes_sel = st.selectbox("Mês (YYYY-MM)", options=meses, index=len(meses)-1 if meses else 0)
        with c2:
            if st.button("🔄 Atualizar dados"):
                st.cache_data.clear()
                st.rerun()

        dfm = df.loc[df["ano_mes"] == mes_sel].copy()
        dfm["valor"] = pd.to_numeric(dfm["valor"], errors="coerce").fillna(0)

        receitas = dfm.loc[dfm["valor"] > 0, "valor"].sum()
        despesas = -dfm.loc[dfm["valor"] < 0, "valor"].sum()
        resultado = receitas - despesas

        k1, k2, k3 = st.columns(3)
        k1.metric("Receitas (mês)", brl(receitas))
        k2.metric("Despesas (mês)", brl(despesas))
        k3.metric("Resultado (mês)", brl(resultado), delta_color="inverse" if resultado < 0 else "normal")

        st.markdown("---")
        st.subheader("📊 Detalhamento por categoria")
        
        # Totais por categoria
        dfm["categoria"] = dfm["categoria"].astype(str).str.strip().replace({"": "Sem categoria"})
        por_cat = dfm.groupby("categoria", dropna=False)["valor"].sum().reset_index()
        por_cat = por_cat.sort_values("valor", ascending=False)
        
        # Adiciona formatação para exibição
        por_cat_display = por_cat.copy()
        por_cat_display["valor_fmt"] = por_cat_display["valor"].map(brl)
        
        st.dataframe(
            por_cat_display[["categoria", "valor_fmt"]].rename(columns={"valor_fmt": "Valor"}),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.subheader("⚙️ Configuração do rateio")
        st.info("Para edição de configurações de rateio, utilize diretamente a planilha do Google Sheets (abas: rateio_config e rateio_centros).")

elif page == "Importar (Excel)":
    st.markdown("# ⬆️ Importar planilha antiga (Excel)")
    st.write("Faça upload do .xlsx. O app detecta o cabeçalho e normaliza os campos.")
    upl = st.file_uploader("Carregar Excel", type=["xlsx", "xls"])
    
    if upl is not None:
        with st.spinner("Processando arquivo..."):
            parsed = parse_legacy_excel(upl.read())
            
        if parsed.empty:
            st.error("Não consegui identificar as colunas. Procure por colunas como 'Data', 'Entrada/Saída', 'Descrição', 'Valor', 'Categoria'.")
        else:
            st.success(f"Foram lidas {len(parsed)} linhas válidas.")
            
            # Pré-visualização
            st.subheader("Pré-visualização (primeiras 20 linhas)")
            preview = parsed.head(20).copy()
            preview["valor_fmt"] = preview["valor"].map(brl)
            st.dataframe(preview, use_container_width=True)
            
            if st.button("📤 Enviar tudo para o Google Sheets", type="primary"):
                try:
                    rows = []
                    for _, r in parsed.iterrows():
                        row_data = [
                            r.get("data").strftime("%Y-%m-%d") if pd.notna(r.get("data")) else datetime.today().strftime("%Y-%m-%d"),
                            r.get("tipo", "Entrada"),
                            r.get("categoria", "Outros"),
                            r.get("descricao", ""),
                            r.get("conta", ""),
                            float(r.get("valor", 0) or 0),
                            "import",
                            "",
                            "legacy"
                        ]
                        rows.append(row_data)
                    
                    append_rows("lancamentos", rows)
                    st.cache_data.clear()
                    st.success(f"✅ Importação concluída! {len(rows)} lançamentos foram adicionados ao Google Sheets.")
                    
                except Exception as e:
                    st.error(f"Falha na importação: {e}")

# =========================
# STATUS DA CONEXÃO – SIDEBAR
# =========================
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔌 Status da conexão")
    try:
        gc, sheet_id = get_sheet_client()
        if gc is None or not sheet_id:
            st.error("Google Sheets **NÃO** configurado")
            st.info("Verifique o arquivo secrets.toml com as credenciais")
        else:
            st.success("Conectado ao Sheets ✅")
            st.caption(f"ID: {sheet_id[:8]}...")
            
            if st.button("🧪 Inserir linha de teste", use_container_width=True):
                try:
                    sh = gc.open_by_key(sheet_id)
                    ws = ensure_ws_with_header(sh, "lancamentos")
                    test_row = [
                        datetime.now().strftime("%Y-%m-%d"), 
                        "Entrada", 
                        "Debug", 
                        "Teste botão sidebar", 
                        "Pix", 
                        1200.50, 
                        "Sistema", 
                        "Teste", 
                        "botao"
                    ]
                    ws.append_row(test_row, value_input_option="USER_ENTERED")
                    st.cache_data.clear()
                    st.success("Linha de teste inserida!")
                except Exception as e:
                    st.error(f"Falha ao inserir teste: {e}")
                    
    except Exception as e:
        st.error(f"Falha na conexão: {e}")

# =========================
# RODAPÉ
# =========================
st.sidebar.markdown("---")
st.sidebar.markdown("**Band Finanças** v1.0")
st.sidebar.caption("Desenvolvido para RockBuzz")