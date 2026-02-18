"""
Módulo de autenticação e controle de acesso
Implementa login simples (dev) + JWT opcional
"""

import streamlit as st
import hashlib
import time
from datetime import datetime, timedelta
import jwt


def hash_password(password: str) -> str:
    salt = st.secrets.get("auth_salt", "rockbuzz_salt_2024")
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def validate_credentials(username: str, password: str) -> bool:
    # DEV fallback (simples)
    valid_users = {
        "admin": "admin123",
        "Murillo": "murillo123",
        "Tay": "tay123",
        "Everton": "everton123",
        "Helio": "helio123",
        "Kiko": "kiko123",
        "Naldo": "naldo123",
    }
    if username in valid_users and valid_users[username] == password:
        return True

    # secrets.toml (opcional)
    try:
        credentials = st.secrets.get("credentials", {})
        user_cred = credentials.get(username)
        if user_cred:
            stored_hash = user_cred.get("password_hash")
            return stored_hash == hash_password(password)
    except Exception:
        pass

    return False


def create_auth_token(username: str) -> str:
    payload = {"username": username, "exp": datetime.now() + timedelta(hours=8), "iat": datetime.now()}
    secret = st.secrets.get("jwt_secret", "rockbuzz_jwt_secret_2024")
    return jwt.encode(payload, secret, algorithm="HS256")


def validate_token(token: str) -> bool:
    try:
        secret = st.secrets.get("jwt_secret", "rockbuzz_jwt_secret_2024")
        jwt.decode(token, secret, algorithms=["HS256"])
        return True
    except Exception:
        return False


def get_user_role(username: str) -> str:
    credentials = st.secrets.get("credentials", {})
    user_cred = credentials.get(username, {})
    return user_cred.get("role", "membro")


def init_session_state():
    defaults = {
        "authenticated": False,
        "user_name": None,
        "user_role": "membro",
        "auth_token": None,
        "login_time": None,
        "current_page": "Home",
        "data_cache": {},
        "last_cache_update": None,
        "filter_period": "Todo período",
        "filter_start_date": None,
        "filter_end_date": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def check_password() -> bool:
    if st.session_state.get("authenticated", False):
        token = st.session_state.get("auth_token")
        if token and validate_token(token):
            return True

    st.title("🔐 Rockbuzz Finance - Login")

    with st.form("login_form"):
        username = st.text_input("Usuário", key="login_username")
        password = st.text_input("Senha", type="password", key="login_password")
        submit = st.form_submit_button("Entrar")

        if submit:
            if validate_credentials(username, password):
                st.session_state.authenticated = True
                st.session_state.auth_token = create_auth_token(username)
                st.session_state.user_name = username
                st.session_state.user_role = get_user_role(username)
                st.session_state.login_time = datetime.now()
                st.success(f"Bem-vindo, {username}!")
                time.sleep(0.6)
                st.rerun()
            else:
                st.error("Credenciais inválidas!")

    return False


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
