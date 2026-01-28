"""
Configurações do sistema
"""
import streamlit as st
import os

def get_config():
    """Retorna a configuração do sistema."""
    # Configurações padrão
    config = {
        "google_sheets": {
            "spreadsheet_id": st.secrets.get("spreadsheet_id", ""),
            "credentials": st.secrets.get("google_credentials", {})
        },
        "cache_ttl": 300,  # 5 minutos
        "default_currency": "R$",
        "date_format": "%d/%m/%Y"
    }
    return config