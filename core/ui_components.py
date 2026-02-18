"""
Componentes de UI reutilizáveis
Sidebar com navegação + filtros globais + status conexão
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Tuple


def setup_page_config():
    st.set_page_config(
        page_title="Rockbuzz Finance",
        page_icon="RF",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com/seu-usuario/rockbuzz-finance",
            "Report a bug": "https://github.com/seu-usuario/rockbuzz-finance/issues",
            "About": "Dashboard Financeiro Profissional para Bandas",
        },
    )

    # CSS
    try:
        with open("assets/styles.css", "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception:
        pass


def get_period_dates(period_label: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    today = datetime.now()

    if period_label == "Mês atual":
        start_date = today.replace(day=1)
        end_date = today
    elif period_label == "Mês anterior":
        end_date = today.replace(day=1) - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif period_label == "Últimos 6 meses":
        start_date = today - timedelta(days=180)
        end_date = today
    elif period_label == "Ano atual":
        start_date = today.replace(month=1, day=1)
        end_date = today
    elif period_label == "Ano anterior":
        start_date = today.replace(year=today.year - 1, month=1, day=1)
        end_date = today.replace(year=today.year - 1, month=12, day=31)
    else:  # Todo período
        start_date = None
        end_date = None

    return start_date, end_date


def render_global_filters():
    st.subheader("Filtros de Período")

    options = ["Mês atual", "Mês anterior", "Últimos 6 meses", "Ano atual", "Ano anterior", "Todo período"]

    # mantém a seleção entre páginas
    current = st.session_state.get("filter_period", "Todo período")
    if current not in options:
        current = "Todo período"
    idx = options.index(current)

    selected = st.selectbox("Selecione o período", options, index=idx, key="global_period_filter")

    start_date, end_date = get_period_dates(selected)

    st.session_state.filter_period = selected
    st.session_state.filter_start_date = start_date
    st.session_state.filter_end_date = end_date

    if start_date and end_date:
        st.caption(f"Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
    else:
        st.caption("Período: Todo período")


def render_sidebar():
    from core.auth import logout
    from core.google_cloud import google_cloud_manager
    from core.data_loader import data_loader

    with st.sidebar:
        col1, col2 = st.columns([1, 3])
        with col1:
            try:
                st.image("assets/logo.png", width=48)
            except Exception:
                st.markdown("RF")
        with col2:
            st.markdown("### Rockbuzz Finance")

        st.divider()

        if st.session_state.get("authenticated", False):
            st.markdown(f"**{st.session_state.get('user_name', 'Usuário')}**")
            st.caption(f"_{st.session_state.get('user_role', 'membro')}_")
            if st.button("Sair", use_container_width=True):
                logout()

        st.divider()

        st.markdown("### Navegação")
        menu_pages = {
            "Home": "Home",
            "Shows": "Shows",
            "Relatórios & Projeções": "Relatorios",
            "Cadastro de Registros": "Cadastros",
            "Transações": "Transacoes",
        }

        current_page = st.session_state.get("current_page", "Home")
        for label, page in menu_pages.items():
            btn_type = "primary" if current_page == page else "secondary"
            if st.button(label, key=f"menu_{page}", use_container_width=True, type=btn_type):
                st.session_state.current_page = page
                st.rerun()

        st.divider()

        st.markdown("### Análises")
        quick = {
            "Receitas vs Despesas": "ReceitasDespesas",
            "Despesas Detalhadas": "Despesas",
            "Receitas Detalhadas": "Receitas",
        }
        for label, page in quick.items():
            if st.button(label, key=f"quick_{page}", use_container_width=True, type="secondary"):
                st.session_state.current_page = page
                st.rerun()

        st.divider()

        render_global_filters()

        st.divider()

        st.markdown("### Conexão")
        status = google_cloud_manager.get_connection_status()
        is_fallback = getattr(data_loader, "use_excel_fallback", False)
        data_source = st.session_state.get("data_source", "Desconhecido")

        if status.get("connected"):
            st.success(f"✅ Conectado | Fonte: {status.get('source','google')}")
            if status.get("spreadsheet_title"):
                st.caption(f"Planilha: {status.get('spreadsheet_title')}")
        elif is_fallback and "fallback" in str(data_source).lower():
            st.warning(f"⚠️ Fallback ativo | Fonte: {data_source}")
        else:
            st.error("❌ Desconectado")
            with st.expander("📋 Ver detalhes do erro"):
                st.write(status.get("error", "Erro desconhecido"))
                if status.get("suggestion"):
                    st.info(status.get("suggestion"))

        if st.button("🔄 Testar Conexão", use_container_width=True, type="secondary"):
            with st.spinner("Testando conexão..."):
                res = google_cloud_manager.test_connection_live()
                if res.get("success"):
                    st.success(res.get("message", "OK"))
                else:
                    st.error(res.get("message", "Falhou"))

        st.divider()

        if st.button("Atualizar Dados", use_container_width=True):
            data_loader.load_all_data(force_refresh=True)
            st.rerun()

        if st.session_state.get("last_cache_update"):
            last = st.session_state.last_cache_update
            if isinstance(last, str):
                last = datetime.fromisoformat(last)
            st.caption(f"Atualizado: {last.strftime('%H:%M')}")


def render_footer():
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("🎸 Rockbuzz Finance v1.0")
    with col2:
        st.caption("Dashboard Financeiro Profissional")
    with col3:
        st.caption(f"© {datetime.now().year} - Todos os direitos reservados")
