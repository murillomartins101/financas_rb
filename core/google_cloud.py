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
    
    # Campos opcionais mas recomendados (para compatibilidade com versões novas)
    OPTIONAL_CRED_FIELDS = [
        'universe_domain'  # Necessário para google-auth >= 2.15
    ]
    
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.credentials = None
        self._initialized = False
        self._connection_error = None
        self._last_attempt_time = None
        self._initialization_logs = []
        self._initialization_attempted = False  # Track if we've tried to initialize
        
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
        
        # Também logar no console em desenvolvimento, mas apenas para erros graves
        # Não logar mensagens sobre credenciais ausentes se ainda não tentamos inicializar
        # (ou seja, se foi apenas uma chamada a get_connection_status sem initialize)
        should_suppress = (
            not self._initialization_attempted and 
            ("credenciais" in message.lower() or "credentials" in message.lower())
        )
        
        if level == "ERROR" and not should_suppress:
            logging.error(log_entry)
        elif level == "WARNING":
            logging.warning(log_entry)
        else:  # INFO and other levels
            logging.info(log_entry)
    
    def _validate_credentials_dict(self, creds_dict: dict) -> Tuple[bool, Optional[str]]:
        """
        Valida se o dicionário de credenciais contém todos os campos necessários
        
        NOTA: Esta função pode modificar creds_dict adicionando valores padrão
        para campos opcionais ausentes (ex: universe_domain).
        
        Args:
            creds_dict: Dicionário com credenciais (pode ser modificado)
            
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
        
        # Verificar campos opcionais e adicionar valores padrão se necessário
        # (isso é feito APÓS a validação para garantir que as credenciais básicas estão corretas)
        missing_optional = []
        for field in self.OPTIONAL_CRED_FIELDS:
            if field not in creds_dict or creds_dict[field] is None or creds_dict[field] == "":
                missing_optional.append(field)
        
        if missing_optional:
            self._log(
                f"Campos opcionais ausentes (recomendado para google-auth >= 2.15): {', '.join(missing_optional)}. "
                "Será usado valor padrão 'googleapis.com' para universe_domain.",
                "WARNING"
            )
            # Adicionar valores padrão para campos opcionais
            if 'universe_domain' not in creds_dict or not creds_dict['universe_domain']:
                creds_dict['universe_domain'] = 'googleapis.com'
        
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
        self._initialization_attempted = True  # Mark that we've attempted initialization
        
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
                
                # Método 1: Usar arquivo JSON local (prioridade para desenvolvimento local)
                # Tentar google_credentials.json primeiro
                json_path = base_dir / "google_credentials.json"
                
                # Se não existir, procurar por outros arquivos JSON de credenciais na raiz
                if not json_path.exists():
                    # Procurar por arquivos JSON que parecem ser credenciais
                    for candidate in base_dir.glob("*.json"):
                        # Pular arquivos que claramente não são credenciais
                        if candidate.name in ['package.json', 'tsconfig.json', 'manifest.json']:
                            continue
                        # Verificar se tem campos de service account
                        try:
                            with open(candidate, 'r') as f:
                                test_creds = json.load(f)
                            if 'type' in test_creds and test_creds.get('type') == 'service_account':
                                json_path = candidate
                                self._log(f"Encontrado arquivo de credenciais: {json_path.name}")
                                break
                        except:
                            continue
                
                if json_path.exists():
                    self._log(f"Encontrado arquivo de credenciais local: {json_path}")
                    try:
                        with open(json_path, 'r') as f:
                            creds_dict = json.load(f)
                        creds_source = f"arquivo local ({json_path.name})"
                        self._log("Credenciais carregadas do arquivo local com sucesso")
                    except json.JSONDecodeError as e:
                        self._log(f"Erro ao decodificar JSON do arquivo local: {e}", "ERROR")
                        self._connection_error = f"Arquivo {json_path.name} contém JSON inválido: {str(e)}"
                        continue
                    except Exception as e:
                        self._log(f"Erro ao ler arquivo local: {e}", "ERROR")
                        self._connection_error = f"Erro ao ler {json_path.name}: {str(e)}"
                        continue
                
                # Método 2: Usar secrets.toml (recomendado para Streamlit Cloud)
                if not creds_dict:
                    try:
                        # Verificar se st.secrets existe e tem conteúdo
                        secrets_available = hasattr(st, 'secrets') and len(st.secrets) > 0
                        
                        if secrets_available:
                            self._log("Arquivo secrets.toml encontrado e carregado pelo Streamlit")
                            
                            # Verificar se contém a chave google_credentials
                            if "google_credentials" in st.secrets:
                                self._log("Encontradas credenciais em st.secrets['google_credentials']")
                                creds_dict = dict(st.secrets["google_credentials"])
                                creds_source = "st.secrets (secrets.toml)"
                                self._log("Credenciais carregadas do secrets.toml com sucesso")
                            else:
                                # secrets.toml existe mas não tem google_credentials
                                self._log(
                                    "secrets.toml existe mas não contém a seção [google_credentials]",
                                    "WARNING"
                                )
                                available_keys = list(st.secrets.keys())
                                self._log(
                                    f"Chaves disponíveis em secrets.toml: {', '.join(available_keys) if available_keys else 'nenhuma'}",
                                    "INFO"
                                )
                        else:
                            self._log("Arquivo secrets.toml não encontrado ou vazio", "INFO")
                    except FileNotFoundError:
                        self._log("Arquivo .streamlit/secrets.toml não existe", "INFO")
                    except Exception as e:
                        self._log(f"Erro ao acessar st.secrets: {str(e)}", "WARNING")
                
                # Método 3: Variáveis de ambiente
                if not creds_dict:
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
                
                # Se ainda não tem credenciais, retornar erro
                if not creds_dict:
                    self._log("Nenhuma fonte de credenciais encontrada", "ERROR")
                    
                    # Construir mensagem de erro mais específica baseada no que foi tentado
                    error_parts = ["❌ Credenciais do Google Cloud não configuradas.\n"]
                    
                    # Verificar se secrets.toml existe mas está incompleto
                    try:
                        if hasattr(st, 'secrets') and len(st.secrets) > 0:
                            if "google_credentials" not in st.secrets:
                                error_parts.append(
                                    "⚠️  O arquivo .streamlit/secrets.toml existe, mas não contém a seção [google_credentials].\n"
                                    "    Verifique se você copiou a estrutura completa do secrets.toml.example.\n"
                                )
                            if "spreadsheet_id" not in st.secrets:
                                error_parts.append(
                                    "⚠️  O arquivo .streamlit/secrets.toml não contém 'spreadsheet_id'.\n"
                                )
                    except Exception:
                        # Ignorar erros ao verificar st.secrets
                        pass
                    
                    error_parts.append(
                        "\n📋 Para configurar, escolha UMA das opções:\n\n"
                        "1️⃣ Arquivo secrets.toml (RECOMENDADO para desenvolvimento local e Streamlit Cloud):\n"
                        "   • Copie: .streamlit/secrets.toml.example → .streamlit/secrets.toml\n"
                        "   • Preencha com suas credenciais reais da Service Account\n"
                        "   • Inclua a seção [google_credentials] com TODOS os campos\n"
                        "   • Adicione spreadsheet_id no topo do arquivo\n"
                        "   • Tutorial: docs/SETUP_GOOGLE_SHEETS.md\n\n"
                        "2️⃣ Arquivo JSON local (alternativa para desenvolvimento):\n"
                        "   • Coloque google_credentials.json na raiz do projeto\n"
                        "   • Configure SPREADSHEET_ID como variável de ambiente\n\n"
                        "3️⃣ Variável de ambiente (para ambientes de CI/CD):\n"
                        "   • Configure GOOGLE_CREDENTIALS_JSON com o JSON completo\n"
                        "   • Configure SPREADSHEET_ID\n\n"
                        "📚 Ajuda detalhada:\n"
                        "   • Setup completo: docs/SETUP_GOOGLE_SHEETS.md\n"
                        "   • Problemas comuns: docs/TROUBLESHOOTING.md\n"
                        "   • Exemplo de estrutura: .streamlit/README.md"
                    )
                    
                    self._connection_error = "".join(error_parts)
                    logging.error("[GOOGLE_CLOUD] Credenciais não encontradas - nenhuma fonte configurada")
                    return False
                
                # Etapa 2: Validar estrutura das credenciais
                self._log("Validando estrutura das credenciais")
                is_valid, error_msg = self._validate_credentials_dict(creds_dict)
                if not is_valid:
                    self._log(f"Validação de credenciais falhou: {error_msg}", "ERROR")
                    self._connection_error = f"Credenciais inválidas ({creds_source}): {error_msg}"
                    continue
                
                self._log("Estrutura das credenciais validada com sucesso")
                
                # Normalizar private_key: garantir que tenha newlines reais
                # Uma chave RSA privada PEM típica tem ~25-30 newlines
                # Se tiver muito poucas, provavelmente são literais \\n que precisam ser convertidos
                if 'private_key' in creds_dict and isinstance(creds_dict['private_key'], str):
                    pk = creds_dict['private_key']
                    real_newlines = pk.count('\n')
                    # Chaves PEM válidas devem ter pelo menos 10 newlines
                    if real_newlines < 10 and '\\n' in pk:
                        self._log(
                            f"Private key tem apenas {real_newlines} newlines reais mas contém '\\\\n' literal. "
                            "Convertendo \\\\n para newlines reais...", 
                            "WARNING"
                        )
                        creds_dict['private_key'] = pk.replace('\\n', '\n')
                        self._log(f"Após conversão: {creds_dict['private_key'].count('\n')} newlines reais")
                
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
                    error_str = str(e)
                    self._log(f"Erro ao autorizar cliente gspread: {error_str}", "ERROR")
                    
                    # Tratar erros específicos de JWT
                    if "invalid_grant" in error_str.lower() or "invalid jwt signature" in error_str.lower():
                        self._connection_error = (
                            "Erro de autenticação JWT: Assinatura inválida.\n\n"
                            "Possíveis causas:\n"
                            "1. A chave da Service Account foi revogada ou excluída no Google Cloud Console\n"
                            "2. O relógio do sistema está dessincronizado (diferença > 5 minutos)\n"
                            "3. A chave privada (private_key) está corrompida ou incompleta\n\n"
                            "Soluções:\n"
                            "1. Verifique se a Service Account ainda existe no Google Cloud Console\n"
                            "2. Gere uma nova chave JSON para a Service Account\n"
                            "3. Verifique a hora do sistema: 'date' no terminal\n"
                            "4. Se usar secrets.toml, certifique-se que private_key tem todas as quebras de linha (\\n)"
                        )
                    else:
                        self._connection_error = f"Erro ao autorizar cliente: {error_str}"
                    continue
                
                # Obter e validar spreadsheet_id
                self._log("Obtendo spreadsheet_id")
                spreadsheet_id = None
                
                # Tentar obter de st.secrets
                try:
                    if "spreadsheet_id" in st.secrets:
                        spreadsheet_id = st.secrets.get("spreadsheet_id")
                        self._log(f"spreadsheet_id encontrado em st.secrets")
                except Exception as e:
                    self._log(f"Erro ao acessar st.secrets para spreadsheet_id: {e}", "WARNING")
                
                # Tentar variável de ambiente como fallback
                if not spreadsheet_id:
                    spreadsheet_id = os.getenv("SPREADSHEET_ID")
                    if spreadsheet_id:
                        self._log(f"spreadsheet_id encontrado em variável de ambiente")
                    else:
                        self._log("spreadsheet_id não encontrado em nenhuma fonte", "ERROR")
                        
                        # Mensagem de erro específica para spreadsheet_id ausente
                        error_msg_parts = [
                            "❌ ID da planilha (spreadsheet_id) não configurado.\n\n"
                            "O spreadsheet_id é obrigatório e identifica qual planilha do Google Sheets será usada.\n\n"
                        ]
                        
                        # Verificar se credentials foram encontrados em secrets.toml
                        if creds_source == "st.secrets (secrets.toml)":
                            error_msg_parts.append(
                                "✅ Suas credenciais foram encontradas em .streamlit/secrets.toml\n"
                                "❌ Mas falta a chave 'spreadsheet_id' nesse arquivo\n\n"
                                "Para corrigir:\n"
                                "1. Abra .streamlit/secrets.toml\n"
                                "2. Adicione no INÍCIO do arquivo (antes de qualquer seção []):\n"
                                '   spreadsheet_id = "SEU_ID_AQUI"\n\n'
                                "3. Para encontrar o ID da sua planilha:\n"
                                "   • Abra a planilha no Google Sheets\n"
                                "   • Copie o ID da URL: docs.google.com/spreadsheets/d/SEU_ID_AQUI/edit\n"
                            )
                        else:
                            error_msg_parts.append(
                                "Configure o spreadsheet_id usando uma das opções:\n\n"
                                "1️⃣ No arquivo secrets.toml (recomendado):\n"
                                "   • Adicione no início: spreadsheet_id = \"SEU_ID_AQUI\"\n\n"
                                "2️⃣ Variável de ambiente:\n"
                                "   • export SPREADSHEET_ID=\"SEU_ID_AQUI\"\n\n"
                            )
                        
                        error_msg_parts.append(
                            "📚 Tutorial completo: docs/SETUP_GOOGLE_SHEETS.md"
                        )
                        
                        self._connection_error = "".join(error_msg_parts)
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
        NÃO tenta inicializar automaticamente - use initialize() para isso.
        
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
            if not self._initialization_attempted:
                error_str = 'Credenciais não configuradas (clique em "Testar Conexão" para verificar)'
            else:
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
                'source': 'Não conectado',
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
