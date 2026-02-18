"""
Testes para utilitários de cálculo seguro
Verifica que os cálculos de percentuais lidam corretamente com casos extremos
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.calculation_utils import (
    safe_percentage_change,
    safe_division,
    safe_percentage,
    format_percentage_change,
    is_reliable_trend,
    calculate_margin_safely,
    get_sparkline_values
)


def test_safe_percentage_change():
    """Testa cálculo seguro de mudança percentual"""
    print("="*80)
    print("TEST: safe_percentage_change")
    print("="*80)
    
    tests = [
        # (current, previous, expected, description)
        (150, 100, 50.0, "Aumento de 50%"),
        (50, 100, -50.0, "Queda de 50%"),
        (0, 100, -100.0, "Queda para zero"),
        (200, 100, 100.0, "Dobrou (100%)"),
        (100, 0.001, None, "Valor anterior muito pequeno"),
        (0, 0, 0.0, "Ambos zero"),
        (5000, 100, 1000.0, "Aumento extremo (limitado a 1000%)"),
        (100, 5000, -98.0, "Queda extrema"),
        (3180, 0.07, None, "Denominador próximo de zero (mudança extrema)"),
    ]
    
    all_passed = True
    for current, previous, expected, desc in tests:
        result = safe_percentage_change(current, previous)
        
        if expected is None:
            passed = result is None
        else:
            passed = result is not None and abs(result - expected) < 0.01
        
        status = "✅" if passed else "❌"
        print(f"{status} {desc}")
        print(f"   Input: {current} vs {previous}")
        print(f"   Expected: {expected}, Got: {result}")
        
        if not passed:
            all_passed = False
    
    return all_passed


def test_safe_division():
    """Testa divisão segura"""
    print("\n" + "="*80)
    print("TEST: safe_division")
    print("="*80)
    
    tests = [
        # (numerator, denominator, expected, description)
        (100, 50, 2.0, "Divisão normal"),
        (100, 0, 0.0, "Divisão por zero"),
        (100, 0.005, 0.0, "Denominador muito pequeno"),
        (0, 100, 0.0, "Numerador zero"),
        (-100, 50, -2.0, "Números negativos"),
    ]
    
    all_passed = True
    for num, denom, expected, desc in tests:
        result = safe_division(num, denom)
        passed = abs(result - expected) < 0.01
        
        status = "✅" if passed else "❌"
        print(f"{status} {desc}")
        print(f"   {num} / {denom} = {result} (expected {expected})")
        
        if not passed:
            all_passed = False
    
    return all_passed


def test_calculate_margin_safely():
    """Testa cálculo seguro de margem"""
    print("\n" + "="*80)
    print("TEST: calculate_margin_safely")
    print("="*80)
    
    tests = [
        # (revenue, expenses, expected, description)
        (1000, 700, 30.0, "Margem positiva 30%"),
        (1000, 1200, -20.0, "Margem negativa (prejuízo)"),
        (0, 100, None, "Receita zero"),
        (0.5, 100, None, "Receita muito pequena (threshold 1.0)"),
        (45209.86, 40502.35, 10.41, "Dados reais do teste"),
    ]
    
    all_passed = True
    for revenue, expenses, expected, desc in tests:
        result = calculate_margin_safely(revenue, expenses, min_revenue_threshold=1.0)
        
        if expected is None:
            passed = result is None
        else:
            passed = result is not None and abs(result - expected) < 0.01
        
        status = "✅" if passed else "❌"
        print(f"{status} {desc}")
        print(f"   Revenue: R$ {revenue:,.2f}, Expenses: R$ {expenses:,.2f}")
        print(f"   Expected: {expected}, Got: {result}")
        
        if not passed:
            all_passed = False
    
    return all_passed


def test_is_reliable_trend():
    """Testa validação de tendência confiável"""
    print("\n" + "="*80)
    print("TEST: is_reliable_trend")
    print("="*80)
    
    tests = [
        # (values, expected, description)
        ([100, 150, 200], True, "Tendência válida com 3 valores"),
        ([0.01, 0.02], False, "Valores muito pequenos"),
        ([100], False, "Apenas 1 valor"),
        ([], False, "Lista vazia"),
        ([0, 0, 0], False, "Todos zeros"),
        ([100, 200], True, "Dois valores válidos"),
        ([1000, 2000, 3000, 0.01], True, "Maioria valores válidos"),
    ]
    
    all_passed = True
    for values, expected, desc in tests:
        result = is_reliable_trend(values)
        passed = result == expected
        
        status = "✅" if passed else "❌"
        print(f"{status} {desc}")
        print(f"   Values: {values}")
        print(f"   Expected: {expected}, Got: {result}")
        
        if not passed:
            all_passed = False
    
    return all_passed


def test_get_sparkline_values():
    """Testa preparação de valores para sparkline"""
    print("\n" + "="*80)
    print("TEST: get_sparkline_values")
    print("="*80)
    
    tests = [
        # (input_values, expected_length, description)
        ([100, 200, 300], 5, "Preenche até 5 valores"),
        ([1, 2, 3, 4, 5, 6], 6, "Mantém se já tem 5+"),
        ([], 5, "Lista vazia retorna 5 zeros"),
        ([100], 5, "Um valor preenchido"),
    ]
    
    all_passed = True
    for values, expected_len, desc in tests:
        result = get_sparkline_values(values)
        passed = len(result) == expected_len
        
        status = "✅" if passed else "❌"
        print(f"{status} {desc}")
        print(f"   Input: {values}")
        print(f"   Output length: {len(result)} (expected {expected_len})")
        
        if not passed:
            all_passed = False
    
    return all_passed


def test_format_percentage_change():
    """Testa formatação de mudança percentual"""
    print("\n" + "="*80)
    print("TEST: format_percentage_change")
    print("="*80)
    
    tests = [
        # (value, expected, description)
        (15.5, "+15.5%", "Valor positivo"),
        (-20.3, "-20.3%", "Valor negativo"),
        (None, "N/A", "Valor None"),
        (0, "+0.0%", "Zero"),
        (100.0, "+100.0%", "Limite superior comum"),
        (-100.0, "-100.0%", "Limite inferior comum"),
    ]
    
    all_passed = True
    for value, expected, desc in tests:
        result = format_percentage_change(value)
        passed = result == expected
        
        status = "✅" if passed else "❌"
        print(f"{status} {desc}")
        print(f"   Input: {value}")
        print(f"   Expected: '{expected}', Got: '{result}'")
        
        if not passed:
            all_passed = False
    
    return all_passed


def test_extreme_cases():
    """Testa casos extremos que causavam problemas"""
    print("\n" + "="*80)
    print("TEST: Casos Extremos (Problema Original)")
    print("="*80)
    
    # Caso real que causava -100% ou valores extremos
    tests = [
        {
            'name': 'Mês com valor muito baixo',
            'current': 0.07,
            'previous': 3180.0,
            'expected': -100.0,  # Queda extrema, limitada a -100%
        },
        {
            'name': 'Mês zero após mês normal',
            'current': 0.0,
            'previous': 888.02,
            'expected': -100.0,  # Pode calcular, queda para zero
        },
        {
            'name': 'Valores muito diferentes',
            'current': 5000,
            'previous': 100,
            'expected': 1000.0,  # Limitado a 1000%
        },
    ]
    
    all_passed = True
    for test in tests:
        result = safe_percentage_change(test['current'], test['previous'])
        
        if test['expected'] is None:
            passed = result is None
        else:
            passed = result is not None and abs(result - test['expected']) < 0.01
        
        status = "✅" if passed else "❌"
        print(f"\n{status} {test['name']}")
        print(f"   Current: R$ {test['current']:,.2f}")
        print(f"   Previous: R$ {test['previous']:,.2f}")
        print(f"   Expected: {test['expected']}")
        print(f"   Got: {result}")
        
        if not passed:
            all_passed = False
    
    return all_passed


def run_all_tests():
    """Executa todos os testes"""
    print("\n" + "="*80)
    print("RUNNING CALCULATION UTILS TESTS")
    print("="*80 + "\n")
    
    results = {
        'safe_percentage_change': test_safe_percentage_change(),
        'safe_division': test_safe_division(),
        'calculate_margin_safely': test_calculate_margin_safely(),
        'is_reliable_trend': test_is_reliable_trend(),
        'get_sparkline_values': test_get_sparkline_values(),
        'format_percentage_change': test_format_percentage_change(),
        'extreme_cases': test_extreme_cases(),
    }
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ ALL CALCULATION UTILS TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
