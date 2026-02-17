import pandas as pd
import streamlit as st
from typing import List, Dict, Any, Optional, Union
import numpy as np
from datetime import datetime
from core.google_cloud import google_cloud_manager
# Removi a importação duplicada e mantive a definição local conforme seu exemplo
import time

def read_sheet(worksheet_name: str) -> pd.DataFrame:
    """
    Lê dados de uma aba do Google Sheets e converte tipos automaticamente.
    Utiliza a planilha já aberta pelo google_cloud_manager.
    """
    try:
        # Verificar se a planilha foi inicializada com sucesso
        if not google_cloud_manager.spreadsheet:
            if not google_cloud_manager.initialize():
                return pd.DataFrame()
        
        # Obter a aba (worksheet) da planilha já aberta
        worksheet = google_cloud_manager.get_worksheet(worksheet_name)
        
        if worksheet:
            # Obter registros (já mapeia cabeçalho para chaves de dicionário)
            data = worksheet.get_all_records()
            
            if not data:
                return pd.DataFrame()
                
            df = pd.DataFrame(data)
            
            # --- Ajuste de Tipos de Dados ---
            # Colunas Numéricas
            numeric_cols = ['valor', 'cache_acordado', 'publico', 'pct_caixa', 'pct_musicos', 'valor_total']
            for col in numeric_cols:
                if col in df.columns:
                    # Remove símbolos monetários e converte
                    df[col] = df[col].replace(r'[R\$\.\,]', '', regex=True).astype(float) / 100 if df[col].dtype == object else df[col]
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            # Colunas de Data
            date_cols = ['data', 'data_show', 'vigencia_inicio', 'vigencia_fim']
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
            
            return df
        
        return pd.DataFrame()
        
    except Exception as e:
        error_msg = str(e)
        
        # Melhorar mensagem de erro para problemas comuns de JWT
        if "invalid_grant" in error_msg.lower() or "invalid jwt signature" in error_msg.lower():
            st.error(
                f"❌ Erro de autenticação JWT ao ler a aba '{worksheet_name}'\n\n"
                "**Causa:** Assinatura JWT inválida\n\n"
                "**Soluções:**\n"
                "1. Verifique se a Service Account ainda existe no Google Cloud Console\n"
                "2. Gere uma nova chave JSON para a Service Account e atualize as credenciais\n"
                "3. Verifique se o relógio do sistema está correto\n"
                "4. Certifique-se de que a `private_key` no secrets.toml está completa e não corrompida\n\n"
                f"**Erro técnico:** {error_msg}"
            )
        else:
            st.error(f"Erro ao ler {sheet_name} ({worksheet_name}): {error_msg}")
        
        return pd.DataFrame()

def write_row(worksheet_name: str, row_data: List[Any]) -> bool:
    try:
        if not google_cloud_manager.spreadsheet:
            if not google_cloud_manager.initialize(): return False
        
        worksheet = google_cloud_manager.get_worksheet(worksheet_name)
        
        if worksheet:
            worksheet.append_row(row_data)
            log_audit("INSERT", f"{sheet_name}:{worksheet_name}", row_data)
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao escrever: {str(e)}")
        return False

def update_row(worksheet_name: str, row_index: int, row_data: List[Any]) -> bool:
    """ row_index deve ser base 1 (ex: linha 2 é a primeira após cabeçalho) """
    try:
        if not google_cloud_manager.spreadsheet:
            if not google_cloud_manager.initialize(): return False
        
        worksheet = google_cloud_manager.get_worksheet(worksheet_name)
        
        if worksheet:
            # gspread moderno usa list of lists para update
            range_label = f"A{row_index}" 
            worksheet.update(range_name=range_label, values=[row_data])
            log_audit("UPDATE", worksheet_name, row_data, row_index)
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao atualizar: {str(e)}")
        return False

def sync_all() -> Dict[str, bool]:
    """ Sincroniza as abas principais da planilha de finanças """
    # Defina aqui quais abas você quer sincronizar obrigatoriamente
    abas_para_sync = ["shows", "transactions", "members"]
    results = {}
    
    for aba in abas_para_sync:
        df = read_sheet(aba)
        if not df.empty:
            st.session_state[f"financas_{aba}_data"] = df
            results[aba] = True
        else:
            results[aba] = False
    
    st.session_state["last_cache_update"] = datetime.now()
    return results

def log_audit(action: str, sheet_info: str, data: List[Any], row_index: Optional[int] = None):
    if "audit_log" not in st.session_state:
        st.session_state.audit_log = []
    
    audit_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": st.session_state.get("user_name", "Sistema"),
        "action": action,
        "sheet": sheet_info,
        "row": row_index,
        "data": str(data)
    }
    st.session_state.audit_log.append(audit_entry)

def get_all_data() -> Dict[str, pd.DataFrame]:
    """ Retorna os dados do cache ou busca se estiverem expirados """
    abas = ["shows", "transactions", "members", "payout_rules"]
    data = {}
    
    last_update = st.session_state.get("last_cache_update")
    cache_expired = True if not last_update else (datetime.now() - last_update).total_seconds() > 300

    for aba in abas:
        cache_key = f"financas_{aba}_data"
        if cache_key in st.session_state and not cache_expired:
            data[aba] = st.session_state[cache_key]
        else:
            df = read_sheet(aba)
            st.session_state[cache_key] = df
            data[aba] = df
            
    if cache_expired:
        st.session_state["last_cache_update"] = datetime.now()
        
    return data