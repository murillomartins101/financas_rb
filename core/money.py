import pandas as pd
import re

def parse_brl(val) -> float:
    """
    Versão reforçada para evitar inflação de valores.
    Remove qualquer caractere que não seja número, ponto ou vírgula.
    """
    if pd.isna(val) or val == "" or val is None:
        return 0.0
    
    if isinstance(val, (int, float)):
        return float(val)

    try:
        # 1. Converte para string e limpa espaços
        s = str(val).strip()
        
        # 2. Remove TUDO que não for número, vírgula ou ponto
        s = re.sub(r'[^\d.,-]', '', s)
        
        # 3. Lógica robusta para padrão brasileiro
        if "," in s:
            # Se tem vírgula, o ponto é milhar e deve sumir
            s = s.replace(".", "").replace(",", ".")
        
        # 4. Converte e protege contra valores bizarros
        result = float(s)
        return result
    except (ValueError, TypeError):
        return 0.0

def format_brl(val: float) -> str:
    """Formata float para exibição padrão R$ 1.234,56."""
    try:
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"