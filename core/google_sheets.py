"""
Operações de leitura e escrita no Google Sheets
Implementa todas as funções obrigatórias da especificação
"""

import pandas as pd
import streamlit as st
from typing import List, Dict, Any, Optional, Union
import numpy as np
from datetime import datetime
from core.google_cloud import google_cloud_manager
from core.constants import SHEET_NAMES
import time

def read_sheet(sheet_name: str, worksheet_name: Optional[str] = None) -> pd.DataFrame:
    """
    Lê dados de uma aba do Google Sheets
    
    Args:
        sheet_name: Nome da planilha (chave no SHEET_NAMES)
        worksheet_name: Nome específico da aba (opcional)
        
    Returns:
        DataFrame com os dados
    """
    try:
        if not google_cloud_manager.client:
            if not google_cloud_manager.initialize():
                return pd.DataFrame()
        
        actual_sheet_name = SHEET_NAMES.get(sheet_name, sheet_name)
        worksheet = google_cloud_manager.get_worksheet(actual_sheet_name)
        
        if worksheet:
            # Obter todos os valores
            data = worksheet.get_all_values()
            
            if data:
                # Primeira linha como cabeçalho
                df = pd.DataFrame(data[1:], columns=data[0])
                
                # Converter tipos de dados
                for col in df.columns:
                    if col in ['valor', 'cache_acordado', 'publico', 'pct_caixa', 'pct_musicos']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    elif col in ['data', 'data_show', 'vigencia_inicio', 'vigencia_fim']:
                        df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
                
                return df
        
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Erro ao ler {sheet_name}: {str(e)}")
        return pd.DataFrame()

def write_row(sheet_name: str, row_data: List[Any], 
              worksheet_name: Optional[str] = None) -> bool:
    """
    Adiciona uma nova linha ao Google Sheets
    
    Args:
        sheet_name: Nome da planilha
        row_data: Lista com valores da linha
        worksheet_name: Nome da aba
        
    Returns:
        True se sucesso
    """
    try:
        if not google_cloud_manager.client:
            if not google_cloud_manager.initialize():
                return False
        
        actual_sheet_name = worksheet_name or SHEET_NAMES.get(sheet_name, sheet_name)
        worksheet = google_cloud_manager.get_worksheet(actual_sheet_name)
        
        if worksheet:
            # Adicionar nova linha
            worksheet.append_row(row_data)
            
            # Registrar no log
            log_audit("INSERT", sheet_name, row_data)
            
            return True
        
        return False
        
    except Exception as e:
        st.error(f"Erro ao escrever em {sheet_name}: {str(e)}")
        return False

def update_row(sheet_name: str, row_index: int, row_data: List[Any],
               worksheet_name: Optional[str] = None) -> bool:
    """
    Atualiza uma linha existente no Google Sheets
    
    Args:
        sheet_name: Nome da planilha
        row_index: Índice da linha (base 1)
        row_data: Novos valores da linha
        worksheet_name: Nome da aba
        
    Returns:
        True se sucesso
    """
    try:
        if not google_cloud_manager.client:
            if not google_cloud_manager.initialize():
                return False
        
        actual_sheet_name = worksheet_name or SHEET_NAMES.get(sheet_name, sheet_name)
        worksheet = google_cloud_manager.get_worksheet(actual_sheet_name)
        
        if worksheet:
            # Atualizar linha
            worksheet.update(f"A{row_index}:{chr(64+len(row_data))}{row_index}", [row_data])
            
            # Registrar no log
            log_audit("UPDATE", sheet_name, row_data, row_index)
            
            return True
        
        return False
        
    except Exception as e:
        st.error(f"Erro ao atualizar {sheet_name}: {str(e)}")
        return False

def delete_row(sheet_name: str, row_index: int,
               worksheet_name: Optional[str] = None) -> bool:
    """
    Remove uma linha do Google Sheets
    
    Args:
        sheet_name: Nome da planilha
        row_index: Índice da linha (base 1)
        worksheet_name: Nome da aba
        
    Returns:
        True se sucesso
    """
    try:
        if not google_cloud_manager.client:
            if not google_cloud_manager.initialize():
                return False
        
        actual_sheet_name = worksheet_name or SHEET_NAMES.get(sheet_name, sheet_name)
        worksheet = google_cloud_manager.get_worksheet(actual_sheet_name)
        
        if worksheet:
            # Registrar antes de deletar para auditoria
            row_data = worksheet.row_values(row_index)
            
            # Deletar linha
            worksheet.delete_rows(row_index)
            
            # Registrar no log
            log_audit("DELETE", sheet_name, row_data, row_index)
            
            return True
        
        return False
        
    except Exception as e:
        st.error(f"Erro ao deletar de {sheet_name}: {str(e)}")
        return False

def sync_all() -> Dict[str, bool]:
    """
    Sincroniza todos os dados com cache local
    
    Returns:
        Dicionário com status de sincronização por aba
    """
    results = {}
    
    for sheet_key in SHEET_NAMES.keys():
        try:
            df = read_sheet(sheet_key)
            if not df.empty:
                # Atualizar cache
                cache_key = f"{sheet_key}_data"
                st.session_state[cache_key] = df
                results[sheet_key] = True
            else:
                results[sheet_key] = False
        except:
            results[sheet_key] = False
    
    # Atualizar timestamp do cache
    st.session_state["last_cache_update"] = datetime.now()
    
    return results

def log_audit(action: str, sheet_name: str, data: List[Any], 
              row_index: Optional[int] = None):
    """
    Registra ação de auditoria
    
    Args:
        action: Ação realizada (INSERT, UPDATE, DELETE)
        sheet_name: Nome da planilha
        data: Dados envolvidos
        row_index: Índice da linha (se aplicável)
    """
    try:
        audit_data = {
            "timestamp": datetime.now().isoformat(),
            "user": st.session_state.get("user_name", "unknown"),
            "action": action,
            "sheet": sheet_name,
            "row_index": row_index,
            "data": str(data)
        }
        
        # Adicionar ao log de auditoria
        audit_log = st.session_state.get("audit_log", [])
        audit_log.append(audit_data)
        st.session_state.audit_log = audit_log
        
    except:
        pass

def get_all_data() -> Dict[str, pd.DataFrame]:
    """
    Obtém todos os dados das planilhas
    
    Returns:
        Dicionário com DataFrames de todas as abas
    """
    data = {}
    
    for sheet_key in SHEET_NAMES.keys():
        cache_key = f"{sheet_key}_data"
        
        # Verificar cache
        if cache_key in st.session_state:
            # Verificar se cache está expirado (5 minutos)
            last_update = st.session_state.get("last_cache_update")
            if last_update and (datetime.now() - last_update).seconds < 300:
                data[sheet_key] = st.session_state[cache_key]
                continue
        
        # Buscar do Google Sheets
        df = read_sheet(sheet_key)
        if not df.empty:
            st.session_state[cache_key] = df
            data[sheet_key] = df
    
    return data