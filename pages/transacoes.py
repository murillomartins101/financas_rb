"""
Página de visualização de transações
"""

import streamlit as st
import pandas as pd

from core.data_loader import data_loader

def main():
    """Página de transações"""
    st.title("💰 Transações - Rockbuzz Finance")
    
    # Carregar dados
    with st.spinner("Carregando transações..."):
        data = data_loader.load_all_data()
    
    if not data or 'transactions' not in data or data['transactions'].empty:
        st.error("Não foi possível carregar as transações")
        return
    
    transacoes_df = data['transactions'].copy()
    
    # Estatísticas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_transacoes = len(transacoes_df)
        st.metric("Total", total_transacoes)
    
    with col2:
        entradas = len(transacoes_df[transacoes_df['tipo'] == 'ENTRADA'])
        st.metric("Entradas", entradas)
    
    with col3:
        saidas = len(transacoes_df[transacoes_df['tipo'] == 'SAIDA'])
        st.metric("Saídas", saidas)
    
    with col4:
        valor_total = transacoes_df['valor'].sum() if 'valor' in transacoes_df.columns else 0
        st.metric("Valor Total", f"R$ {valor_total:,.2f}")
    
    st.divider()
    
    # Tabela de transações
    st.subheader("Todas as Transações")
    
    # Preparar dados para exibição
    if 'data' in transacoes_df.columns:
        transacoes_df['data'] = pd.to_datetime(transacoes_df['data'], errors='coerce')
        transacoes_display = transacoes_df.copy()
        transacoes_display['data'] = transacoes_display['data'].dt.strftime('%d/%m/%Y')
    else:
        transacoes_display = transacoes_df.copy()
    
    st.dataframe(transacoes_display, width='stretch', height=400)