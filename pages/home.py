"""
Página inicial do dashboard
Exibe KPIs principais e visão geral do sistema
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from core.data_loader import data_loader
from core.metrics import calculate_kpis_with_explanation
from core.ui_components import render_kpi_grid
from core.filters import DataFilter, display_current_filters

def main():
    """
    Função principal da página Home
    """
    st.title("🏠 Home - Rockbuzz Finance")
    
    # Carregar dados
    with st.spinner("Carregando dados..."):
        data = data_loader.load_all_data()
    
    if not data or 'transactions' not in data or data['transactions'].empty:
        st.error("❌ Não foi possível carregar os dados financeiros.")
        st.info("Por favor, verifique a conexão com o Google Sheets ou o arquivo Excel local.")
        return
    
    # Aplicar filtros globais
    filtered_data = DataFilter.apply_global_filters(data)
    
    # Exibir filtros ativos
    display_current_filters()
    
    st.divider()
    
    # Seção 1: KPIs Principais
    st.header("📊 KPIs Financeiros")
    
    # Calcular KPIs com explicações
    start_date = st.session_state.get('filter_start_date')
    end_date = st.session_state.get('filter_end_date')
    
    kpis_with_explanations = calculate_kpis_with_explanation(
        filtered_data, start_date, end_date
    )
    
    # Exibir grid de KPIs
    render_kpi_grid(kpis_with_explanations, columns=4)
    
    st.divider()
    
    # Seção 2: Resumo Executivo
    st.header("📋 Resumo Executivo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Performance")
        if 'total_entradas' in kpis_with_explanations:
            receitas = kpis_with_explanations['total_entradas']['valor']
            despesas = kpis_with_explanations['total_despesas']['valor']
            lucro = receitas - despesas
            margem = (lucro / receitas * 100) if receitas > 0 else 0
            
            st.metric("Receitas Totais", f"R$ {receitas:,.2f}")
            st.metric("Lucro", f"R$ {lucro:,.2f}")
            st.metric("Margem", f"{margem:.1f}%")
    
    with col2:
        st.subheader("💰 Saúde Financeira")
        if 'caixa_atual' in kpis_with_explanations:
            caixa = kpis_with_explanations['caixa_atual']['valor']
            a_receber = kpis_with_explanations['a_receber']['valor']
            
            st.metric("Caixa Atual", f"R$ {caixa:,.2f}")
            st.metric("A Receber", f"R$ {a_receber:,.2f}")
            st.metric("Shows Realizados", kpis_with_explanations.get('total_shows_realizados', {}).get('valor', 0))
    
    # Botão de atualização
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        data_loader.load_all_data(force_refresh=True)
        st.rerun()