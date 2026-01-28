"""
Página de cadastro de registros (CRUD)
"""

import streamlit as st
import pandas as pd

from core.data_loader import data_loader

def main():
    """Página de cadastros"""
    st.title("📝 Cadastro de Registros")
    
    st.info("Funcionalidade em desenvolvimento")
    st.write("Esta página permitirá cadastrar, editar e excluir registros.")
    
    # Opções de cadastro
    opcao = st.selectbox(
        "O que você deseja fazer?",
        ["Visualizar dados", "Adicionar novo", "Editar existente", "Excluir"]
    )
    
    if opcao == "Visualizar dados":
        # Carregar dados
        with st.spinner("Carregando..."):
            data = data_loader.load_all_data()
        
        # Mostrar abas com diferentes tipos de dados
        if data:
            tabs = st.tabs(list(data.keys()))
            
            for tab, (key, df) in zip(tabs, data.items()):
                with tab:
                    st.write(f"**{key.upper()}** - {len(df)} registros")
                    if not df.empty:
                        st.dataframe(df, use_container_width=True, height=300)
                    else:
                        st.info("Nenhum dado disponível")