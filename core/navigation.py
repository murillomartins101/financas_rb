"""
Navigation module for multi-page dashboard
Centralizes page rendering functions to avoid circular imports
"""

import streamlit as st
from typing import Callable, Dict
import sys
import os
import importlib.util

# Constants for module paths
ANALISES_MODULE_NAME = '05_📈_Análises'


def _load_analises_module():
    """
    Helper function to dynamically load the analysis module.
    Handles the special file name with emoji characters.
    
    Returns:
        The loaded module or None if loading fails
    """
    try:
        pages_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pages')
        
        # Check if module is already loaded
        if ANALISES_MODULE_NAME in sys.modules:
            return sys.modules[ANALISES_MODULE_NAME]
        
        # Load the module dynamically
        module_path = os.path.join(pages_dir, f'{ANALISES_MODULE_NAME}.py')
        if not os.path.exists(module_path):
            st.error(f"Arquivo de análises não encontrado: {module_path}")
            return None
        
        spec = importlib.util.spec_from_file_location(ANALISES_MODULE_NAME, module_path)
        if spec is None or spec.loader is None:
            st.error("Não foi possível carregar o módulo de análises")
            return None
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[ANALISES_MODULE_NAME] = module
        spec.loader.exec_module(module)
        
        return module
    except Exception as e:
        st.error(f"Erro ao carregar módulo de análises: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None


def show_home_page():
    """Exibe a página inicial com KPIs principais"""
    try:
        # Import the page module
        from pages.home import main as home_main
        home_main()
    except ImportError as e:
        st.warning(f"Módulo da página Home não encontrado, usando dashboard básico. Detalhes: {e}")
        _show_basic_dashboard()
    except Exception as e:
        st.error(f"Erro ao carregar página Home: {str(e)}")
        _show_basic_dashboard()


def show_shows_page():
    """Exibe a página de Shows"""
    try:
        from pages.shows import main as shows_main
        shows_main()
    except Exception as e:
        st.error(f"Erro ao carregar página de Shows: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def show_transacoes_page():
    """Exibe a página de Transações"""
    try:
        from pages.transacoes import main as transacoes_main
        transacoes_main()
    except Exception as e:
        st.error(f"Erro ao carregar página de Transações: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def show_relatorios_page():
    """Exibe a página de Relatórios e Projeções"""
    try:
        from pages.relatorios import main as relatorios_main
        relatorios_main()
    except Exception as e:
        st.error(f"Erro ao carregar página de Relatórios: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def show_cadastros_page():
    """Exibe a página de Cadastros (CRUD)"""
    try:
        from pages.cadastros import main as cadastros_main
        cadastros_main()
    except Exception as e:
        st.error(f"Erro ao carregar página de Cadastros: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def show_receitas_vs_despesas(data=None):
    """Exibe análise comparativa: Receitas vs. Despesas"""
    try:
        from core.data_loader import data_loader
        # Se data não foi fornecido, carrega
        if data is None:
            with st.spinner("Carregando dados..."):
                data = data_loader.load_all_data()
        
        # Load the analysis module and call the function
        analises_module = _load_analises_module()
        if analises_module and hasattr(analises_module, 'show_receitas_vs_despesas'):
            analises_module.show_receitas_vs_despesas(data)
        else:
            st.error("Função show_receitas_vs_despesas não encontrada no módulo de análises")
    except Exception as e:
        st.error(f"Erro ao carregar análise: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def show_despesas_detalhadas(data=None):
    """Exibe análise detalhada de despesas"""
    try:
        from core.data_loader import data_loader
        if data is None:
            with st.spinner("Carregando dados..."):
                data = data_loader.load_all_data()
        
        # Load the analysis module and call the function
        analises_module = _load_analises_module()
        if analises_module and hasattr(analises_module, 'show_despesas_detalhadas'):
            analises_module.show_despesas_detalhadas(data)
        else:
            st.error("Função show_despesas_detalhadas não encontrada no módulo de análises")
    except Exception as e:
        st.error(f"Erro ao carregar análise de Despesas: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def show_receitas_detalhadas(data=None):
    """Exibe análise detalhada de receitas"""
    try:
        from core.data_loader import data_loader
        if data is None:
            with st.spinner("Carregando dados..."):
                data = data_loader.load_all_data()
        
        # Load the analysis module and call the function
        analises_module = _load_analises_module()
        if analises_module and hasattr(analises_module, 'show_receitas_detalhadas'):
            analises_module.show_receitas_detalhadas(data)
        else:
            st.error("Função show_receitas_detalhadas não encontrada no módulo de análises")
    except Exception as e:
        st.error(f"Erro ao carregar análise de Receitas: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def _show_basic_dashboard():
    """Dashboard básico como fallback"""
    from core.data_loader import data_loader
    from core.metrics import FinancialMetrics
    
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
        st.error("Não foi possível carregar os dados financeiros.")
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


# Dictionary mapping page names to their render functions
PAGE_FUNCTIONS: Dict[str, Callable] = {
    "Home": show_home_page,
    "Shows": show_shows_page,
    "Transacoes": show_transacoes_page,
    "Relatorios": show_relatorios_page,
    "Cadastros": show_cadastros_page,
    "ReceitasDespesas": show_receitas_vs_despesas,
    "Despesas": show_despesas_detalhadas,
    "Receitas": show_receitas_detalhadas,
}


def render_page(page_name: str, **kwargs):
    """
    Renders a page by its name
    
    Args:
        page_name: Name of the page to render
        **kwargs: Additional arguments to pass to the page function
    """
    if page_name in PAGE_FUNCTIONS:
        try:
            PAGE_FUNCTIONS[page_name](**kwargs)
        except Exception as e:
            st.error(f"Erro ao renderizar página {page_name}: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.error(f"Página '{page_name}' não encontrada")
