"""
Utilitários para manipulação de datas
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import pandas as pd

def get_period_dates(period_name: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Retorna datas de início e fim baseadas no nome do período
    
    Args:
        period_name: Nome do período
        
    Returns:
        Tupla (data_inicio, data_fim)
    """
    today = datetime.now()
    
    if period_name == "Mês atual":
        start = today.replace(day=1)
        end = today
    elif period_name == "Mês anterior":
        first_day_current = today.replace(day=1)
        end = first_day_current - timedelta(days=1)
        start = end.replace(day=1)
    elif period_name == "Últimos 6 meses":
        start = today - timedelta(days=180)
        end = today
    elif period_name == "Ano atual":
        start = today.replace(month=1, day=1)
        end = today
    elif period_name == "Ano anterior":
        start = today.replace(year=today.year-1, month=1, day=1)
        end = today.replace(year=today.year-1, month=12, day=31)
    else:  # Todo período
        start = None
        end = None
    
    return start, end

def format_currency(value: float) -> str:
    """
    Formata valor como moeda brasileira
    
    Args:
        value: Valor numérico
        
    Returns:
        String formatada
    """
    if value >= 1000000:
        return f"R$ {value/1000000:.1f}M"
    elif value >= 1000:
        return f"R$ {value/1000:.1f}K"
    else:
        return f"R$ {value:,.2f}"