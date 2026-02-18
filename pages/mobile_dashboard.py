"""
Pagina mobile do dashboard com sidebar colapsavel
"""

import streamlit as st

from core.auth import check_password, init_session_state
from core.ui_components import setup_page_config, render_sidebar, render_footer
from core.navigation import (
    show_home_page,
    show_shows_page,
    show_transacoes_page,
    show_relatorios_page,
    show_cadastros_page,
    show_receitas_vs_despesas,
    show_despesas_detalhadas,
    show_receitas_detalhadas,
)

def apply_mobile_sidebar_fix():
    """Reabilita o header para exibir o controle do sidebar no mobile."""
    st.markdown(
        """
        <style>
        @media (max-width: 768px) {
          header[data-testid="stHeader"] {
            display: flex !important;
            visibility: visible !important;
          }

          [data-testid="collapsedControl"] {
            display: block !important;
            visibility: visible !important;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def render_current_page():
    """Renderiza a pagina selecionada na navegacao."""
    current_page = st.session_state.get("current_page", "Home")

    try:
        if current_page == "Home":
            show_home_page()
        elif current_page == "Shows":
            show_shows_page()
        elif current_page == "Transacoes":
            show_transacoes_page()
        elif current_page == "Relatorios":
            show_relatorios_page()
        elif current_page == "Cadastros":
            show_cadastros_page()
        elif current_page == "ReceitasDespesas":
            show_receitas_vs_despesas()
        elif current_page == "Despesas":
            show_despesas_detalhadas()
        elif current_page == "Receitas":
            show_receitas_detalhadas()
        else:
            st.session_state.current_page = "Home"
            st.rerun()
    except Exception as e:
        st.error(f"Erro ao carregar a pagina: {str(e)}")
        import traceback

        st.code(traceback.format_exc())
        st.info("Tente recarregar a pagina ou voltar para Home")
        if st.button("Voltar para Home"):
            st.session_state.current_page = "Home"
            st.rerun()

def main():
    """Inicializa a pagina mobile do dashboard."""
    setup_page_config()
    init_session_state()
    apply_mobile_sidebar_fix()

    if not st.session_state.get("authenticated", False):
        if check_password():
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.stop()

    render_sidebar()

    with st.container():
        render_current_page()

    render_footer()

if __name__ == "__main__":
    main()