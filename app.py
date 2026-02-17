"""
Rockbuzz Finance - Dashboard Financeiro para Bandas
Arquivo principal da aplicação Streamlit (Página Home)
"""

import streamlit as st

from core.auth import check_password, init_session_state
from core.ui_components import setup_page_config, render_sidebar, render_footer
from core.data_loader import data_loader
from core.metrics import FinancialMetrics

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

def show_home_page():
    """Exibe a página inicial com KPIs principais"""
    try:
        # Importar a página Home
        from pages.home import main as home_main # Supondo que a lógica da home está em pages/home.py
        home_main()
    except ImportError as e:
        st.warning(f"Módulo da página Home não encontrado, usando dashboard básico. Detalhes: {e}")
        show_basic_dashboard()
    except Exception as e:
        st.error(f"Erro ao carregar página Home: {str(e)}")
        show_basic_dashboard()

def show_basic_dashboard():
    """Dashboard básico como fallback"""
    st.title("Rockbuzz Finance - Dashboard")
    
    # Carregar dados
    data = {}
    try:
        with st.spinner("Carregando dados..."):
            data = data_loader.load_all_data()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        if "Credenciais não configuradas" in str(e):
            st.info("💡 Configure as credenciais no menu lateral para conectar ao Google Sheets.")
        return
    
    if not data or 'transactions' not in data:
        st.error("Nao foi possivel carregar os dados financeiros.")
        return
    
    # KPIs básicos
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_entradas = data['transactions'][
            (data['transactions']['tipo'] == 'ENTRADA') & 
            (data['transactions']['payment_status'] == 'PAGO')
        ]['valor'].sum()
        st.metric("Total Receitas", f"R$ {total_entradas:,.2f}")
    
    with col2:
        total_despesas = data['transactions'][
            (data['transactions']['tipo'] == 'SAIDA') & 
            (data['transactions']['payment_status'] == 'PAGO')
        ]['valor'].sum()
        st.metric("Total Despesas", f"R$ {total_despesas:,.2f}")
    
    with col3:
        saldo = total_entradas - total_despesas
        st.metric("Saldo", f"R$ {saldo:,.2f}")

if __name__ == "__main__":
    main()
