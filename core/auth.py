"""
Módulo de autenticação e controle de acesso
Implementa login seguro com expiração de token
"""

import streamlit as st
import hashlib
import time
from datetime import datetime, timedelta
import jwt
from typing import Optional, Dict, Tuple

def hash_password(password: str) -> str:
    """
    Cria hash seguro da senha usando SHA-256 com salt
    
    Args:
        password: Senha em texto claro
        
    Returns:
        Hash da senha
    """
    salt = st.secrets.get("auth_salt", "rockbuzz_salt_2024")
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

def check_password() -> bool:
    """
    Verifica credenciais do usuário e gerencia sessão
    
    Returns:
        True se autenticado com sucesso
    """
    
    # Se já autenticado e token válido
    if st.session_state.get("authenticated", False):
        token = st.session_state.get("auth_token")
        if token and validate_token(token):
            return True
    
    # Formulário de login
    st.title("🔐 Rockbuzz Finance - Login")
    
    with st.form("login_form"):
        username = st.text_input("Usuário", key="login_username")
        password = st.text_input("Senha", type="password", key="login_password")
        submit = st.form_submit_button("Entrar")
        
        if submit:
            if validate_credentials(username, password):
                # Criar token JWT
                token = create_auth_token(username)
                st.session_state.authenticated = True
                st.session_state.auth_token = token
                st.session_state.user_name = username
                st.session_state.user_role = get_user_role(username)
                st.session_state.login_time = datetime.now()
                
                st.success(f"Bem-vindo, {username}!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Credenciais inválidas!")
    
    return False

def validate_credentials(username: str, password: str) -> bool:
    """
    Valida credenciais do usuário.
    Tenta usar secrets.toml primeiro, se falhar usa credenciais de desenvolvimento.
    """
    
    try:
        # Carregar credenciais do secrets.toml
        credentials = st.secrets.get("credentials", {})
        user_cred = credentials.get(username)
        
        if user_cred:
            stored_hash = user_cred.get("password_hash")
            input_hash = hash_password(password)
            return stored_hash == input_hash
        
        return False
    except Exception:
        # Fallback para credenciais de desenvolvimento
        # IMPORTANTE: Remover em produção!
        valid_users = {
            "admin": "admin123",
            "Murillo": "murillo123",
            "Tay": "tay123",
            "Everton": "everton123",
            "Helio": "helio123",
            "Kiko": "kiko123",
            "Naldo": "naldo123"
        }
        
        return username in valid_users and valid_users[username] == password

def create_auth_token(username: str) -> str:
    """
    Cria token JWT para autenticação
    
    Args:
        username: Nome de usuário
        
    Returns:
        Token JWT assinado
    """
    payload = {
        "username": username,
        "exp": datetime.now() + timedelta(hours=8),  # Expira em 8 horas
        "iat": datetime.now()
    }
    
    secret = st.secrets.get("jwt_secret", "rockbuzz_jwt_secret_2024")
    return jwt.encode(payload, secret, algorithm="HS256")

def validate_token(token: str) -> bool:
    """
    Valida token JWT
    
    Args:
        token: Token JWT
        
    Returns:
        True se token válido
    """
    try:
        secret = st.secrets.get("jwt_secret", "rockbuzz_jwt_secret_2024")
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return True
    except:
        return False

def get_user_role(username: str) -> str:
    """
    Obtém role do usuário (admin ou membro)
    
    Args:
        username: Nome de usuário
        
    Returns:
        Role do usuário
    """
    credentials = st.secrets.get("credentials", {})
    user_cred = credentials.get(username, {})
    return user_cred.get("role", "membro")

def init_session_state():
    """
    Inicializa o estado da sessão com valores padrão
    """
    defaults = {
        "authenticated": False,
        "user_name": None,
        "user_role": "membro",
        "auth_token": None,
        "login_time": None,
        "current_page": "Home",
        "data_cache": {},
        "last_cache_update": None,
        "filter_period": "Mês atual"
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def check_permission(required_role: str = "membro") -> bool:
    """
    Verifica se usuário tem permissão para acessar recurso
    
    Args:
        required_role: Role mínima requerida
        
    Returns:
        True se usuário tem permissão
    """
    user_role = st.session_state.get("user_role", "membro")
    
    role_hierarchy = {
        "membro": 1,
        "admin": 2
    }
    
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level

def logout():
    """
    Realiza logout do usuário limpando a sessão
    """
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()