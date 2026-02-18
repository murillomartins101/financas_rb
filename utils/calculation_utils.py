"""
Utilitários para cálculos financeiros e percentuais
Fornece funções seguras para evitar valores extremos e divisões por zero
"""

from typing import Optional, List
import math


def safe_percentage_change(
    current_value: float,
    previous_value: float,
    min_threshold: float = 0.01,
    cap_min: float = -100.0,
    cap_max: float = 1000.0
) -> Optional[float]:
    """
    Calcula mudança percentual de forma segura, com tratamento de valores extremos.
    
    Esta função implementa as seguintes proteções:
    1. Retorna None se o valor anterior for muito próximo de zero (< min_threshold)
    2. Limita o resultado ao intervalo [cap_min, cap_max] para evitar valores absurdos
    3. Trata corretamente casos onde ambos os valores são zero
    
    Args:
        current_value: Valor atual
        previous_value: Valor anterior
        min_threshold: Valor mínimo para o denominador (default: 0.01)
        cap_min: Limite mínimo do percentual (default: -100.0)
        cap_max: Limite máximo do percentual (default: 1000.0)
        
    Returns:
        Mudança percentual limitada, ou None se o cálculo não for confiável
        
    Examples:
        >>> safe_percentage_change(150, 100)  # Aumento de 50%
        50.0
        >>> safe_percentage_change(50, 100)   # Queda de 50%
        -50.0
        >>> safe_percentage_change(100, 0.01) # Valor anterior muito pequeno
        None
        >>> safe_percentage_change(0, 3000)   # Queda para zero
        -100.0
        >>> safe_percentage_change(5000, 100) # Aumento extremo
        1000.0 (limitado)
    """
    # Se ambos são zero ou muito próximos, não há mudança
    if abs(current_value) < min_threshold and abs(previous_value) < min_threshold:
        return 0.0
    
    # Se o valor anterior é muito pequeno, o cálculo não é confiável
    if abs(previous_value) < min_threshold:
        return None
    
    # Se o valor atual é muito pequeno comparado ao anterior (mais de 99% de queda)
    # e o valor anterior também é pequeno, não é confiável
    if abs(current_value) < min_threshold and abs(previous_value) < 10.0:
        return None
    
    # Calcula o percentual de mudança
    change_pct = ((current_value - previous_value) / abs(previous_value)) * 100
    
    # Limita aos valores máximos e mínimos
    if not math.isfinite(change_pct):
        return None
    
    # Se o percentual calculado está muito próximo dos limites (±99%), considerar não confiável
    # pois indica mudança extrema que pode não ser significativa
    if abs(change_pct) > 99.9 and abs(previous_value) < 10.0:
        return None
    
    return max(cap_min, min(cap_max, change_pct))


def safe_division(
    numerator: float,
    denominator: float,
    default: float = 0.0,
    min_threshold: float = 0.01
) -> float:
    """
    Realiza divisão segura, retornando valor padrão se denominador for muito pequeno.
    
    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor padrão a retornar (default: 0.0)
        min_threshold: Limite mínimo para o denominador (default: 0.01)
        
    Returns:
        Resultado da divisão ou valor padrão
        
    Examples:
        >>> safe_division(100, 50)
        2.0
        >>> safe_division(100, 0)
        0.0
        >>> safe_division(100, 0.005)
        0.0
        >>> safe_division(100, 0, default=None)
        None
    """
    if abs(denominator) < min_threshold:
        return default
    
    result = numerator / denominator
    
    if not math.isfinite(result):
        return default
    
    return result


def safe_percentage(
    part: float,
    total: float,
    default: float = 0.0,
    min_threshold: float = 0.01
) -> float:
    """
    Calcula percentual de forma segura (part/total * 100).
    
    Args:
        part: Parte do total
        total: Valor total
        default: Valor padrão a retornar (default: 0.0)
        min_threshold: Limite mínimo para o total (default: 0.01)
        
    Returns:
        Percentual (0-100) ou valor padrão
        
    Examples:
        >>> safe_percentage(25, 100)
        25.0
        >>> safe_percentage(50, 200)
        25.0
        >>> safe_percentage(100, 0)
        0.0
    """
    return safe_division(part, total, default, min_threshold) * 100


def format_percentage_change(
    value: Optional[float],
    decimals: int = 1,
    show_plus: bool = True
) -> str:
    """
    Formata mudança percentual para exibição.
    
    Args:
        value: Valor percentual ou None
        decimals: Número de casas decimais (default: 1)
        show_plus: Mostrar sinal + para valores positivos (default: True)
        
    Returns:
        String formatada
        
    Examples:
        >>> format_percentage_change(15.5)
        '+15.5%'
        >>> format_percentage_change(-20.3)
        '-20.3%'
        >>> format_percentage_change(None)
        'N/A'
    """
    if value is None:
        return "N/A"
    
    sign = "+" if value >= 0 and show_plus else ""
    return f"{sign}{value:.{decimals}f}%"


def is_reliable_trend(
    values: List[float],
    min_values: int = 2,
    min_value_threshold: float = 1.0
) -> bool:
    """
    Verifica se uma série de valores é confiável para cálculo de tendências.
    
    Args:
        values: Lista de valores
        min_values: Número mínimo de valores necessários (default: 2)
        min_value_threshold: Valor mínimo para considerar significativo (default: 1.0)
        
    Returns:
        True se a tendência é confiável, False caso contrário
        
    Examples:
        >>> is_reliable_trend([100, 150, 200])
        True
        >>> is_reliable_trend([0.01, 0.02])
        False
        >>> is_reliable_trend([100])
        False
    """
    if not values or len(values) < min_values:
        return False
    
    # Verifica se há valores significativos suficientes
    significant_values = [v for v in values if abs(v) >= min_value_threshold]
    
    return len(significant_values) >= min_values


def calculate_margin_safely(
    revenue: float,
    expenses: float,
    min_revenue_threshold: float = 0.01
) -> Optional[float]:
    """
    Calcula margem de lucro de forma segura.
    
    Fórmula: ((receita - despesa) / receita) * 100
    
    Args:
        revenue: Receita total
        expenses: Despesas totais
        min_revenue_threshold: Receita mínima para cálculo confiável (default: 0.01)
        
    Returns:
        Margem percentual ou None se não confiável
        
    Examples:
        >>> calculate_margin_safely(1000, 700)
        30.0
        >>> calculate_margin_safely(1000, 1200)
        -20.0
        >>> calculate_margin_safely(0, 100)
        None
    """
    if abs(revenue) < min_revenue_threshold:
        return None
    
    profit = revenue - expenses
    margin = (profit / abs(revenue)) * 100
    
    if not math.isfinite(margin):
        return None
    
    return margin


def get_sparkline_values(
    values: List[float],
    min_length: int = 5,
    default_value: float = 0.0
) -> List[float]:
    """
    Prepara valores para exibição em sparkline, preenchendo se necessário.
    
    Args:
        values: Lista de valores originais
        min_length: Comprimento mínimo da lista (default: 5)
        default_value: Valor padrão para preenchimento (default: 0.0)
        
    Returns:
        Lista de valores com comprimento mínimo
        
    Examples:
        >>> get_sparkline_values([100, 200, 300])
        [0.0, 0.0, 100, 200, 300]
        >>> get_sparkline_values([1, 2, 3, 4, 5, 6])
        [1, 2, 3, 4, 5, 6]
    """
    if not values:
        return [default_value] * min_length
    
    if len(values) >= min_length:
        return values
    
    # Preenche no início com valores padrão
    padding = [default_value] * (min_length - len(values))
    return padding + values
