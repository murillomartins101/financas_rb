# financas_rb/core/auth.py
import os
import hmac
import streamlit as st
from typing import Any, Dict, Set


# =========================
# Sessão / Estado
# =========================
def init_session_state() -> None:
    """
    Inicializa chaves necessárias no st.session_state.
    Mantém compatibilidade com app.py e páginas.
    """
    defaults = {
        "authenticated": False,
        "user": None,                 # ex: {"username": "admin", "is_admin": True}
        "permissions": None,          # ex: {"*", "cadastros:view"}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def is_logged_in() -> bool:
    return bool(st.session_state.get("authenticated"))


def logout() -> None:
    """
    Faz logout limpando o essencial.
    """
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.session_state["permissions"] = None


# =========================
# Auth (senha)
# =========================
def _get_admin_password() -> str:
    """
    Busca senha do admin de forma compatível com:
      - st.secrets["auth"]["password"]
      - st.secrets["PASSWORD"]
      - env var PASSWORD
      - env var ADMIN_PASSWORD
    """
    # secrets.toml recomendado:
    # [auth]
    # password="SUA_SENHA"
    try:
        if "auth" in st.secrets and "password" in st.secrets["auth"]:
            return str(st.secrets["auth"]["password"])
    except Exception:
        pass

    try:
        if "PASSWORD" in st.secrets:
            return str(st.secrets["PASSWORD"])
    except Exception:
        pass

    return os.getenv("ADMIN_PASSWORD") or os.getenv("PASSWORD") or ""


def _constant_time_equals(a: str, b: str) -> bool:
    """
    Comparação em tempo constante (evita timing attack bobo).
    """
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def check_password() -> bool:
    """
    Tela de login simples (Streamlit).
    Retorna True se usuário autenticado.

    Compatível com app.py que chama:
      from core.auth import check_password, init_session_state
    """
    init_session_state()

    if st.session_state.get("authenticated"):
        return True

    admin_password = _get_admin_password()
    if not admin_password:
        st.error(
            "Senha não configurada.\n\n"
            "Configure em `.streamlit/secrets.toml`:\n"
            "[auth]\npassword = \"...\"\n"
            "ou defina env var ADMIN_PASSWORD."
        )
        return False

    st.markdown("### Login")
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Usuário", value="admin")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

    if submitted:
        if _constant_time_equals(password, admin_password):
            st.session_state["authenticated"] = True
            st.session_state["user"] = {"username": username, "is_admin": (username == "admin")}
            # permissões default: admin = tudo
            st.session_state["permissions"] = {"*"} if username == "admin" else set()
            st.success("Login realizado.")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
            st.session_state["authenticated"] = False
            return False

    return st.session_state.get("authenticated", False)


# =========================
# Permissões
# =========================
def _get_permissions() -> Set[str]:
    perms = st.session_state.get("permissions")

    if perms is None:
        user = st.session_state.get("user") or {}
        if user.get("is_admin") is True or user.get("username") == "admin":
            return {"*"}
        return set()

    if isinstance(perms, set):
        return perms
    if isinstance(perms, (list, tuple)):
        return set(perms)
    if isinstance(perms, str):
        return {perms}

    return set()


def check_permission(permission: str, *, fail_silently: bool = False) -> bool:
    """
    Verifica permissão.
    Regra: "*" libera tudo.
    """
    perms = _get_permissions()
    ok = ("*" in perms) or (permission in perms)

    if (not ok) and (not fail_silently):
        st.error("Você não tem permissão para acessar esta área.")
    return ok


def require_permission(permission: str) -> None:
    if not check_permission(permission):
        st.stop()


def require_login() -> None:
    if not is_logged_in():
        st.error("Sessão expirada. Faça login novamente.")
        st.stop()
