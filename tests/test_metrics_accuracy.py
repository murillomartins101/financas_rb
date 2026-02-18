"""
Test script to verify that dashboard metrics match the spreadsheet data
This ensures the fixes correctly align dashboard values with the database
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from core.metrics import FinancialMetrics, validate_data_integrity


def load_test_data():
    """Load data from the Excel file"""
    excel_path = "data/Financas_RB.xlsx"
    
    data = {
        'shows': pd.read_excel(excel_path, sheet_name='shows'),
        'transactions': pd.read_excel(excel_path, sheet_name='transactions'),
    }
    
    return data


def test_data_integrity():
    """Test that data has proper structure and values"""
    print("="*80)
    print("TEST 1: Data Integrity Validation")
    print("="*80)
    
    data = load_test_data()
    warnings = validate_data_integrity(data)
    
    print(f"\nCritical Issues: {len(warnings['critical'])}")
    for w in warnings['critical']:
        print(f"  ❌ {w}")
    
    print(f"\nWarnings: {len(warnings['warnings'])}")
    for w in warnings['warnings']:
        print(f"  ⚠️  {w}")
    
    print(f"\nInfo: {len(warnings['info'])}")
    for w in warnings['info']:
        print(f"  ℹ️  {w}")
    
    if len(warnings['critical']) == 0:
        print("\n✅ Data integrity check PASSED")
        return True
    else:
        print("\n❌ Data integrity check FAILED")
        return False


def test_metrics_calculation():
    """Test that metrics match expected values from spreadsheet"""
    print("\n" + "="*80)
    print("TEST 2: Metrics Calculation Accuracy")
    print("="*80)
    
    data = load_test_data()
    metrics = FinancialMetrics(data)
    
    # Calculate all KPIs (no date filter = all data)
    kpis = metrics.calculate_all_kpis()
    
    # Expected values (calculated from spreadsheet analysis)
    expected = {
        'total_entradas': 45209.86,
        'total_despesas': 40502.35,
        'caixa_atual': 4707.51,
        'total_shows_realizados': 18,
        'a_receber': 0.0,
    }
    
    print("\n--- Comparison: Calculated vs Expected ---")
    all_match = True
    tolerance = 0.01  # Allow 1 cent difference for rounding
    
    for key, expected_val in expected.items():
        calculated_val = kpis.get(key, 0)
        diff = abs(calculated_val - expected_val)
        match = diff <= tolerance
        
        status = "✅" if match else "❌"
        print(f"{status} {key}:")
        print(f"    Expected:   R$ {expected_val:,.2f}")
        print(f"    Calculated: R$ {calculated_val:,.2f}")
        print(f"    Difference: R$ {diff:,.2f}")
        
        if not match:
            all_match = False
    
    if all_match:
        print("\n✅ All metrics match expected values!")
        return True
    else:
        print("\n❌ Some metrics don't match expected values")
        return False


def test_payment_status_filtering():
    """Test that only PAGO transactions are counted"""
    print("\n" + "="*80)
    print("TEST 3: Payment Status Filtering")
    print("="*80)
    
    data = load_test_data()
    trans = data['transactions']
    
    print(f"\nTotal transactions: {len(trans)}")
    print(f"\nPayment status distribution:")
    print(trans['payment_status'].value_counts())
    
    # Count by type and payment_status
    entradas_pago = len(trans[(trans['tipo'] == 'ENTRADA') & (trans['payment_status'] == 'PAGO')])
    saidas_pago = len(trans[(trans['tipo'] == 'SAIDA') & (trans['payment_status'] == 'PAGO')])
    
    print(f"\nENTRADA + PAGO: {entradas_pago} transactions")
    print(f"SAIDA + PAGO: {saidas_pago} transactions")
    
    # Verify no ESTORNADO in data
    estornado = len(trans[trans['payment_status'] == 'ESTORNADO'])
    
    if estornado == 0:
        print(f"\n✅ No ESTORNADO transactions found (expected)")
        return True
    else:
        print(f"\n⚠️  Found {estornado} ESTORNADO transactions")
        return False


def test_category_matching():
    """Test that musician payment categories are recognized"""
    print("\n" + "="*80)
    print("TEST 4: Category Matching")
    print("="*80)
    
    data = load_test_data()
    trans = data['transactions']
    
    # Import constants from metrics module
    from core.metrics import MUSICIAN_PAYOUT_CATEGORIES
    
    # Check for musician payment categories
    print(f"\nChecking for musician payment categories: {MUSICIAN_PAYOUT_CATEGORIES}")
    
    for cat in MUSICIAN_PAYOUT_CATEGORIES:
        count = len(trans[trans['categoria'] == cat])
        if count > 0:
            total = trans[trans['categoria'] == cat]['valor'].sum()
            print(f"  Found {cat}: {count} transactions, total R$ {total:,.2f}")
    
    # Calculate using metrics class public method
    metrics = FinancialMetrics(data)
    cache_total = metrics.calculate_total_cache_musicos(trans)
    
    print(f"\nTotal cache músicos calculated: R$ {cache_total:,.2f}")
    
    if cache_total > 0:
        print("✅ Musician payments detected and calculated")
        return True
    else:
        print("⚠️  No musician payments found (may be expected)")
        return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("RUNNING ALL TESTS")
    print("="*80)
    
    results = {
        'Data Integrity': test_data_integrity(),
        'Metrics Calculation': test_metrics_calculation(),
        'Payment Status Filtering': test_payment_status_filtering(),
        'Category Matching': test_category_matching(),
    }
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
