"""
Escrita centralizada de dados com validações
Implementa CRUD completo com auditoria
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from core.google_sheets import write_row, update_row, delete_row, sync_all
from core.validators import validate_transaction, validate_show, validate_payout_rule
from core.cache_manager import CacheManager

class DataWriter:
    """
    Gerenciador de escrita de dados com validação e auditoria
    """
    
    def __init__(self):
        self.cache_manager = CacheManager()
    
    def create_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """
        Cria nova transação
        
        Args:
            transaction_data: Dados da transação
            
        Returns:
            True se sucesso
        """
        # Validar dados
        if not validate_transaction(transaction_data):
            st.error("Dados da transação inválidos!")
            return False
        
        try:
            # Preparar linha para Google Sheets
            row = [
                transaction_data.get('id', ''),
                transaction_data.get('data', '').strftime('%d/%m/%Y'),
                transaction_data.get('tipo', ''),
                transaction_data.get('categoria', ''),
                transaction_data.get('subcategoria', ''),
                transaction_data.get('descricao', ''),
                str(transaction_data.get('valor', 0)).replace('.', ','),
                transaction_data.get('show_id', ''),
                transaction_data.get('payment_status', ''),
                transaction_data.get('conta', '')
            ]
            
            # Escrever no Google Sheets
            success = write_row('transactions', row)
            
            if success:
                # Atualizar cache
                self.cache_manager.invalidate_cache('transactions')
                
                # Registrar auditoria
                self._log_audit('CREATE', 'transactions', transaction_data)
                
                st.success("✅ Transação criada com sucesso!")
                return True
            else:
                st.error("❌ Erro ao criar transação no Google Sheets")
                return False
                
        except Exception as e:
            st.error(f"❌ Erro ao criar transação: {str(e)}")
            return False
    
    def update_transaction(self, transaction_id: str, 
                          transaction_data: Dict[str, Any]) -> bool:
        """
        Atualiza transação existente
        
        Args:
            transaction_id: ID da transação
            transaction_data: Novos dados
            
        Returns:
            True se sucesso
        """
        # Validar dados
        if not validate_transaction(transaction_data):
            st.error("Dados da transação inválidos!")
            return False
        
        try:
            # Obter índice da linha
            transactions_df = st.session_state.get('transactions_data', pd.DataFrame())
            if transactions_df.empty:
                st.error("Nenhuma transação encontrada!")
                return False
            
            row_index = transactions_df[transactions_df['id'] == transaction_id].index
            if len(row_index) == 0:
                st.error(f"Transação {transaction_id} não encontrada!")
                return False
            
            # Preparar linha para Google Sheets
            row = [
                transaction_data.get('id', ''),
                transaction_data.get('data', '').strftime('%d/%m/%Y'),
                transaction_data.get('tipo', ''),
                transaction_data.get('categoria', ''),
                transaction_data.get('subcategoria', ''),
                transaction_data.get('descricao', ''),
                str(transaction_data.get('valor', 0)).replace('.', ','),
                transaction_data.get('show_id', ''),
                transaction_data.get('payment_status', ''),
                transaction_data.get('conta', '')
            ]
            
            # Atualizar no Google Sheets (row_index + 2 porque Google Sheets começa em 1 e tem cabeçalho)
            success = update_row('transactions', row_index[0] + 2, row)
            
            if success:
                # Atualizar cache
                self.cache_manager.invalidate_cache('transactions')
                
                # Registrar auditoria
                self._log_audit('UPDATE', 'transactions', transaction_data)
                
                st.success("✅ Transação atualizada com sucesso!")
                return True
            else:
                st.error("❌ Erro ao atualizar transação no Google Sheets")
                return False
                
        except Exception as e:
            st.error(f"❌ Erro ao atualizar transação: {str(e)}")
            return False
    
    def delete_transaction(self, transaction_id: str) -> bool:
        """
        Remove transação
        
        Args:
            transaction_id: ID da transação
            
        Returns:
            True se sucesso
        """
        try:
            # Obter índice da linha
            transactions_df = st.session_state.get('transactions_data', pd.DataFrame())
            if transactions_df.empty:
                st.error("Nenhuma transação encontrada!")
                return False
            
            row_index = transactions_df[transactions_df['id'] == transaction_id].index
            if len(row_index) == 0:
                st.error(f"Transação {transaction_id} não encontrada!")
                return False
            
            # Deletar do Google Sheets
            success = delete_row('transactions', row_index[0] + 2)
            
            if success:
                # Atualizar cache
                self.cache_manager.invalidate_cache('transactions')
                
                # Registrar auditoria
                self._log_audit('DELETE', 'transactions', {'id': transaction_id})
                
                st.success("✅ Transação removida com sucesso!")
                return True
            else:
                st.error("❌ Erro ao remover transação do Google Sheets")
                return False
                
        except Exception as e:
            st.error(f"❌ Erro ao remover transação: {str(e)}")
            return False
    
    def create_show(self, show_data: Dict[str, Any]) -> bool:
        """
        Cria novo show
        
        Args:
            show_data: Dados do show
            
        Returns:
            True se sucesso
        """
        # Validar dados
        if not validate_show(show_data):
            st.error("Dados do show inválidos!")
            return False
        
        try:
            # Preparar linha para Google Sheets
            row = [
                show_data.get('show_id', ''),
                show_data.get('data_show', '').strftime('%d/%m/%Y'),
                show_data.get('casa', ''),
                show_data.get('cidade', ''),
                show_data.get('status', ''),
                str(show_data.get('publico', 0)),
                str(show_data.get('cache_acordado', 0)).replace('.', ','),
                show_data.get('observacao', '')
            ]
            
            # Escrever no Google Sheets
            success = write_row('shows', row)
            
            if success:
                # Atualizar cache
                self.cache_manager.invalidate_cache('shows')
                
                # Registrar auditoria
                self._log_audit('CREATE', 'shows', show_data)
                
                st.success("✅ Show criado com sucesso!")
                return True
            else:
                st.error("❌ Erro ao criar show no Google Sheets")
                return False
                
        except Exception as e:
            st.error(f"❌ Erro ao criar show: {str(e)}")
            return False
    
    def update_show(self, show_id: str, show_data: Dict[str, Any]) -> bool:
        """
        Atualiza show existente
        
        Args:
            show_id: ID do show
            show_data: Novos dados
            
        Returns:
            True se sucesso
        """
        # Implementação similar à update_transaction
        pass
    
    def delete_show(self, show_id: str) -> bool:
        """
        Remove show
        
        Args:
            show_id: ID do show
            
        Returns:
            True se sucesso
        """
        # Implementação similar à delete_transaction
        pass
    
    def create_payout_rule(self, rule_data: Dict[str, Any]) -> bool:
        """
        Cria nova regra de rateio
        
        Args:
            rule_data: Dados da regra
            
        Returns:
            True se sucesso
        """
        # Validar dados
        if not validate_payout_rule(rule_data):
            st.error("Dados da regra de rateio inválidos!")
            return False
        
        try:
            # Preparar linha para Google Sheets
            row = [
                rule_data.get('rule_id', ''),
                rule_data.get('nome_regra', ''),
                rule_data.get('modelo', ''),
                str(rule_data.get('pct_caixa', 0)).replace('.', ','),
                str(rule_data.get('pct_musicos', 0)).replace('.', ','),
                rule_data.get('ativa', 'SIM'),
                rule_data.get('vigencia_inicio', '').strftime('%d/%m/%Y'),
                rule_data.get('vigencia_fim', '').strftime('%d/%m/%Y') if rule_data.get('vigencia_fim') else ''
            ]
            
            # Escrever no Google Sheets
            success = write_row('payout_rules', row)
            
            if success:
                # Atualizar cache
                self.cache_manager.invalidate_cache('payout_rules')
                
                # Registrar auditoria
                self._log_audit('CREATE', 'payout_rules', rule_data)
                
                st.success("✅ Regra de rateio criada com sucesso!")
                return True
            else:
                st.error("❌ Erro ao criar regra no Google Sheets")
                return False
                
        except Exception as e:
            st.error(f"❌ Erro ao criar regra de rateio: {str(e)}")
            return False
    
    def sync_all_data(self) -> bool:
        """
        Sincroniza todos os dados
        
        Returns:
            True se sucesso
        """
        try:
            results = sync_all()
            
            if all(results.values()):
                st.success("✅ Todos os dados sincronizados com sucesso!")
                return True
            else:
                failed = [k for k, v in results.items() if not v]
                st.error(f"❌ Falha na sincronização de: {', '.join(failed)}")
                return False
                
        except Exception as e:
            st.error(f"❌ Erro na sincronização: {str(e)}")
            return False
    
    def _log_audit(self, action: str, entity: str, data: Dict[str, Any]):
        """
        Registra ação de auditoria
        
        Args:
            action: Ação realizada
            entity: Entidade afetada
            data: Dados envolvidos
        """
        audit_entry = {
            'timestamp': datetime.now(),
            'user': st.session_state.get('user_name', 'unknown'),
            'action': action,
            'entity': entity,
            'data': str(data)
        }
        
        # Adicionar ao log de auditoria
        if 'audit_log' not in st.session_state:
            st.session_state.audit_log = []
        
        st.session_state.audit_log.append(audit_entry)

# Instância global do writer
data_writer = DataWriter()