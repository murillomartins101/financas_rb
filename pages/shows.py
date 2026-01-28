"""
Página de gestão e análise de shows
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from core.data_loader import data_loader

def main():
    """Página de shows"""
    st.title("🎸 Shows - Rockbuzz Finance")
    
    # Carregar dados
    with st.spinner("Carregando shows..."):
        data = data_loader.load_all_data()
    
    if not data or 'shows' not in data or data['shows'].empty:
        st.error("Não foi possível carregar os dados de shows")
        return
    
    shows_df = data['shows'].copy()
    
    # Estatísticas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_shows = len(shows_df)
        st.metric("Total Shows", total_shows)
    
    with col2:
        shows_realizados = len(shows_df[shows_df['status'] == 'REALIZADO'])
        st.metric("Realizados", shows_realizados)
    
    with col3:
        shows_confirmados = len(shows_df[shows_df['status'] == 'CONFIRMADO'])
        st.metric("Confirmados", shows_confirmados)
    
    with col4:
        cache_total = shows_df['cache_acordado'].sum() if 'cache_acordado' in shows_df.columns else 0
        st.metric("Cache Total", f"R$ {cache_total:,.2f}")
    
    st.divider()
    
    # Tabela de shows
    st.subheader("Lista de Shows")
    
    # Preparar dados para exibição
    if 'data_show' in shows_df.columns:
        shows_df['data_show'] = pd.to_datetime(shows_df['data_show'], errors='coerce')
        shows_display = shows_df.copy()
        shows_display['data_show'] = shows_display['data_show'].dt.strftime('%d/%m/%Y')
    else:
        shows_display = shows_df.copy()
    
    st.dataframe(shows_display, use_container_width=True, height=400)