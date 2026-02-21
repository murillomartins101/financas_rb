"""
Rockbuzz Finance - Dashboard Financeiro para Bandas
Arquivo principal da aplicação Streamlit (Página Home)

Atualização (fix de Google Sheets e DataLoader):
- Import correto do data_loader
- Tratamento de erros SSL
- Fallback para Excel quando necessário
- Diagnóstico detalhado de conexão
"""

import os
import sys
import streamlit as st
import traceback
from datetime import datetime

# Adicionar diretório raiz ao path para garantir imports corretos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.auth import check_password, init_session_state
from core.ui_components import setup_page_config, render_sidebar, render_footer
from core.navigation import render_page
from core.google_cloud import google_cloud_manager
from core.data_loader import data_loader, load_financial_data, get_sheet_df

def _get_app_config() -> dict:
    """Obtém configuração da aplicação de secrets.toml e variáveis de ambiente"""
    cfg = {
        "primary_source": "google", 
        "allow_fallback": True,  # Alterado para True por padrão
        "spreadsheet_id": None,
        "credentials_path": None
    }

    # st.secrets
    try:
        if "data_config" in st.secrets:
            cfg["primary_source"] = st.secrets["data_config"].get("primary_source", cfg["primary_source"])
            cfg["allow_fallback"] = bool(st.secrets["data_config"].get("allow_fallback", cfg["allow_fallback"]))
            cfg["spreadsheet_id"] = st.secrets["data_config"].get("spreadsheet_id")
        elif "app" in st.secrets:
            cfg["primary_source"] = st.secrets["app"].get("primary_source", cfg["primary_source"])
            cfg["allow_fallback"] = bool(st.secrets["app"].get("allow_fallback", cfg["allow_fallback"]))
            cfg["spreadsheet_id"] = st.secrets["app"].get("spreadsheet_id")
        
        # Credenciais do Google
        if "google_credentials" in st.secrets:
            cfg["credentials_json"] = st.secrets["google_credentials"].get("credentials_json")
    except Exception as e:
        st.sidebar.caption(f"⚠️ Erro ao ler secrets: {e}")

    # env vars (sobrescrevem secrets)
    if os.getenv("PRIMARY_SOURCE"):
        cfg["primary_source"] = os.getenv("PRIMARY_SOURCE", cfg["primary_source"])
    if os.getenv("ALLOW_FALLBACK") is not None:
        cfg["allow_fallback"] = os.getenv("ALLOW_FALLBACK", "true").strip().lower() in ("1", "true", "yes", "y")
    if os.getenv("SPREADSHEET_ID"):
        cfg["spreadsheet_id"] = os.getenv("SPREADSHEET_ID")
    if os.getenv("GOOGLE_CREDENTIALS_JSON"):
        cfg["credentials_json"] = os.getenv("GOOGLE_CREDENTIALS_JSON")

    cfg["primary_source"] = (cfg["primary_source"] or "google").strip().lower()
    cfg["allow_fallback"] = bool(cfg["allow_fallback"])
    
    return cfg


def _render_google_setup_help():
    """Renderiza ajuda para configuração do Google Sheets"""
    st.error("❌ Falha na autenticação com Google Sheets")
    st.caption('Configuração atual: primary_source = "google" e allow_fallback = false')

    status = google_cloud_manager.get_connection_status()
    error_msg = status.get("error") or "Erro não especificado"
    
    # Diagnóstico específico para erro SSL
    if "SSL" in error_msg or "EOF" in error_msg:
        st.warning("🔒 **Problema de SSL detectado**")
        st.markdown("""
        **Possíveis causas:**
        - Certificados SSL desatualizados
        - Firewall/Proxy bloqueando conexão
        - Problema de rede corporativa
        
        **Soluções rápidas:**
        1. Atualizar certificados: `pip install --upgrade certifi`
        2. Usar fallback Excel: configure `allow_fallback = true`
        3. Verificar conexão com internet
        """)

    st.write(f"**Problema:** {error_msg}")

    st.markdown("### Como resolver (escolha UMA opção)")
    st.markdown("""
    1. **Configurar Google Sheets:** Siga o guia em `docs/SETUP_GOOGLE_SHEETS.md`.
    2. **Ativar Fallback Excel:** No arquivo `.streamlit/secrets.toml`, defina `allow_fallback = true`.
    3. **Verificar Conexão:** Certifique-se de que o ID da planilha está correto e compartilhado com o e-mail da conta de serviço.
    """)

def main():
    setup_page_config()
    init_session_state()

    if not check_password():
        st.stop()