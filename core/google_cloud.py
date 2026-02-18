"""
Integração com Google Cloud Platform
Gerencia autenticação e inicialização de clientes
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from typing import Optional, Tuple
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

    MAX_RETRIES = 3
    RETRY_DELAY = 2  # segundos

    REQUIRED_CRED_FIELDS = [
        "type", "project_id", "private_key_id", "private_key",
        "client_email", "client_id", "auth_uri", "token_uri",
        "auth_provider_x509_cert_url", "client_x509_cert_url"
    ]

    OPTIONAL_CRED_FIELDS = ["universe_domain"]  # google-auth >= 2.15

    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.credentials = None
        self._initialized = False
        self._connection_error = None
        self._last_attempt_time = None
        self._initialization_logs = []
        self._initialization_attempted = False

    def _log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self._initialization_logs.append(log_entry)

        should_suppress = (
            not self._initialization_attempted
            and ("credenciais" in message.lower() or "credentials" in message.lower())
        )

        if level == "ERROR" and not should_suppress:
            logging.error(log_entry)
        elif level == "WARNING":
            logging.warning(log_entry)
        else:
            logging.info(log_entry)

    def _validate_credentials_dict(self, creds_dict: dict) -> Tuple[bool, Optional[str]]:
        missing_fields = []
        for field in self.REQUIRED_CRED_FIELDS:
            if field not in creds_dict or creds_dict[field] in (None, ""):
                missing_fields.append(field)

        if missing_fields:
            return False, f"Campos obrigatórios ausentes: {', '.join(missing_fields)}"

        if creds_dict.get("type") != "service_account":
            return False, f"Tipo de credencial inválido: '{creds_dict.get('type')}'. Esperado: 'service_account'"

        client_email = creds_dict.get("client_email", "")
        if not client_email.endswith(".iam.gserviceaccount.com"):
            return False, f"client_email inválido: '{client_email}'. Deve terminar com '.iam.gserviceaccount.com'"

        private_key = creds_dict.get("private_key", "")
        if not private_key.startswith("-----BEGIN PRIVATE KEY-----"):
            return False, "private_key com formato inválido. Deve começar com '-----BEGIN PRIVATE KEY-----'"

        missing_optional = []
        for field in self.OPTIONAL_CRED_FIELDS:
            if field not in creds_dict or creds_dict[field] in (None, ""):
                missing_optional.append(field)

        if missing_optional:
            self._log(
                "Campos opcionais ausentes (recomendado para google-auth >= 2.15): "
                f"{', '.join(missing_optional)}. Usando padrão 'googleapis.com'.",
                "WARNING",
            )
            if "universe_domain" not in creds_dict or not creds_dict["universe_domain"]:
                creds_dict["universe_domain"] = "googleapis.com"

        return True, None

    def _validate_spreadsheet_id(self, spreadsheet_id: str) -> Tuple[bool, Optional[str]]:
        if not spreadsheet_id:
            return False, "spreadsheet_id está vazio"

        if len(spreadsheet_id) < 30:
            return False, (
                f"spreadsheet_id muito curto ({len(spreadsheet_id)} caracteres). "
                "IDs válidos geralmente têm ~44 caracteres"
            )

        if not re.match(r"^[a-zA-Z0-9_-]+$", spreadsheet_id):
            return False, "spreadsheet_id contém caracteres inválidos. Use apenas letras, números, '_' e '-'"

        return True, None

    def initialize(self, show_messages: bool = False) -> bool:
        self._last_attempt_time = datetime.now()
        self._initialization_logs = []
        self._initialization_attempted = True

        if self._initialized and self.client and self.spreadsheet:
            self._log("Conexão já inicializada, reutilizando cliente existente")
            return True

        self._log("Iniciando processo de autenticação com Google Sheets")

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                self._log(f"Tentativa {attempt} de {self.MAX_RETRIES}")

                creds_dict = None
                creds_source = None

                base_dir = Path(__file__).parent.parent

                # 1) arquivo local
                json_path = base_dir / "google_credentials.json"
                if not json_path.exists():
                    for candidate in base_dir.glob("*.json"):
                        if candidate.name in ["package.json", "tsconfig.json", "manifest.json"]:
                            continue
                        try:
                            with open(candidate, "r", encoding="utf-8") as f:
                                test_creds = json.load(f)
                            if test_creds.get("type") == "service_account":
                                json_path = candidate
                                self._log(f"Encontrado arquivo de credenciais: {json_path.name}")
                                break
                        except Exception:
                            continue

                if json_path.exists():
                    self._log(f"Encontrado arquivo de credenciais local: {json_path}")
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            creds_dict = json.load(f)
                        creds_source = f"arquivo local ({json_path.name})"
                        self._log("Credenciais carregadas do arquivo local com sucesso")
                    except json.JSONDecodeError as e:
                        self._log(f"JSON inválido no arquivo local: {e}", "ERROR")
                        self._connection_error = f"Arquivo {json_path.name} contém JSON inválido: {str(e)}"
                        continue
                    except Exception as e:
                        self._log(f"Erro ao ler arquivo local: {e}", "ERROR")
                        self._connection_error = f"Erro ao ler {json_path.name}: {str(e)}"
                        continue

                # 2) secrets.toml
                if not creds_dict:
                    try:
                        if "google_credentials" in st.secrets:
                            self._log("Encontradas credenciais em st.secrets['google_credentials']")
                            sec = st.secrets["google_credentials"]

                            if "credentials_json" in sec and sec.get("credentials_json"):
                                try:
                                    creds_dict = json.loads(sec.get("credentials_json"))
                                    self._log("Credenciais carregadas de credentials_json (JSON completo)")
                                except json.JSONDecodeError as e:
                                    self._log(f"credentials_json inválido: {e}", "ERROR")
                                    self._connection_error = f"credentials_json inválido no secrets.toml: {str(e)}"
                                    continue
                            else:
                                creds_dict = dict(sec)
                                self._log("Credenciais carregadas como campos separados")

                            creds_source = "st.secrets (secrets.toml)"
                            self._log("Credenciais carregadas do secrets.toml com sucesso")
                    except Exception as e:
                        self._log(f"Secrets.toml não disponível: {str(e)}", "INFO")

                # 3) env var
                if not creds_dict:
                    self._log("Tentando GOOGLE_CREDENTIALS_JSON (env)")
                    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
                    if creds_json:
                        try:
                            creds_dict = json.loads(creds_json)
                            creds_source = "env (GOOGLE_CREDENTIALS_JSON)"
                            self._log("Credenciais carregadas da env com sucesso")
                        except json.JSONDecodeError as e:
                            self._log(f"JSON inválido na env: {e}", "ERROR")
                            self._connection_error = f"GOOGLE_CREDENTIALS_JSON contém JSON inválido: {str(e)}"
                            continue

                if not creds_dict:
                    self._log("Nenhuma fonte de credenciais encontrada", "ERROR")
                    self._connection_error = (
                        "❌ Credenciais do Google Cloud não configuradas.\n\n"
                        "Configure via:\n"
                        "- .streamlit/secrets.toml (google_credentials)\n"
                        "- google_credentials.json na raiz\n"
                        "- env GOOGLE_CREDENTIALS_JSON\n"
                    )
                    return False

                # validar
                self._log("Validando estrutura das credenciais")
                is_valid, error_msg = self._validate_credentials_dict(creds_dict)
                if not is_valid:
                    self._log(f"Validação falhou: {error_msg}", "ERROR")
                    self._connection_error = f"Credenciais inválidas ({creds_source}): {error_msg}"
                    continue

                # normalizar private_key \n
                if "private_key" in creds_dict and isinstance(creds_dict["private_key"], str):
                    pk = creds_dict["private_key"]
                    if pk.count("\n") < 10 and "\\n" in pk:
                        self._log("Convertendo \\n literal para quebras de linha reais", "WARNING")
                        creds_dict["private_key"] = pk.replace("\\n", "\n")

                # creds object
                self._log("Criando objeto Credentials")
                try:
                    self.credentials = Credentials.from_service_account_info(
                        creds_dict,
                        scopes=[
                            "https://www.googleapis.com/auth/spreadsheets",
                            "https://www.googleapis.com/auth/drive",
                        ],
                    )
                    self._log("Credentials criado com sucesso")
                except Exception as e:
                    self._log(f"Erro ao criar Credentials: {e}", "ERROR")
                    self._connection_error = f"Erro ao processar credenciais: {str(e)}"
                    continue

                # gspread client
                self._log("Autorizando gspread")
                try:
                    self.client = gspread.authorize(self.credentials)
                    self._log("gspread autorizado com sucesso")
                except Exception as e:
                    error_str = str(e)
                    self._log(f"Erro ao autorizar gspread: {error_str}", "ERROR")
                    self._connection_error = f"Erro ao autorizar cliente: {error_str}"
                    continue

                # spreadsheet_id
                self._log("Obtendo spreadsheet_id")
                spreadsheet_id = None

                try:
                    if "google_credentials" in st.secrets and st.secrets["google_credentials"].get("spreadsheet_id"):
                        spreadsheet_id = st.secrets["google_credentials"].get("spreadsheet_id")
                        self._log("spreadsheet_id encontrado em st.secrets['google_credentials']")
                    elif "spreadsheet_id" in st.secrets and st.secrets.get("spreadsheet_id"):
                        spreadsheet_id = st.secrets.get("spreadsheet_id")
                        self._log("spreadsheet_id encontrado em st.secrets (top-level)")
                except Exception as e:
                    self._log(f"Erro lendo spreadsheet_id do secrets: {e}", "WARNING")

                if not spreadsheet_id:
                    spreadsheet_id = os.getenv("SPREADSHEET_ID")
                    if spreadsheet_id:
                        self._log("spreadsheet_id encontrado em env SPREADSHEET_ID")

                if not spreadsheet_id:
                    self._log("spreadsheet_id não encontrado", "ERROR")
                    self._connection_error = (
                        "ID da planilha não configurado. Configure 'spreadsheet_id' no secrets.toml "
                        "ou a env SPREADSHEET_ID."
                    )
                    return False

                ok_id, msg_id = self._validate_spreadsheet_id(spreadsheet_id)
                if not ok_id:
                    self._log(f"spreadsheet_id inválido: {msg_id}", "ERROR")
                    self._connection_error = f"spreadsheet_id inválido: {msg_id}"
                    return False

                # open sheet
                self._log("Abrindo planilha por key")
                try:
                    self.spreadsheet = self.client.open_by_key(spreadsheet_id)
                    self._log(f"Planilha aberta: {self.spreadsheet.title}")
                except gspread.exceptions.SpreadsheetNotFound:
                    self._log("Planilha não encontrada", "ERROR")
                    self._connection_error = (
                        "Planilha não encontrada. Verifique o ID e compartilhe com a Service Account (client_email)."
                    )
                    return False
                except gspread.exceptions.APIError as e:
                    details = str(e)
                    self._log(f"Erro API Google: {details}", "ERROR")
                    if "PERMISSION_DENIED" in details or "403" in details:
                        self._connection_error = (
                            "Permissão negada. Compartilhe a planilha com a Service Account (client_email) como Editor."
                        )
                        return False
                    self._connection_error = f"Erro da API do Google Sheets: {details}"
                    continue
                except Exception as e:
                    self._log(f"Erro ao abrir planilha: {e}", "ERROR")
                    self._connection_error = f"Erro ao abrir planilha: {str(e)}"
                    continue

                # worksheets check
                self._log("Listando abas")
                try:
                    worksheets = self.spreadsheet.worksheets()
                    names = [ws.title for ws in worksheets]
                    self._log(f"{len(worksheets)} abas: {', '.join(names)}")
                except Exception as e:
                    self._log(f"Erro ao listar abas: {e}", "ERROR")
                    self._connection_error = f"Erro ao acessar abas: {str(e)}"
                    continue

                self._initialized = True
                self._connection_error = None
                self._log(f"Conexão estabelecida! Fonte: {creds_source}")

                if show_messages:
                    st.success(
                        f"✅ Conectado ao Google Sheets\n\n"
                        f"Planilha: {self.spreadsheet.title}\n"
                        f"{len(worksheets)} abas disponíveis"
                    )

                return True

            except Exception as e:
                self._log(f"Erro inesperado na tentativa {attempt}: {e}", "ERROR")
                self._connection_error = f"Erro inesperado: {str(e)}"

                if attempt < self.MAX_RETRIES:
                    delay = self.RETRY_DELAY * (2 ** (attempt - 1))
                    self._log(f"Aguardando {delay}s para retry...")
                    time.sleep(delay)

        if show_messages:
            st.error(f"❌ Erro ao conectar ao Google Sheets\n\n{self._connection_error}")

        return False

    def get_connection_status(self) -> dict:
        """
        Retorna o status da conexão com Google Sheets com informações detalhadas.
        NÃO tenta inicializar automaticamente - use initialize() para isso.
        """
        logs = self._initialization_logs if isinstance(self._initialization_logs, list) else []

        if self._initialized and self.client and self.spreadsheet:
            return {
                "connected": True,
                "source": "Google Sheets",
                "spreadsheet_title": self.spreadsheet.title if self.spreadsheet else None,
                "error": None,
                "last_attempt": self._last_attempt_time,
                "logs": logs,
                "suggestion": None,
            }

        if not self._initialization_attempted:
            error_str = 'Credenciais não verificadas (clique em "Testar Conexão" para verificar)'
        else:
            error_str = str(self._connection_error) if self._connection_error else "Credenciais não configuradas"

        suggestion = None
        if error_str:
            low = error_str.lower()
            if "não configurad" in low or "not configured" in low:
                suggestion = "Configure as credenciais em secrets.toml ou google_credentials.json"
            elif "inválid" in low or "invalid" in low:
                suggestion = "Verifique o formato das credenciais (secrets.toml.example)"
            elif "permiss" in low or "permission_denied" in low or "403" in low:
                suggestion = "Compartilhe a planilha com a Service Account (client_email) com permissão de Editor"
            elif "não encontrada" in low or "not found" in low:
                suggestion = "Verifique se o spreadsheet_id está correto e se a planilha existe"

        return {
            "connected": False,
            "source": "Não conectado",
            "spreadsheet_title": None,
            "error": error_str,
            "last_attempt": self._last_attempt_time,
            "logs": logs,
            "suggestion": suggestion,
        }

    def get_initialization_logs(self) -> list:
        return self._initialization_logs.copy() if isinstance(self._initialization_logs, list) else []

    def test_connection_live(self) -> dict:
        try:
            if not self.client or not self.spreadsheet:
                if not self.initialize():
                    return {"success": False, "message": self._connection_error or "Não foi possível conectar", "worksheets": None}

            worksheets = self.spreadsheet.worksheets()
            names = [ws.title for ws in worksheets]

            return {"success": True, "message": f"Conectado! {len(worksheets)} abas encontradas", "worksheets": names}
        except Exception as e:
            return {"success": False, "message": f"Erro: {str(e)}", "worksheets": None}

    def get_worksheet(self, sheet_name: str):
        """Obtém worksheet pelo nome. Retorna None se não existir."""
        try:
            if self.spreadsheet:
                return self.spreadsheet.worksheet(sheet_name)
        except Exception:
            return None
        return None

    def test_connection(self) -> bool:
        try:
            if self.client and self.spreadsheet:
                worksheets = self.spreadsheet.worksheets()
                return len(worksheets) > 0
        except Exception:
            pass
        return False


google_cloud_manager = GoogleCloudManager()
