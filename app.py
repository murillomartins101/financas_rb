"""
Rockbuzz Finance - Dashboard Financeiro para Bandas
Arquivo principal da aplicação Streamlit (Página Home)

Atualização (fix de Google Sheets):
- Se primary_source="google" e allow_fallback=false, tenta inicializar Google Sheets automaticamente.
- Exibe diagnóstico acionável (secrets/env vars) quando falhar.
"""

import os
import streamlit as st

from core.auth import check_password, init_session_state
from core.ui_components import setup_page_config, render_sidebar, render_footer
from core.navigation import render_page
from core.google_cloud import google_cloud_manager


def _get_app_config() -> dict:
    cfg = {"primary_source": "google", "allow_fallback": False}

    # st.secrets
    try:
        if "data_config" in st.secrets:
            cfg["primary_source"] = st.secrets["data_config"].get("primary_source", cfg["primary_source"])
            cfg["allow_fallback"] = bool(st.secrets["data_config"].get("allow_fallback", cfg["allow_fallback"]))
        elif "app" in st.secrets:
            cfg["primary_source"] = st.secrets["app"].get("primary_source", cfg["primary_source"])
            cfg["allow_fallback"] = bool(st.secrets["app"].get("allow_fallback", cfg["allow_fallback"]))
        else:
            if "primary_source" in st.secrets:
                cfg["primary_source"] = st.secrets.get("primary_source", cfg["primary_source"])
            if "allow_fallback" in st.secrets:
                cfg["allow_fallback"] = bool(st.secrets.get("allow_fallback", cfg["allow_fallback"]))
    except Exception:
        pass

    # env vars
    if os.getenv("PRIMARY_SOURCE"):
        cfg["primary_source"] = os.getenv("PRIMARY_SOURCE", cfg["primary_source"])
    if os.getenv("ALLOW_FALLBACK") is not None:
        cfg["allow_fallback"] = os.getenv("ALLOW_FALLBACK", "false").strip().lower() in ("1", "true", "yes", "y")

    cfg["primary_source"] = (cfg["primary_source"] or "google").strip().lower()
    cfg["allow_fallback"] = bool(cfg["allow_fallback"])
    return cfg


def _render_google_setup_help():
    st.error("❌ Falha na autenticação com Google Sheets")
    st.caption('Configuração: primary_source = "google" e allow_fallback = false')

    status = google_cloud_manager.get_connection_status()
    error_msg = status.get("error") or "Erro não especificado"
    suggestion = status.get("suggestion")

    st.write(f"**Problema:** {error_msg}")
    if suggestion:
        st.info(f"💡 Sugestão: {suggestion}")

    st.markdown("### Como resolver (escolha UMA opção)")
    st.markdown(
        """
**1️⃣ secrets.toml (local / Streamlit):**
- Arquivo: `.streamlit/secrets.toml`
- Seção: `[google_credentials]`
- Campos suportados:
  - `credentials_json` (JSON completo) **OU**
  - campos separados (`type`, `project_id`, `private_key`, ...)

**2️⃣ Variáveis de ambiente (recomendado em produção):**
- `GOOGLE_CREDENTIALS_JSON` = JSON completo da Service Account
- `SPREADSHEET_ID` = ID da planilha

**3️⃣ Fallback (para rodar sem Google Sheets):**
- `allow_fallback = true` (permite usar Excel local quando Google falhar)
- ou `primary_source = "excel"`
        """.strip()
    )

    with st.expander("📋 Logs técnicos de inicialização"):
        logs = status.get("logs") or []
        st.code("\n".join(logs) if logs else "Sem logs ainda.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔌 Tentar Conectar Agora", use_container_width=True):
            ok = google_cloud_manager.initialize(show_messages=True)
            if ok:
                st.success("Conexão estabelecida. Recarregando…")
                st.rerun()
            else:
                st.warning("Não foi possível conectar. Veja os logs acima.")
    with col2:
        if st.button("🔄 Recarregar Página", use_container_width=True):
            st.rerun()


def _ensure_primary_source_ready() -> bool:
    cfg = _get_app_config()
    st.session_state["primary_source"] = cfg["primary_source"]
    st.session_state["allow_fallback"] = cfg["allow_fallback"]

    if cfg["primary_source"] != "google":
        return True

    ok = google_cloud_manager.initialize(show_messages=False)
    if ok:
        return True

    if cfg["allow_fallback"]:
        st.warning("Google Sheets indisponível. allow_fallback=true → usando fallback (Excel local).")
        return True

    _render_google_setup_help()
    return False


def main():
    setup_page_config()
    init_session_state()

    if not st.session_state.get("authenticated", False):
        if check_password():
            st.session_state.authenticated = True
            st.rerun()
        st.stop()

    if not _ensure_primary_source_ready():
        st.stop()

    render_sidebar()

    try:
        current = st.session_state.get("current_page", "Home")
        render_page(current)
    except Exception as e:
        st.error(f"Erro inesperado na aplicação: {e}")
        import traceback
        st.code(traceback.format_exc())

    render_footer()


if __name__ == "__main__":
    main()
