# core/data_loader.py
from __future__ import annotations
from typing import Dict, Any, Optional
import pandas as pd
import streamlit as st
from datetime import datetime
import os

# Tentar importar do sheets_repo
try:
    from core.sheets_repo import read_sheet_df, SHEETS
    HAS_SHEETS = True
except ImportError:
    HAS_SHEETS = False
    print("Aviso: sheets_repo não encontrado. Usando dados mockados.")
    SHEETS = {
        "transactions": "transactions",
        "shows": "shows",
        "members": "members",
    }

class DataLoader:
    """Gerenciador de carregamento de dados financeiros"""
    
    def __init__(self):
        self.cache_key = "financial_data"
        self.last_update_key = "last_update"
    
    def load_all_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Carrega todos os dados necessários"""
        
        # Verificar cache
        if not force_refresh and self.cache_key in st.session_state:
            return st.session_state[self.cache_key]
        
        # Carregar dados
        data = {
            "transactions": self._load_transactions(),
            "shows": self._load_shows(),
            "members": self._load_members(),
            "status": "success",
            "last_update": datetime.now()
        }
        
        # Verificar se houve erro
        if not data["transactions"].get("success", False):
            data["status"] = "error"
            data["error_message"] = "Falha ao carregar transações"
        
        # Salvar no cache
        st.session_state[self.cache_key] = data
        st.session_state[self.last_update_key] = datetime.now()
        
        return data
    
    def _load_transactions(self) -> Dict[str, Any]:
        """Carrega dados de transações"""
        if HAS_SHEETS:
            try:
                result = read_sheet_df("transactions")
                if result.get("success"):
                    return result
            except Exception as e:
                print(f"Erro ao carregar transactions: {e}")
        
        # Dados mockados para fallback
        return {
            "success": True,
            "df": pd.DataFrame({
                'data': pd.date_range(start='2026-01-01', periods=10, freq='D'),
                'descricao': ['Salário', 'Aluguel', 'Supermercado', 'Internet', 'Show', 
                             'Restaurante', 'Transporte', 'Educação', 'Saúde', 'Lazer'],
                'categoria': ['Receita', 'Despesa', 'Despesa', 'Despesa', 'Receita',
                            'Despesa', 'Despesa', 'Despesa', 'Despesa', 'Despesa'],
                'valor': [5000, -1200, -350, -100, 3000, -80, -50, -200, -150, -100]
            }),
            "error": None
        }
    
    def _load_shows(self) -> Dict[str, Any]:
        """Carrega dados de shows"""
        if HAS_SHEETS:
            try:
                result = read_sheet_df("shows")
                if result.get("success"):
                    return result
            except Exception:
                pass
        
        # Dados mockados
        return {
            "success": True,
            "df": pd.DataFrame({
                'data': ['2026-01-15', '2026-01-20', '2026-01-25'],
                'show': ['Show A', 'Show B', 'Show C'],
                'local': ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte'],
                'receita': [3000, 2500, 4000],
                'despesas': [800, 600, 1000]
            }),
            "error": None
        }
    
    def _load_members(self) -> Dict[str, Any]:
        """Carrega dados de membros"""
        if HAS_SHEETS:
            try:
                result = read_sheet_df("members")
                if result.get("success"):
                    return result
            except Exception:
                pass
        
        # Dados mockados
        return {
            "success": True,
            "df": pd.DataFrame({
                'nome': ['João', 'Maria', 'Pedro', 'Ana'],
                'funcao': ['Vocal', 'Guitarra', 'Bateria', 'Baixo'],
                'percentual': [30, 25, 25, 20]
            }),
            "error": None
        }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Retorna status da conexão"""
        if HAS_SHEETS:
            try:
                from core.sheets_repo import _ensure_connected
                error = _ensure_connected()
                if error is None:
                    return {
                        "connected": True,
                        "source": "Google Sheets",
                        "sheet_name": "financas_rb",
                        "error": None
                    }
                else:
                    return {
                        "connected": False,
                        "source": "Google Sheets",
                        "sheet_name": "financas_rb",
                        "error": error
                    }
            except Exception as e:
                return {
                    "connected": False,
                    "source": "Google Sheets",
                    "error": str(e)
                }
        else:
            return {
                "connected": False,
                "source": "Modo mockado",
                "error": "sheets_repo não disponível"
            }

# Instância global
data_loader = DataLoader()

# Funções de conveniência
def load_financial_data(force_refresh: bool = False) -> Dict[str, Any]:
    """Carrega dados financeiros"""
    return data_loader.load_all_data(force_refresh=force_refresh)

def get_sheet_df(sheet_key: str, data: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """Obtém DataFrame específico"""
    if data is None:
        data = load_financial_data()
    
    sheet_data = data.get(sheet_key, {})
    if isinstance(sheet_data, dict):
        return sheet_data.get("df", pd.DataFrame())
    return pd.DataFrame()