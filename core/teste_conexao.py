"""
Integração com Google Cloud Platform
Gerencia autenticação e inicialização de clientes
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, Any, Optional, Tuple, List
import json
import os
from pathlib import Path
import time
import logging
from datetime import datetime
import re

class GoogleCloudManager:
    """
    Gerenciador de conexão com Google Cloud e Google Sheets API
    """
    
    # Configurações de retry
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    
    REQUIRED_CRED_FIELDS = [
        'type', 'project_id', 'private_key_id', 'private_key',
        'client_email', 'client_id', 'auth_uri', 'token_uri',
        'auth_provider_x509_cert_url', 'client_x509_cert_url'
    ]
    
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.credentials = None
        self._initialized = False
        self._connection_error = None
        self._last_attempt_time = None
        self._initialization_logs = []
        
    def _log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        self._initialization_logs.append(log_entry)
        if level == "ERROR": logging.error(log_entry)
        elif level == "WARNING": logging.warning(log_entry)
        else: logging.info(log_entry)
    
    def _validate_credentials_dict(self, creds_dict: dict) -> Tuple[bool, Optional[str]]:
        missing_fields = [f for f in self.REQUIRED_CRED_FIELDS if f not in creds_dict or not creds_dict[f]]
        if missing_fields:
            return False, f"Campos ausentes: {', '.join(missing_fields)}"
        
        if not creds_dict.get('private_key', '').startswith('-----BEGIN PRIVATE KEY-----'):
            return False, "private_key com formato inválido."
        
        return True, None

    def initialize(self, show_messages: bool = False) -> bool:
        self._last_attempt_time = datetime.now()
        self._initialization_logs = []
        
        if self._initialized and self.client:
            return True
        
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                self._log(f"Tentativa {attempt} de {self.MAX_RETRIES}")
                
                creds_dict = None
                creds_source = ""

                # 1. Tentar st.secrets (Prioridade no Streamlit Cloud)
                if "google_credentials" in st.secrets:
                    creds_dict = dict(st.secrets["google_credentials"])
                    creds_source = "st.secrets"
                
                # 2. Tentar arquivo local
                elif Path("google_credentials.json").exists():
                    with open("google_credentials.json", 'r') as f:
                        creds_dict = json.load(f)
                    creds_source = "google_credentials.json local"

                if not creds_dict:
                    self._connection_error = (
                        "❌ Credenciais não configuradas. "
                        "Copie .streamlit/secrets.toml.example → .streamlit/secrets.toml e preencha. "
                        "Tutorial: docs/SETUP_GOOGLE_SHEETS.md"
                    )
                    return False

                # Validação das credenciais
                # Nota: TOML já carrega private_key com newlines reais, não precisamos fazer replace
                is_valid, error_msg = self._validate_credentials_dict(creds_dict)
                if not is_valid:
                    self._connection_error = f"Erro na estrutura ({creds_source}): {error_msg}"
                    continue

                # Autorização
                self.credentials = Credentials.from_service_account_info(
                    creds_dict,
                    scopes=[
                        'https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/drive'
                    ]
                )
                self.client = gspread.authorize(self.credentials)
                
                # Obter ID da planilha (do secrets ou constante)
                spreadsheet_id = st.secrets.get("spreadsheet_id", "1TZDj3ZNfFluXLTlc4hkkvMb0gs17WskzwS9LapR44eI")
                self.spreadsheet = self.client.open_by_key(spreadsheet_id)
                
                self._initialized = True
                self._log(f"Sucesso via {creds_source}")
                if show_messages: st.success("✅ Conectado ao Google Sheets!")
                return True

            except Exception as e:
                self._connection_error = str(e)
                self._log(f"Falha na tentativa {attempt}: {e}", "ERROR")
                time.sleep(self.RETRY_DELAY)

        if show_messages: st.error(f"❌ Falha: {self._connection_error}")
        return False

    def get_worksheet(self, worksheet_name: str):
        """Retorna uma aba específica da planilha aberta"""
        try:
            if not self.client: self.initialize()
            return self.spreadsheet.worksheet(worksheet_name)
        except Exception as e:
            self._log(f"Erro ao acessar aba {worksheet_name}: {e}", "ERROR")
            return None

# --- INSTANCIAÇÃO COM CACHE DO STREAMLIT ---
@st.cache_resource
def get_google_manager():
    """
    Mantém uma única instância do manager e da conexão
    durante toda a sessão do servidor Streamlit.
    """
    manager = GoogleCloudManager()
    manager.initialize()
    return manager

# Exporta a instância para o resto do app
google_cloud_manager = get_google_manager()