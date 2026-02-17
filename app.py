"""
Rockbuzz Finance - Dashboard Financeiro para Bandas
Arquivo principal da aplicação Streamlit (Página Home)
"""

import streamlit as st

from core.auth import check_password, init_session_state
from core.ui_components import setup_page_config, render_sidebar, render_footer
from core.data_loader import data_loader
from core.metrics import FinancialMetrics
from core.navigation import show_home_page

def main():
    """
    Função principal que inicializa a aplicação Streamlit.
    Gerencia autenticação, sessão e renderiza a página Home.
    """
    
    # Configuração inicial da página
    setup_page_config()
    
    # Inicializar estado da sessão
    init_session_state()
    
    # Verificar autenticação
    if not st.session_state.get("authenticated", False):
        if check_password():
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.stop()
    
    # Renderizar sidebar com logo e navegação
    render_sidebar()
    
    # Container principal
    main_container = st.container()
    
    with main_container:
        try:
            # O conteúdo da página Home é renderizado aqui
            show_home_page()
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado na página Home: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.warning("Tente recarregar a página. Se o erro persistir, verifique os logs.")
    
    # Renderizar rodapé
    render_footer()

if __name__ == "__main__":
    main()
