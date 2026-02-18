"""
Test script to verify dashboard data discrepancy fixes

Tests two specific fixes:
1. ESTORNADO transactions are NOT removed by data_loader
2. get_monthly_data filters for payment_status == 'PAGO'
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from core.data_loader import DataLoader
from pages.home import get_monthly_data


def test_estornado_transactions_not_removed():
    """Test that ESTORNADO transactions are NOT removed by data_loader"""
    print("="*80)
    print("TEST 1: ESTORNADO Transactions Not Removed by DataLoader")
    print("="*80)
    
    # Load data directly from Excel file
    try:
        excel_path = "data/Financas_RB.xlsx"
        trans = pd.read_excel(excel_path, sheet_name='transactions')
    except Exception as e:
        print(f"⚠️  Could not load test data: {e}")
        return False
    
    if trans.empty:
        print("⚠️  No transactions data loaded")
        return False
    
    # Check if payment_status column exists
    if 'payment_status' not in trans.columns:
        print("⚠️  payment_status column not found in transactions")
        return False
    
    # Count ESTORNADO transactions in raw data
    estornado_count = len(trans[trans['payment_status'].astype(str).str.strip() == 'ESTORNADO'])
    
    print(f"\nTotal transactions in raw data: {len(trans)}")
    print(f"ESTORNADO transactions in raw data: {estornado_count}")
    print(f"\nPayment status distribution in raw data:")
    print(trans['payment_status'].value_counts())
    
    # Now test that DataLoader processes them
    # Create a test dataframe with ESTORNADO
    test_df = pd.DataFrame({
        'id': ['T001', 'T002', 'T003'],
        'data': ['2024-01-01', '2024-01-15', '2024-02-01'],
        'valor': ['R$ 1.000,00', 'R$ 500,00', 'R$ 2.000,00'],
        'tipo': ['ENTRADA', 'SAIDA', 'ENTRADA'],
        'payment_status': ['PAGO', 'ESTORNADO', 'NÃO RECEBIDO']
    })
    
    # Process using DataLoader's internal method
    loader = DataLoader()
    processed_df = loader._process_transactions(test_df)
    
    # Check if ESTORNADO transaction is still present
    estornado_after = len(processed_df[processed_df['payment_status'].astype(str).str.strip() == 'ESTORNADO'])
    
    print(f"\nTest processing:")
    print(f"  Before processing: 3 transactions (1 PAGO, 1 ESTORNADO, 1 NÃO RECEBIDO)")
    print(f"  After processing: {len(processed_df)} transactions")
    print(f"  ESTORNADO after processing: {estornado_after}")
    
    if estornado_after == 1:
        print("\n✅ PASS: Data loader no longer filters ESTORNADO transactions")
        print("   (They are now visible and can be filtered by individual screens)")
        return True
    else:
        print("\n❌ FAIL: ESTORNADO transactions were filtered out by data_loader")
        return False


def test_get_monthly_data_filters_pago():
    """Test that get_monthly_data only includes PAGO transactions"""
    print("\n" + "="*80)
    print("TEST 2: get_monthly_data Filters for payment_status == 'PAGO'")
    print("="*80)
    
    # Create test data with mixed payment statuses
    test_data = pd.DataFrame({
        'data': ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-10', '2024-03-01'],
        'tipo': ['ENTRADA', 'SAIDA', 'ENTRADA', 'SAIDA', 'ENTRADA'],
        'valor': [1000.0, 500.0, 2000.0, 300.0, 1500.0],
        'payment_status': ['PAGO', 'PAGO', 'NÃO RECEBIDO', 'ESTORNADO', 'PAGO']
    })
    
    print(f"\nTest data created with {len(test_data)} transactions:")
    print(test_data[['data', 'tipo', 'valor', 'payment_status']])
    
    # Call get_monthly_data
    monthly_data = get_monthly_data(test_data)
    
    print(f"\nMonthly data aggregated:")
    print(monthly_data)
    
    # Verify the function filtered correctly
    # Expected: Only rows with payment_status == 'PAGO' should be aggregated
    # That's rows 0, 1, 4 (total ENTRADA: 2500, total SAIDA: 500)
    
    if monthly_data.empty:
        print("\n❌ FAIL: get_monthly_data returned empty DataFrame")
        return False
    
    # Check if filtering worked
    # January should have: ENTRADA=1000, SAIDA=500 (both PAGO)
    # February should have: ENTRADA=0, SAIDA=0 (both NOT PAGO)
    # March should have: ENTRADA=1500, SAIDA=0 (ENTRADA is PAGO)
    
    jan_data = monthly_data[monthly_data['mes'] == '2024-01']
    feb_data = monthly_data[monthly_data['mes'] == '2024-02']
    mar_data = monthly_data[monthly_data['mes'] == '2024-03']
    
    success = True
    
    if not jan_data.empty:
        jan_entrada = jan_data['ENTRADA'].values[0]
        jan_saida = jan_data['SAIDA'].values[0]
        if jan_entrada == 1000.0 and jan_saida == 500.0:
            print(f"\n✅ January: ENTRADA={jan_entrada}, SAIDA={jan_saida} (correct)")
        else:
            print(f"\n❌ January: ENTRADA={jan_entrada}, SAIDA={jan_saida} (expected 1000, 500)")
            success = False
    
    if not feb_data.empty:
        feb_entrada = feb_data['ENTRADA'].values[0]
        feb_saida = feb_data['SAIDA'].values[0]
        if feb_entrada == 0 and feb_saida == 0:
            print(f"✅ February: ENTRADA={feb_entrada}, SAIDA={feb_saida} (correct - no PAGO)")
        else:
            print(f"❌ February: ENTRADA={feb_entrada}, SAIDA={feb_saida} (expected 0, 0)")
            success = False
    else:
        print("✅ February: No data (correct - no PAGO transactions)")
    
    if not mar_data.empty:
        mar_entrada = mar_data['ENTRADA'].values[0]
        mar_saida = mar_data['SAIDA'].values[0]
        if mar_entrada == 1500.0 and mar_saida == 0:
            print(f"✅ March: ENTRADA={mar_entrada}, SAIDA={mar_saida} (correct)")
        else:
            print(f"❌ March: ENTRADA={mar_entrada}, SAIDA={mar_saida} (expected 1500, 0)")
            success = False
    
    if success:
        print("\n✅ PASS: get_monthly_data correctly filters payment_status == 'PAGO'")
    else:
        print("\n❌ FAIL: get_monthly_data filtering not working as expected")
    
    return success


def test_consistency_with_real_data():
    """Test consistency using real data from Excel"""
    print("\n" + "="*80)
    print("TEST 3: Consistency with Real Data")
    print("="*80)
    
    try:
        # Load data directly from Excel
        excel_path = "data/Financas_RB.xlsx"
        trans = pd.read_excel(excel_path, sheet_name='transactions')
        
        if trans.empty:
            print("⚠️  No transactions data loaded")
            return False
        
        # Process data like DataLoader would (but without ESTORNADO filter)
        # Convert data types properly
        trans['data'] = pd.to_datetime(trans['data'], errors='coerce')
        trans['valor'] = pd.to_numeric(trans['valor'], errors='coerce')
        
        # Get monthly data
        monthly_data = get_monthly_data(trans)
        
        # Calculate expected totals (only PAGO)
        if 'payment_status' in trans.columns:
            pago_trans = trans[trans['payment_status'].astype(str).str.strip() == 'PAGO']
            
            total_entrada_pago = pago_trans[pago_trans['tipo'] == 'ENTRADA']['valor'].sum()
            total_saida_pago = pago_trans[pago_trans['tipo'] == 'SAIDA']['valor'].sum()
            
            # Calculate from monthly data
            if not monthly_data.empty:
                monthly_entrada_total = monthly_data['ENTRADA'].sum()
                monthly_saida_total = monthly_data['SAIDA'].sum()
                
                print(f"\nDirect aggregation (PAGO only):")
                print(f"  Total ENTRADA (PAGO): R$ {total_entrada_pago:,.2f}")
                print(f"  Total SAIDA (PAGO): R$ {total_saida_pago:,.2f}")
                
                print(f"\nMonthly aggregation:")
                print(f"  Total ENTRADA: R$ {monthly_entrada_total:,.2f}")
                print(f"  Total SAIDA: R$ {monthly_saida_total:,.2f}")
                
                # Check if they match (within tolerance for rounding)
                tolerance = 0.01
                entrada_match = abs(total_entrada_pago - monthly_entrada_total) <= tolerance
                saida_match = abs(total_saida_pago - monthly_saida_total) <= tolerance
                
                if entrada_match and saida_match:
                    print("\n✅ PASS: Monthly data matches direct aggregation")
                    return True
                else:
                    print("\n❌ FAIL: Monthly data does NOT match direct aggregation")
                    print(f"   ENTRADA diff: R$ {abs(total_entrada_pago - monthly_entrada_total):,.2f}")
                    print(f"   SAIDA diff: R$ {abs(total_saida_pago - monthly_saida_total):,.2f}")
                    return False
            else:
                print("⚠️  Monthly data is empty")
                return False
        else:
            print("⚠️  payment_status column not found")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests for dashboard fixes"""
    print("\n" + "="*80)
    print("DASHBOARD FIXES VALIDATION TESTS")
    print("="*80)
    
    results = {
        'ESTORNADO Not Removed': test_estornado_transactions_not_removed(),
        'get_monthly_data Filters PAGO': test_get_monthly_data_filters_pago(),
        'Consistency with Real Data': test_consistency_with_real_data(),
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
