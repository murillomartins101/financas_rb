"""
Sistema de filtros globais e específicos
Implementa filtros por período, categoria, status, etc.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from core.constants import TransactionType, PaymentStatus, ShowStatus

class DataFilter:
    """
    Gerenciador de filtros de dados
    """
    
    @staticmethod
    def apply_global_filters(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Aplica filtros globais a todos os dados
        
        Args:
            data: Dicionário com DataFrames originais
            
        Returns:
            Dicionário com DataFrames filtrados
        """
        filtered_data = {}
        
        for key, df in data.items():
            if df.empty:
                filtered_data[key] = df
                continue
            
            df_filtered = df.copy()
            
            # Aplicar filtro de período baseado no session state
            start_date = st.session_state.get('filter_start_date')
            end_date = st.session_state.get('filter_end_date')
            
            if start_date and end_date:
                df_filtered = DataFilter._filter_by_date(df_filtered, start_date, end_date, key)
            
            filtered_data[key] = df_filtered
        
        return filtered_data
    
    @staticmethod
    def _filter_by_date(df: pd.DataFrame, start_date: datetime, 
                       end_date: datetime, data_type: str) -> pd.DataFrame:
        """
        Filtra DataFrame por data baseado no tipo de dados
        
        Args:
            df: DataFrame a ser filtrado
            start_date: Data inicial
            end_date: Data final
            data_type: Tipo de dados (shows, transactions, etc.)
            
        Returns:
            DataFrame filtrado
        """
        if df.empty:
            return df
        
        df_copy = df.copy()
        
        # Determinar coluna de data baseada no tipo
        date_column = None
        if data_type == 'shows':
            date_column = 'data_show'
        elif data_type == 'transactions':
            date_column = 'data'
        elif data_type == 'payout_rules':
            # Para regras de rateio, usar vigência
            pass
        
        if date_column and date_column in df_copy.columns:
            # Converter para datetime se necessário
            if not pd.api.types.is_datetime64_any_dtype(df_copy[date_column]):
                df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors='coerce')
            
            # Aplicar filtro
            mask = (df_copy[date_column] >= start_date) & (df_copy[date_column] <= end_date)
            df_copy = df_copy[mask].copy()
        
        return df_copy
    
    @staticmethod
    def filter_transactions(df: pd.DataFrame, 
                          transaction_type: Optional[str] = None,
                          payment_status: Optional[str] = None,
                          category: Optional[str] = None,
                          min_value: Optional[float] = None,
                          max_value: Optional[float] = None) -> pd.DataFrame:
        """
        Filtra transações com múltiplos critérios
        
        Args:
            df: DataFrame de transações
            transaction_type: Tipo de transação (ENTRADA/SAIDA)
            payment_status: Status de pagamento
            category: Categoria da transação
            min_value: Valor mínimo
            max_value: Valor máximo
            
        Returns:
            DataFrame filtrado
        """
        if df.empty:
            return df
        
        df_filtered = df.copy()
        
        # Aplicar filtros sequencialmente
        if transaction_type and 'tipo' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['tipo'] == transaction_type]
        
        if payment_status and 'payment_status' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['payment_status'] == payment_status]
        
        if category and 'categoria' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['categoria'] == category]
        
        if min_value is not None and 'valor' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['valor'] >= min_value]
        
        if max_value is not None and 'valor' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['valor'] <= max_value]
        
        return df_filtered
    
    @staticmethod
    def filter_shows(df: pd.DataFrame,
                    status: Optional[str] = None,
                    min_public: Optional[int] = None,
                    max_public: Optional[int] = None,
                    city: Optional[str] = None) -> pd.DataFrame:
        """
        Filtra shows com múltiplos critérios
        
        Args:
            df: DataFrame de shows
            status: Status do show
            min_public: Público mínimo
            max_public: Público máximo
            city: Cidade
            
        Returns:
            DataFrame filtrado
        """
        if df.empty:
            return df
        
        df_filtered = df.copy()
        
        if status and 'status' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['status'] == status]
        
        if min_public is not None and 'publico' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['publico'] >= min_public]
        
        if max_public is not None and 'publico' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['publico'] <= max_public]
        
        if city and 'cidade' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['cidade'] == city]
        
        return df_filtered
    
    @staticmethod
    def get_filter_widgets():
        """
        Cria widgets de filtro na sidebar
        
        Returns:
            Dicionário com valores dos filtros
        """
        filters = {}
        
        with st.sidebar.expander("🔍 Filtros Avançados", expanded=False):
            # Filtro por tipo de transação
            filters['transaction_type'] = st.selectbox(
                "Tipo de Transação",
                ["Todos", "ENTRADA", "SAIDA"],
                key="filter_transaction_type"
            )
            
            # Filtro por status de pagamento
            filters['payment_status'] = st.selectbox(
                "Status de Pagamento",
                ["Todos", "PAGO", "NÃO RECEBIDO", "ESTORNADO"],
                key="filter_payment_status"
            )
            
            # Filtro por categoria
            filters['category'] = st.selectbox(
                "Categoria",
                ["Todas", "CACHÊS-MÚSICOS", "PRODUÇÃO", "LOGÍSTICA", "MARKETING", 
                 "ALUGUEL", "EQUIPE TÉCNICA", "FOTOGRAFIA", "ENSAIOS", "OUTROS"],
                key="filter_category"
            )
            
            # Filtro por valor
            col1, col2 = st.columns(2)
            with col1:
                filters['min_value'] = st.number_input(
                    "Valor Mínimo (R$)",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    key="filter_min_value"
                )
            
            with col2:
                filters['max_value'] = st.number_input(
                    "Valor Máximo (R$)",
                    min_value=0.0,
                    value=10000.0,
                    step=100.0,
                    key="filter_max_value"
                )
            
            # Botão para aplicar filtros
            if st.button("Aplicar Filtros", key="apply_filters"):
                st.session_state.filters_applied = True
                st.rerun()
            
            # Botão para limpar filtros
            if st.button("Limpar Filtros", key="clear_filters"):
                st.session_state.filters_applied = False
                st.rerun()
        
        return filters

def get_current_filters() -> Dict[str, Any]:
    """
    Obtém filtros atuais do session state
    
    Returns:
        Dicionário com filtros atuais
    """
    filters = {
        'period': st.session_state.get('filter_period', 'Mês atual'),
        'start_date': st.session_state.get('filter_start_date'),
        'end_date': st.session_state.get('filter_end_date'),
        'transaction_type': st.session_state.get('filter_transaction_type', 'Todos'),
        'payment_status': st.session_state.get('filter_payment_status', 'Todos'),
        'category': st.session_state.get('filter_category', 'Todas'),
        'min_value': st.session_state.get('filter_min_value', 0.0),
        'max_value': st.session_state.get('filter_max_value', 10000.0),
        'applied': st.session_state.get('filters_applied', False)
    }
    
    return filters

def display_current_filters():
    """
    Exibe os filtros atualmente aplicados
    """
    filters = get_current_filters()
    
    if filters['applied']:
        st.info("📌 **Filtros Ativos:**")
        
        filter_texts = []
        
        if filters['period'] != 'Todo período':
            filter_texts.append(f"Período: {filters['period']}")
        
        if filters['transaction_type'] != 'Todos':
            filter_texts.append(f"Tipo: {filters['transaction_type']}")
        
        if filters['payment_status'] != 'Todos':
            filter_texts.append(f"Pagamento: {filters['payment_status']}")
        
        if filters['category'] != 'Todas':
            filter_texts.append(f"Categoria: {filters['category']}")
        
        if filters['min_value'] > 0:
            filter_texts.append(f"Valor mínimo: R$ {filters['min_value']:,.2f}")
        
        if filters['max_value'] < 10000:
            filter_texts.append(f"Valor máximo: R$ {filters['max_value']:,.2f}")
        
        if filter_texts:
            for text in filter_texts:
                st.caption(f"• {text}")
        else:
            st.caption("• Filtro padrão (período selecionado)")
    else:
        st.info("ℹ️ **Filtros:** Apenas filtro de período ativo")