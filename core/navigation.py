"""
Navigation module for multi-page dashboard
Centralizes page rendering functions to avoid circular imports

FIX:
- Loader de análises tenta vários nomes possíveis.
- Prioriza pages/analises.py (nome "normal" e estável).
- _call_page_main agora trata ImportError com mensagem mais clara.
"""

import streamlit as st
from typing import Callable, Dict, Optional
import sys
import os
import importlib.util

# candidatos (ajuste se quiser)
ANALYSIS_PAGE_CANDIDATES = [
    "analises.py",          # ⭐ preferido (sem emoji)
    "05_📈_Análises.py",
    "05_📈_Analises.py",
    "Análises.py",
    "Analises.py",
]


def _pages_dir() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "pages")


def _load_analises_module():
    """
    Carrega dinamicamente o módulo de análises, suportando nomes com emoji/acentos.
    Mantém cache em sys.modules["analises_module"].
    """
    try:
        if "analises_module" in sys.modules:
            return sys.modules["analises_module"]

        pages_dir = _pages_dir()

        module_path: Optional[str] = None
        for fname in ANALYSIS_PAGE_CANDIDATES:
            p = os.path.join(pages_dir, fname)
            if os.path.exists(p):
                module_path = p
                break

        if not module_path:
            st.error(
                "Arquivo de análises não encontrado.\n\n"
                f"📁 Diretório: {pages_dir}\n"
                f"📄 Candidatos: {ANALYSIS_PAGE_CANDIDATES}"
            )
            return None

        spec = importlib.util.spec_from_file_location("analises_module", module_path)
        if spec is None or spec.loader is None:
            st.error("Não foi possível carregar o módulo de análises (spec inválida).")
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules["analises_module"] = module
        spec.loader.exec_module(module)
        return module

    except Exception as e:
        st.error(f"Erro ao carregar módulo de análises: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None


def _call_page_main(page_module_path: str, **kwargs):
    """
    Importa módulo de página e chama main().
    """
    try:
        mod = __import__(page_module_path, fromlist=["main"])
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            f"Página não encontrada: {page_module_path}. "
            f"Verifique se existe o arquivo em {_pages_dir()} e se o nome está correto."
        ) from e
    except ImportError as e:
        # Captura casos como: cannot import name 'check_permission' from 'core.auth'
        raise ImportError(
            f"Falha ao importar dependências da página '{page_module_path}'. "
            f"Erro original: {e}"
        ) from e

    if not hasattr(mod, "main"):
        raise AttributeError(f"Módulo {page_module_path} não tem função main()")

    return mod.main(**kwargs) if kwargs else mod.main()


def show_home_page():
    try:
        _call_page_main("pages.home")
    except Exception as e:
        st.error(f"Erro ao carregar página Home: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def show_shows_page():
    try:
        _call_page_main("pages.shows")
    except Exception as e:
        st.error(f"Erro ao carregar página de Shows: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def show_transacoes_page():
    try:
        _call_page_main("pages.transacoes")
    except Exception as e:
        st.error(f"Erro ao carregar página de Transações: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def show_relatorios_page():
    try:
        _call_page_main("pages.relatorios")
    except Exception as e:
        st.error(f"Erro ao carregar página de Relatórios: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def show_cadastros_page(data=None):
    """
    Opcionalmente permite passar data carregada para evitar reload,
    mas funciona mesmo sem.
    """
    try:
        if data is not None:
            _call_page_main("pages.cadastros", data=data)
        else:
            _call_page_main("pages.cadastros")
    except Exception as e:
        st.error(f"Erro ao carregar página de Cadastros: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def show_receitas_vs_despesas(data=None):
    try:
        from core.data_loader import data_loader
        if data is None:
            with st.spinner("Carregando dados..."):
                data = data_loader.load_all_data()

        mod = _load_analises_module()
        if not mod:
            return

        fn = getattr(mod, "show_receitas_vs_despesas", None)
        if not callable(fn):
            st.error("Função show_receitas_vs_despesas não encontrada no módulo de análises.")
            st.caption("Garanta que o arquivo de análises tenha: def show_receitas_vs_despesas(data): ...")
            return

        fn(data)

    except Exception as e:
        st.error(f"Erro ao carregar análise: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def show_despesas_detalhadas(data=None):
    try:
        from core.data_loader import data_loader
        if data is None:
            with st.spinner("Carregando dados..."):
                data = data_loader.load_all_data()

        mod = _load_analises_module()
        if not mod:
            return

        fn = getattr(mod, "show_despesas_detalhadas", None)
        if not callable(fn):
            st.error("Função show_despesas_detalhadas não encontrada no módulo de análises.")
            return

        fn(data)

    except Exception as e:
        st.error(f"Erro ao carregar análise de Despesas: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def show_receitas_detalhadas(data=None):
    try:
        from core.data_loader import data_loader
        if data is None:
            with st.spinner("Carregando dados..."):
                data = data_loader.load_all_data()

        mod = _load_analises_module()
        if not mod:
            return

        fn = getattr(mod, "show_receitas_detalhadas", None)
        if not callable(fn):
            st.error("Função show_receitas_detalhadas não encontrada no módulo de análises.")
            return

        fn(data)

    except Exception as e:
        st.error(f"Erro ao carregar análise de Receitas: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


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
    if page_name in PAGE_FUNCTIONS:
        try:
            PAGE_FUNCTIONS[page_name](**kwargs)
        except Exception as e:
            st.error(f"Erro ao renderizar página {page_name}: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.error(f"Página '{page_name}' não encontrada")
