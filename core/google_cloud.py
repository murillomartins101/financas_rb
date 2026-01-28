"""
Integração com Google Cloud Platform
Gerencia autenticação e inicialização de clientes
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, Any, Optional
import json
import os
from pathlib import Path

class GoogleCloudManager:
    """
    Gerenciador de conexão com Google Cloud e Google Sheets API
    """
    
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.credentials = None
        
    def initialize(self) -> bool:
        """
        Inicializa cliente do Google Sheets
        
        Returns:
            True se inicializado com sucesso
        """
        try:
            # Método 1: Usar secrets.toml (recomendado para Streamlit Cloud)
            if "google_credentials" in st.secrets:
                creds_dict = dict(st.secrets["google_credentials"])
                self.credentials = Credentials.from_service_account_info(
                    creds_dict,
                    scopes=['https://www.googleapis.com/auth/spreadsheets',
                           'https://www.googleapis.com/auth/drive']
                )
            
            # Método 2: Usar arquivo JSON local
            elif os.path.exists("google_credentials.json"):
                self.credentials = Credentials.from_service_account_file(
                    "google_credentials.json",
                    scopes=['https://www.googleapis.com/auth/spreadsheets',
                           'https://www.googleapis.com/auth/drive']
                )
            
            # Método 3: Variáveis de ambiente
            else:
                creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
                if creds_json:
                    creds_dict = json.loads(creds_json)
                    self.credentials = Credentials.from_service_account_info(
                        creds_dict,
                        scopes=['https://www.googleapis.com/auth/spreadsheets',
                               'https://www.googleapis.com/auth/drive']
                    )
                else:
                    st.error("Credenciais do Google Cloud não encontradas!")
                    return False
            
            # Criar cliente gspread
            self.client = gspread.authorize(self.credentials)
            
            # Carregar spreadsheet
            spreadsheet_id = st.secrets.get("spreadsheet_id")
            if spreadsheet_id:
                self.spreadsheet = self.client.open_by_key(spreadsheet_id)
            else:
                st.error("ID da planilha não configurado!")
                return False
            
            st.success("✅ Conectado ao Google Sheets")
            return True
            
        except Exception as e:
            st.error(f"❌ Erro ao conectar ao Google Sheets: {str(e)}")
            return False
    
    def get_worksheet(self, sheet_name: str):
        """
        Obtém worksheet pelo nome
        
        Args:
            sheet_name: Nome da aba
            
        Returns:
            Worksheet object ou None
        """
        try:
            if self.spreadsheet:
                return self.spreadsheet.worksheet(sheet_name)
        except Exception as e:
            st.error(f"Erro ao acessar aba {sheet_name}: {str(e)}")
        return None
    
    def test_connection(self) -> bool:
        """
        Testa conexão com Google Sheets
        
        Returns:
            True se conexão bem sucedida
        """
        try:
            if self.client and self.spreadsheet:
                # Tenta acessar a primeira aba
                worksheets = self.spreadsheet.worksheets()
                return len(worksheets) > 0
        except:
            pass
        return False

# Instância global do gerenciador
google_cloud_manager = GoogleCloudManager()