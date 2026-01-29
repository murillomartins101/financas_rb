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
        self._initialized = False
        self._connection_error = None
        
    def initialize(self, show_messages: bool = False) -> bool:
        """
        Inicializa cliente do Google Sheets
        
        Args:
            show_messages: Se True, mostra mensagens de sucesso/erro na UI
        
        Returns:
            True se inicializado com sucesso
        """
        # Se já foi inicializado com sucesso, retorna True
        if self._initialized and self.client and self.spreadsheet:
            return True
            
        try:
            # Obter diretório base do projeto
            base_dir = Path(__file__).parent.parent
            json_path = base_dir / "google_credentials.json"
            
            # Método 1: Usar arquivo JSON local (prioridade para desenvolvimento local)
            if json_path.exists():
                self.credentials = Credentials.from_service_account_file(
                    str(json_path),
                    scopes=['https://www.googleapis.com/auth/spreadsheets',
                           'https://www.googleapis.com/auth/drive']
                )
            
            # Método 2: Usar secrets.toml (recomendado para Streamlit Cloud)
            elif "google_credentials" in st.secrets:
                creds_dict = dict(st.secrets["google_credentials"])
                self.credentials = Credentials.from_service_account_info(
                    creds_dict,
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
                    self._connection_error = "Credenciais do Google Cloud nao configuradas"
                    return False
            
            # Criar cliente gspread
            self.client = gspread.authorize(self.credentials)
            
            # Carregar spreadsheet
            spreadsheet_id = st.secrets.get("spreadsheet_id")
            if spreadsheet_id:
                self.spreadsheet = self.client.open_by_key(spreadsheet_id)
            else:
                self._connection_error = "ID da planilha nao configurado"
                return False
            
            self._initialized = True
            self._connection_error = None
            
            if show_messages:
                st.success("Conectado ao Google Sheets")
            return True
            
        except Exception as e:
            self._connection_error = str(e)
            if show_messages:
                st.error(f"Erro ao conectar ao Google Sheets: {str(e)}")
            return False
    
    def get_connection_status(self) -> dict:
        """
        Retorna o status da conexao com Google Sheets
        
        Returns:
            Dict com 'connected' (bool), 'source' (str), 'error' (str ou None)
        """
        if self._initialized and self.client and self.spreadsheet:
            return {
                'connected': True,
                'source': 'Google Sheets',
                'error': None
            }
        else:
            return {
                'connected': False,
                'source': 'Excel local',
                'error': self._connection_error
            }
    
    def test_connection_live(self) -> dict:
        """
        Testa a conexao em tempo real com Google Sheets
        
        Returns:
            Dict com 'success' (bool), 'message' (str), 'worksheets' (list ou None)
        """
        try:
            if not self.client or not self.spreadsheet:
                # Tentar inicializar primeiro
                if not self.initialize():
                    return {
                        'success': False,
                        'message': self._connection_error or 'Nao foi possivel conectar',
                        'worksheets': None
                    }
            
            # Testar acesso real a planilha
            worksheets = self.spreadsheet.worksheets()
            worksheet_names = [ws.title for ws in worksheets]
            
            return {
                'success': True,
                'message': f'Conectado! {len(worksheets)} abas encontradas',
                'worksheets': worksheet_names
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro: {str(e)}',
                'worksheets': None
            }
    
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
