"""
Integração com Google Cloud Platform
Gerencia autenticação e inicialização de clientes
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, Any, Optional, Tuple
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
    RETRY_DELAY = 2  # segundos
    
    # Campos obrigatórios nas credenciais
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
        """
        Registra mensagem de log interna
        
        Args:
            message: Mensagem a ser registrada
            level: Nível do log (INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        self._initialization_logs.append(log_entry)
        
        # Também logar no console em desenvolvimento
        if level == "ERROR":
            logging.error(log_entry)
        elif level == "WARNING":
            logging.warning(log_entry)
        else:
            logging.info(log_entry)
    
    def _validate_credentials_dict(self, creds_dict: dict) -> Tuple[bool, Optional[str]]:
        """
        Valida se o dicionário de credenciais contém todos os campos necessários
        
        Args:
            creds_dict: Dicionário com credenciais
            
        Returns:
            Tupla (válido, mensagem_erro)
        """
        missing_fields = []
        for field in self.REQUIRED_CRED_FIELDS:
            if field not in creds_dict or creds_dict[field] is None or creds_dict[field] == "":
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"Campos obrigatórios ausentes: {', '.join(missing_fields)}"
        
        # Validar formato do tipo
        if creds_dict.get('type') != 'service_account':
            return False, f"Tipo de credencial inválido: '{creds_dict.get('type')}'. Esperado: 'service_account'"
        
        # Validar formato do email
        client_email = creds_dict.get('client_email', '')
        if not client_email.endswith('.iam.gserviceaccount.com'):
            return False, f"client_email inválido: '{client_email}'. Deve terminar com '.iam.gserviceaccount.com'"
        
        # Validar private_key
        private_key = creds_dict.get('private_key', '')
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            return False, "private_key com formato inválido. Deve começar com '-----BEGIN PRIVATE KEY-----'"
        
        return True, None
    
    def _validate_spreadsheet_id(self, spreadsheet_id: str) -> Tuple[bool, Optional[str]]:
        """
        Valida formato do spreadsheet_id
        
        Args:
            spreadsheet_id: ID da planilha
            
        Returns:
            Tupla (válido, mensagem_erro)
        """
        if not spreadsheet_id:
            return False, "spreadsheet_id está vazio"
        
        # ID do Google Sheets geralmente tem 44 caracteres
        if len(spreadsheet_id) < 30:
            return False, f"spreadsheet_id muito curto ({len(spreadsheet_id)} caracteres). IDs válidos geralmente têm ~44 caracteres"
        
        # Verificar caracteres válidos (alfanuméricos, underscores, hífens)
        if not re.match(r'^[a-zA-Z0-9_-]+$', spreadsheet_id):
            return False, "spreadsheet_id contém caracteres inválidos. Apenas letras, números, '_' e '-' são permitidos"
        
        return True, None
    
    def initialize(self, show_messages: bool = False) -> bool:
        """
        Inicializa cliente do Google Sheets com validação robusta e retry
        
        Args:
            show_messages: Se True, mostra mensagens de sucesso/erro na UI
        
        Returns:
            True se inicializado com sucesso
        """
        self._last_attempt_time = datetime.now()
        self._initialization_logs = []  # Limpar logs anteriores
        
        # Se já foi inicializado com sucesso, retorna True
        if self._initialized and self.client and self.spreadsheet:
            self._log("Conexão já inicializada, reutilizando cliente existente")
            return True
        
        self._log("Iniciando processo de autenticação com Google Sheets")
        
        # Tentar inicializar com retry
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                self._log(f"Tentativa {attempt} de {self.MAX_RETRIES}")
                
                # Etapa 1: Carregar credenciais
                creds_dict = None
                creds_source = None
                
                # Obter diretório base do projeto
                base_dir = Path(__file__).parent.parent
                json_path = base_dir / "google_credentials.json"
                
                # Método 1: Usar arquivo JSON local (prioridade para desenvolvimento local)
                if json_path.exists():
                    self._log(f"Encontrado arquivo de credenciais local: {json_path}")
                    try:
                        with open(json_path, 'r') as f:
                            creds_dict = json.load(f)
                        creds_source = "arquivo local (google_credentials.json)"
                        self._log("Credenciais carregadas do arquivo local com sucesso")
                    except json.JSONDecodeError as e:
                        self._log(f"Erro ao decodificar JSON do arquivo local: {e}", "ERROR")
                        self._connection_error = f"Arquivo google_credentials.json contém JSON inválido: {str(e)}"
                        continue
                    except Exception as e:
                        self._log(f"Erro ao ler arquivo local: {e}", "ERROR")
                        self._connection_error = f"Erro ao ler google_credentials.json: {str(e)}"
                        continue
                
                # Método 2: Usar secrets.toml (recomendado para Streamlit Cloud)
                elif "google_credentials" in st.secrets:
                    self._log("Encontradas credenciais em st.secrets['google_credentials']")
                    try:
                        creds_dict = dict(st.secrets["google_credentials"])
                        creds_source = "st.secrets (secrets.toml)"
                        self._log("Credenciais carregadas do secrets.toml com sucesso")
                    except Exception as e:
                        self._log(f"Erro ao carregar secrets do Streamlit: {e}", "ERROR")
                        self._connection_error = f"Erro ao carregar st.secrets['google_credentials']: {str(e)}"
                        continue
                
                # Método 3: Variáveis de ambiente
                else:
                    self._log("Tentando carregar credenciais de variável de ambiente GOOGLE_CREDENTIALS_JSON")
                    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
                    if creds_json:
                        try:
                            creds_dict = json.loads(creds_json)
                            creds_source = "variável de ambiente (GOOGLE_CREDENTIALS_JSON)"
                            self._log("Credenciais carregadas da variável de ambiente com sucesso")
                        except json.JSONDecodeError as e:
                            self._log(f"Erro ao decodificar JSON da variável de ambiente: {e}", "ERROR")
                            self._connection_error = f"GOOGLE_CREDENTIALS_JSON contém JSON inválido: {str(e)}"
                            continue
                    else:
                        self._log("Nenhuma fonte de credenciais encontrada", "ERROR")
                        self._connection_error = (
                            "Credenciais do Google Cloud não configuradas. "
                            "Configure através de:\n"
                            "1. Arquivo 'google_credentials.json' na raiz do projeto, OU\n"
                            "2. st.secrets['google_credentials'] no secrets.toml, OU\n"
                            "3. Variável de ambiente GOOGLE_CREDENTIALS_JSON"
                        )
                        return False
                
                # Etapa 2: Validar estrutura das credenciais
                self._log("Validando estrutura das credenciais")
                is_valid, error_msg = self._validate_credentials_dict(creds_dict)
                if not is_valid:
                    self._log(f"Validação de credenciais falhou: {error_msg}", "ERROR")
                    self._connection_error = f"Credenciais inválidas ({creds_source}): {error_msg}"
                    continue
                
                self._log("Estrutura das credenciais validada com sucesso")
                
                # Etapa 3: Criar objeto Credentials
                self._log("Criando objeto de credenciais do Google")
                try:
                    self.credentials = Credentials.from_service_account_info(
                        creds_dict,
                        scopes=[
                            'https://www.googleapis.com/auth/spreadsheets',
                            'https://www.googleapis.com/auth/drive'
                        ]
                    )
                    self._log("Objeto de credenciais criado com sucesso")
                except Exception as e:
                    self._log(f"Erro ao criar objeto de credenciais: {e}", "ERROR")
                    self._connection_error = f"Erro ao processar credenciais: {str(e)}"
                    continue
                
                # Etapa 4: Criar cliente gspread
                self._log("Autorizando cliente gspread")
                try:
                    self.client = gspread.authorize(self.credentials)
                    self._log("Cliente gspread autorizado com sucesso")
                except Exception as e:
                    self._log(f"Erro ao autorizar cliente gspread: {e}", "ERROR")
                    self._connection_error = f"Erro ao autorizar cliente: {str(e)}"
                    continue
                
                # Obter e validar spreadsheet_id
                self._log("Obtendo spreadsheet_id")
                spreadsheet_id = None
                
                # Tentar obter de st.secrets
                if "spreadsheet_id" in st.secrets:
                    spreadsheet_id = st.secrets.get("spreadsheet_id")
                    self._log(f"spreadsheet_id encontrado em st.secrets")
                else:
                    # Tentar variável de ambiente como fallback
                    spreadsheet_id = os.getenv("SPREADSHEET_ID")
                    if spreadsheet_id:
                        self._log(f"spreadsheet_id encontrado em variável de ambiente")
                    else:
                        self._log("spreadsheet_id não encontrado", "ERROR")
                        self._connection_error = (
                            "ID da planilha não configurado. "
                            "Configure 'spreadsheet_id' em secrets.toml ou na variável de ambiente SPREADSHEET_ID"
                        )
                        return False
                
                # Validar formato do spreadsheet_id
                is_valid, error_msg = self._validate_spreadsheet_id(spreadsheet_id)
                if not is_valid:
                    self._log(f"Validação do spreadsheet_id falhou: {error_msg}", "ERROR")
                    self._connection_error = f"spreadsheet_id inválido: {error_msg}"
                    return False
                
                # Etapa 6: Abrir planilha
                self._log(f"Tentando abrir planilha...")
                try:
                    self.spreadsheet = self.client.open_by_key(spreadsheet_id)
                    self._log(f"Planilha aberta com sucesso: {self.spreadsheet.title}")
                except gspread.exceptions.SpreadsheetNotFound:
                    self._log("Planilha não encontrada", "ERROR")
                    self._connection_error = (
                        f"Planilha não encontrada. "
                        "Verifique se:\n"
                        "1. O ID está correto\n"
                        "2. A planilha existe\n"
                        "3. A Service Account tem permissão de acesso"
                    )
                    return False
                except gspread.exceptions.APIError as e:
                    error_details = str(e)
                    self._log(f"Erro de API do Google: {error_details}", "ERROR")
                    
                    if "PERMISSION_DENIED" in error_details or "403" in error_details:
                        self._connection_error = (
                            f"Permissão negada para acessar a planilha. "
                            f"Compartilhe a planilha com a Service Account (verifique o client_email nas credenciais) "
                            "com permissão de Editor"
                        )
                    else:
                        self._connection_error = f"Erro da API do Google Sheets: {error_details}"
                    
                    # Não fazer retry em erros de permissão
                    if "PERMISSION_DENIED" in error_details or "403" in error_details:
                        return False
                    continue
                except Exception as e:
                    self._log(f"Erro inesperado ao abrir planilha: {e}", "ERROR")
                    self._connection_error = f"Erro ao abrir planilha: {str(e)}"
                    continue
                
                # Etapa 7: Verificar acesso às worksheets
                self._log("Testando acesso às worksheets")
                try:
                    worksheets = self.spreadsheet.worksheets()
                    worksheet_names = [ws.title for ws in worksheets]
                    self._log(f"Acesso confirmado a {len(worksheets)} abas: {', '.join(worksheet_names)}")
                except Exception as e:
                    self._log(f"Erro ao listar worksheets: {e}", "ERROR")
                    self._connection_error = f"Erro ao acessar abas da planilha: {str(e)}"
                    continue
                
                # Sucesso!
                self._initialized = True
                self._connection_error = None
                self._log(f"Conexão estabelecida com sucesso! Fonte: {creds_source}")
                
                if show_messages:
                    st.success(f"✅ Conectado ao Google Sheets\n\nPlanilha: {self.spreadsheet.title}\n{len(worksheets)} abas disponíveis")
                
                return True
                
            except Exception as e:
                self._log(f"Erro inesperado na tentativa {attempt}: {e}", "ERROR")
                self._connection_error = f"Erro inesperado: {str(e)}"
                
                # Fazer retry se não for a última tentativa
                if attempt < self.MAX_RETRIES:
                    delay = self.RETRY_DELAY * (2 ** (attempt - 1))  # Backoff exponencial
                    self._log(f"Aguardando {delay}s antes de tentar novamente...")
                    time.sleep(delay)
                else:
                    self._log("Todas as tentativas falharam", "ERROR")
        
        # Se chegou aqui, todas as tentativas falharam
        if show_messages:
            st.error(f"❌ Erro ao conectar ao Google Sheets\n\n{self._connection_error}")
        
        return False
    
    def get_connection_status(self) -> dict:
        """
        Retorna o status da conexão com Google Sheets com informações detalhadas
        
        Returns:
            Dict com 'connected' (bool), 'source' (str), 'error' (str ou None),
            'last_attempt' (datetime ou None), 'logs' (list), 'suggestion' (str ou None)
        """
        if self._initialized and self.client and self.spreadsheet:
            return {
                'connected': True,
                'source': 'Google Sheets',
                'spreadsheet_title': self.spreadsheet.title if self.spreadsheet else None,
                'error': None,
                'last_attempt': self._last_attempt_time,
                'logs': self._initialization_logs,
                'suggestion': None
            }
        else:
            # Garantir que error sempre é uma string válida
            error_str = str(self._connection_error) if self._connection_error else 'Credenciais não configuradas'
            
            # Gerar sugestão baseada no erro
            suggestion = None
            if self._connection_error:
                error_lower = error_str.lower()
                if "não configuradas" in error_str or "not configured" in error_lower:
                    suggestion = "Configure as credenciais em secrets.toml ou google_credentials.json"
                elif "inválida" in error_str or "invalid" in error_lower:
                    suggestion = "Verifique o formato das credenciais no secrets.toml.example"
                elif "Permissão negada" in error_str or "PERMISSION_DENIED" in error_str:
                    suggestion = "Compartilhe a planilha com a Service Account (client_email das credenciais)"
                elif "não encontrada" in error_str or "not found" in error_lower:
                    suggestion = "Verifique se o spreadsheet_id está correto e se a planilha existe"
            
            return {
                'connected': False,
                'source': 'Excel local',
                'spreadsheet_title': None,
                'error': error_str,
                'last_attempt': self._last_attempt_time,
                'logs': self._initialization_logs,
                'suggestion': suggestion
            }
    
    def get_initialization_logs(self) -> list:
        """
        Retorna os logs de inicialização para diagnóstico
        
        Returns:
            Lista de strings com logs detalhados
        """
        return self._initialization_logs.copy()
    
    def test_connection_live(self) -> dict:
        """
        Testa a conexão em tempo real com Google Sheets
        
        Returns:
            Dict com 'success' (bool), 'message' (str), 'worksheets' (list ou None)
        """
        try:
            if not self.client or not self.spreadsheet:
                # Tentar inicializar primeiro
                if not self.initialize():
                    return {
                        'success': False,
                        'message': self._connection_error or 'Não foi possível conectar',
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
        except Exception:
            pass
        return False

# Instância global do gerenciador
google_cloud_manager = GoogleCloudManager()
