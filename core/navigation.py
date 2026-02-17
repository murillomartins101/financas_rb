"""
Navigation module for multi-page dashboard
Centralizes page rendering functions to avoid circular imports
"""

import streamlit as st
from typing import Callable, Dict


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
        
        # Import the analysis function
        from pages import main as analises_main
        analises_main.show_receitas_vs_despesas(data)
    except ImportError:
        # Se a importação falhar, tenta importar diretamente da página
        try:
            import sys
            import os
            # Add pages directory to path if needed
            pages_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pages')
            if pages_dir not in sys.path:
                sys.path.insert(0, pages_dir)
            
            # Try importing from the specific analysis file
            from pages import show_receitas_vs_despesas as receitas_vs_despesas_func
            
            from core.data_loader import data_loader
            if data is None:
                with st.spinner("Carregando dados..."):
                    data = data_loader.load_all_data()
            
            receitas_vs_despesas_func(data)
        except Exception as e2:
            st.error(f"Erro ao carregar análise Receitas vs Despesas: {str(e2)}")
            import traceback
            st.code(traceback.format_exc())
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
        
        # Import from the analysis page
        import sys
        import os
        pages_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pages')
        if pages_dir not in sys.path:
            sys.path.insert(0, pages_dir)
        
        # Import the specific function from the analysis file
        module_name = '05_📈_Análises'
        if module_name in sys.modules:
            analises_module = sys.modules[module_name]
        else:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                module_name,
                os.path.join(pages_dir, '05_📈_Análises.py')
            )
            analises_module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = analises_module
            spec.loader.exec_module(analises_module)
        
        analises_module.show_despesas_detalhadas(data)
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
        
        # Import from the analysis page
        import sys
        import os
        pages_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pages')
        if pages_dir not in sys.path:
            sys.path.insert(0, pages_dir)
        
        # Import the specific function from the analysis file
        module_name = '05_📈_Análises'
        if module_name in sys.modules:
            analises_module = sys.modules[module_name]
        else:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                module_name,
                os.path.join(pages_dir, '05_📈_Análises.py')
            )
            analises_module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = analises_module
            spec.loader.exec_module(analises_module)
        
        analises_module.show_receitas_detalhadas(data)
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
