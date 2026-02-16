"""
Carregamento de dados com fallback para Excel
Implementa prioridade: Google Sheets > Excel local
"""

import pandas as pd
import streamlit as st
from pathlib import Path
import os
from typing import Dict, Optional
from datetime import datetime
from core.google_sheets import get_all_data, read_sheet
from core.google_cloud import google_cloud_manager
import warnings
import logging
warnings.filterwarnings('ignore')

class DataLoader:
    """
    Carregador de dados com múltiplas fontes e cache
    """
    
    def __init__(self):
        self.excel_path = Path("data/Financas_RB.xlsx")
        self.use_excel_fallback = False
        self.last_load_time = None
        self._load_data_config()
    
    def _load_data_config(self):
        """
        Carrega configuração de fonte de dados de st.secrets
        
        IMPORTANTE: Se data_config não estiver presente em secrets.toml,
        o sistema usa valores padrão seguros (strict mode):
        - primary_source = "google"
        - allow_fallback = False
        
        Isso garante que erros de infraestrutura sejam visíveis em produção.
        Para desenvolvimento, configure explicitamente allow_fallback = true.
        """
        try:
            if "data_config" in st.secrets:
                self.primary_source = st.secrets["data_config"].get("primary_source", "google")
                self.allow_fallback = st.secrets["data_config"].get("allow_fallback", False)
                logging.info(f"[DATA_LOADER] Configuração carregada: primary_source={self.primary_source}, allow_fallback={self.allow_fallback}")
            else:
                # Valores padrão se não houver configuração
                self.primary_source = "google"
                self.allow_fallback = False
                logging.info(
                    "[DATA_LOADER] Usando configuração padrão (strict mode): "
                    "primary_source=google, allow_fallback=false. "
                    "Configure [data_config] em secrets.toml para alterar."
                )
        except Exception as e:
            # Em caso de erro, usar valores padrão seguros
            logging.warning(f"Erro ao carregar data_config de secrets: {e}")
            self.primary_source = "google"
            self.allow_fallback = False
        
    def load_all_data(self, force_refresh: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Carrega todos os dados do sistema
        
        Args:
            force_refresh: Forçar recarregamento ignorando cache
            
        Returns:
            Dicionário com todos os DataFrames
        """
        # Verificar se precisa atualizar cache
        needs_refresh = force_refresh or self._should_refresh_cache()
        
        if not needs_refresh and hasattr(st.session_state, 'all_data'):
            return st.session_state.all_data
        
        # Determinar fonte de dados baseado na configuração
        if self.primary_source == "excel":
            # Excel como fonte primária - carregar diretamente
            logging.info("[DATA_LOADER] Fonte primária configurada: Excel local")
            data = self._load_from_excel()
            self.use_excel_fallback = False
            data_source = "Excel local"
            
        elif self.primary_source == "google":
            # Google Sheets como fonte primária
            logging.info("[DATA_LOADER] Fonte primária configurada: Google Sheets")
            
            # Verificar se Google Cloud está inicializado
            connection_status = google_cloud_manager.get_connection_status()
            
            if not connection_status['connected']:
                # Google não está conectado
                error_msg = connection_status.get('error', 'Credenciais não configuradas')
                logging.error(f"[DATA_LOADER] Google Sheets não conectado: {error_msg}")
                
                if self.allow_fallback:
                    # Fallback permitido - usar Excel com warning
                    logging.warning("[DATA_LOADER] ⚠️ Executando fallback para Excel local (allow_fallback=true)")
                    st.warning(
                        f"⚠️ **Operando em modo fallback**\n\n"
                        f"**Causa:** Falha ao conectar com Google Sheets\n\n"
                        f"**Detalhes:** {error_msg}\n\n"
                        f"**Ação:** Usando Excel local como fonte de dados alternativa"
                    )
                    data = self._load_from_excel()
                    self.use_excel_fallback = True
                    data_source = "Excel local (fallback)"
                else:
                    # Fallback não permitido - falhar explicitamente
                    logging.error("[DATA_LOADER] ❌ Falha crítica: Google Sheets não disponível e fallback desabilitado")
                    error_message = (
                        f"❌ **Falha na autenticação com Google Sheets**\n\n"
                        f"**Configuração:** `primary_source = \"google\"` e `allow_fallback = false`\n\n"
                        f"**Problema:** {error_msg}\n\n"
                        f"**Solução:**\n"
                        f"1. Configure as credenciais do Google Cloud em `.streamlit/secrets.toml`\n"
                        f"2. Ou altere `allow_fallback = true` para permitir uso do Excel local\n"
                        f"3. Ou altere `primary_source = \"excel\"` para usar Excel como fonte primária\n\n"
                        f"📚 Consulte: `.streamlit/README.md` e `docs/SETUP_GOOGLE_SHEETS.md`"
                    )
                    st.error(error_message)
                    raise RuntimeError(f"Google Sheets não disponível: {error_msg}")
            
            else:
                # Google está conectado - tentar carregar dados
                try:
                    logging.info("[DATA_LOADER] Carregando dados do Google Sheets...")
                    data = get_all_data()
                    
                    # Validar se os dados foram carregados corretamente
                    if self._validate_data(data):
                        self.use_excel_fallback = False
                        data_source = "Google Sheets"
                        logging.info("[DATA_LOADER] ✅ Dados carregados com sucesso do Google Sheets")
                    else:
                        # Dados incompletos do Google
                        logging.warning("[DATA_LOADER] ⚠️ Google Sheets conectado mas dados incompletos/inválidos")
                        
                        if self.allow_fallback:
                            # Fallback para Excel
                            logging.warning("[DATA_LOADER] Executando fallback para Excel devido a dados incompletos")
                            st.warning(
                                "⚠️ **Google Sheets conectado mas dados incompletos**\n\n"
                                "Usando Excel local como fonte alternativa."
                            )
                            data = self._load_from_excel()
                            self.use_excel_fallback = True
                            data_source = "Excel local (fallback)"
                        else:
                            # Sem fallback - reportar erro
                            logging.error("[DATA_LOADER] Dados incompletos e fallback desabilitado")
                            st.error(
                                "❌ **Google Sheets conectado mas dados inválidos**\n\n"
                                "Verifique se todas as abas necessárias existem e contêm dados."
                            )
                            raise RuntimeError("Dados inválidos no Google Sheets e fallback desabilitado")
                
                except Exception as e:
                    # Erro ao carregar do Google
                    logging.error(f"[DATA_LOADER] Erro ao carregar dados do Google Sheets: {e}")
                    
                    if self.allow_fallback:
                        logging.warning("[DATA_LOADER] Executando fallback para Excel devido a erro")
                        st.warning(
                            f"⚠️ **Erro ao carregar do Google Sheets**\n\n"
                            f"Usando Excel local como fonte alternativa.\n\n"
                            f"Erro: {str(e)}"
                        )
                        data = self._load_from_excel()
                        self.use_excel_fallback = True
                        data_source = "Excel local (fallback)"
                    else:
                        logging.error("[DATA_LOADER] Erro ao carregar e fallback desabilitado")
                        st.error(f"❌ **Erro ao carregar dados do Google Sheets**\n\n{str(e)}")
                        raise
        else:
            # Fonte desconhecida
            logging.error(f"[DATA_LOADER] Fonte primária desconhecida: {self.primary_source}")
            st.error(f"Fonte de dados desconhecida: {self.primary_source}")
            return {}
        
        # Processar dados
        data = self._process_data(data)
        
        # Armazenar em cache
        st.session_state.all_data = data
        st.session_state.data_source = data_source
        st.session_state.last_cache_update = datetime.now()
        self.last_load_time = datetime.now()
        
        # Exibir fonte na sidebar
        if self.use_excel_fallback:
            st.sidebar.warning(f"⚠️ Fonte: {data_source}")
        else:
            st.sidebar.info(f"📊 Fonte: {data_source}")
        
        return data
    
    def _load_from_excel(self) -> Dict[str, pd.DataFrame]:
        """
        Carrega dados do arquivo Excel local
        
        Returns:
            Dicionário com DataFrames
        """
        data = {}
        
        if self.excel_path.exists():
            try:
                # Carregar cada aba
                sheet_mapping = {
                    'shows': 'shows',
                    'transactions': 'transactions',
                    'payout_rules': 'payout_rules',
                    'show_payout_config': 'show_payout_config',
                    'members': 'members',
                    'member_shares': 'member_shares'
                }
                
                for key, sheet_name in sheet_mapping.items():
                    try:
                        df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
                        data[key] = df
                    except:
                        data[key] = pd.DataFrame()
                
            except Exception as e:
                st.error(f"Erro ao ler Excel: {str(e)}")
        
        return data
    
    def _validate_data(self, data: Dict[str, pd.DataFrame]) -> bool:
        """
        Valida se os dados estão completos e válidos
        
        Args:
            data: Dicionário com DataFrames
            
        Returns:
            True se dados válidos
        """
        required_sheets = ['shows', 'transactions']
        
        for sheet in required_sheets:
            if sheet not in data or data[sheet].empty:
                return False
        
        return True
    
    def _process_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Processa e limpa os dados carregados
        
        Args:
            data: Dicionário com DataFrames brutos
            
        Returns:
            Dicionário com DataFrames processados
        """
        processed = {}
        
        for key, df in data.items():
            if df.empty:
                processed[key] = df
                continue
            
            df_processed = df.copy()
            
            # Processamento específico por tipo de dado
            if key == 'shows':
                df_processed = self._process_shows(df_processed)
            elif key == 'transactions':
                df_processed = self._process_transactions(df_processed)
            elif key == 'payout_rules':
                df_processed = self._process_payout_rules(df_processed)
            
            processed[key] = df_processed
        
        return processed
    
    def _process_shows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processa dados de shows
        
        Args:
            df: DataFrame de shows
            
        Returns:
            DataFrame processado
        """
        df = df.copy()
        
        # Converter datas
        if 'data_show' in df.columns:
            df['data_show'] = pd.to_datetime(df['data_show'], errors='coerce')
        
        # Garantir tipos numéricos
        numeric_cols = ['publico', 'cache_acordado']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remover duplicatas
        if 'show_id' in df.columns:
            df = df.drop_duplicates(subset=['show_id'], keep='last')
        
        return df
    
    def _process_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processa dados de transações
        
        Args:
            df: DataFrame de transações
            
        Returns:
            DataFrame processado
        """
        df = df.copy()
        
        # Converter datas
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
        
        # Garantir tipos numéricos
        if 'valor' in df.columns:
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        
        # Filtrar transações estornadas
        if 'payment_status' in df.columns:
            df = df[df['payment_status'] != 'ESTORNADO']
        
        # Remover duplicatas
        if 'id' in df.columns:
            df = df.drop_duplicates(subset=['id'], keep='last')
        
        return df
    
    def _process_payout_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processa regras de rateio
        
        Args:
            df: DataFrame de regras
            
        Returns:
            DataFrame processado
        """
        df = df.copy()
        
        # Converter datas
        date_cols = ['vigencia_inicio', 'vigencia_fim']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Garantir tipos numéricos
        numeric_cols = ['pct_caixa', 'pct_musicos']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce') / 100
        
        return df
    
    def _should_refresh_cache(self) -> bool:
        """
        Determina se o cache precisa ser atualizado
        
        Returns:
            True se cache expirado
        """
        if not hasattr(st.session_state, 'last_cache_update'):
            return True
        
        last_update = st.session_state.last_cache_update
        if not last_update:
            return True
        
        # Verificar se passaram mais de 5 minutos
        cache_ttl = 300  # 5 minutos em segundos
        time_diff = (datetime.now() - last_update).total_seconds()
        
        return time_diff > cache_ttl
    
    def save_to_excel(self, data: Dict[str, pd.DataFrame]):
        """
        Salva dados no Excel local (backup)
        
        Args:
            data: Dicionário com DataFrames
        """
        try:
            with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                for key, df in data.items():
                    if not df.empty:
                        df.to_excel(writer, sheet_name=key, index=False)
            
            st.success("Backup salvo no Excel local")
        except Exception as e:
            st.error(f"Erro ao salvar Excel: {str(e)}")

# Instância global do carregador
data_loader = DataLoader()