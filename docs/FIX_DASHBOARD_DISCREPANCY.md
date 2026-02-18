# Financial Dashboard Data Discrepancy Fix - Technical Documentation

## Executive Summary

This document details the root causes and solutions for the data discrepancy issues in the Rockbuzz Finance dashboard, where displayed metrics did not match the underlying spreadsheet data.

## Problem Statement

The financial dashboard was showing incorrect values for key metrics:
- Total Receitas (Revenue)
- Total Despesas (Expenses)
- Caixa Atual (Current Cash)
- Valor Bruto (Gross Value)
- Custos Operacionais (Operational Costs)

The dashboard numbers did not match the source data in the spreadsheet, causing confusion and unreliable financial reporting.

## Root Cause Analysis

### Issue 1: Data File Path Mismatch

**Symptom**: Application failed to load correct data or loaded wrong file structure

**Root Cause**: The data loader in `core/data_loader.py` was configured to look for data in `data/Financas_RB.xlsx`, but:
- The directory `data/` did not exist
- The correct file was located at `Old/Financas_RB_modelo_novo.xlsx`
- An outdated file at `Base/Backup/Financas_RB.xlsx` had incompatible structure (used `lancamentos` sheet instead of separate `shows` and `transactions` sheets)

**Solution**: 
- Created the `data/` directory
- Copied the correct file from `Old/Financas_RB_modelo_novo.xlsx` to `data/Financas_RB.xlsx`
- Ensured the file has the expected structure with sheets: `shows`, `transactions`, `payout_rules`, etc.

### Issue 2: Inconsistent Payment Status Filtering

**Symptom**: Total Despesas was including unpaid expenses

**Root Cause**: In `core/metrics.py`, the `_calculate_total_despesas()` method was using:
```python
(transactions_df['payment_status'] != 'ESTORNADO')
```
This included transactions with status 'NÃO PAGO' and 'NÃO RECEBIDO', which should not be counted as actual expenses according to the business rule: "Só entra em caixa: payment_status == PAGO"

**Solution**: Changed the filter to:
```python
(transactions_df['payment_status'] == 'PAGO')
```
This ensures only PAID transactions are counted, consistent with the calculation for revenues.

### Issue 3: Category Name Mismatch for Musician Payments

**Symptom**: Musician payment (cachê) metrics were not being calculated correctly

**Root Cause**: The code expected category name `CACHÊS-MÚSICOS` but the actual data uses `PAYOUT_MUSICOS`

**Solution**: 
- Created a constant `MUSICIAN_PAYOUT_CATEGORIES = ['CACHÊS-MÚSICOS', 'PAYOUT_MUSICOS']`
- Updated `calculate_total_cache_musicos()` to check for any of these category names
- This provides backward compatibility and supports multiple naming conventions

### Issue 4: Lack of Data Validation

**Symptom**: Silent failures when data structure changed

**Root Cause**: No validation of data integrity before processing

**Solution**: Added `validate_data_integrity()` function that checks:
- Required columns exist (show_id, data_show, status, tipo, valor, payment_status)
- Valid status values (REALIZADO, CONFIRMADO for shows; PAGO, NÃO RECEBIDO, etc. for transactions)
- Valid transaction types (ENTRADA, SAIDA)
- Null value detection in critical fields

## Code Changes

### 1. Data File Setup

**File**: `data/Financas_RB.xlsx` (created)

**Change**: Copied correct Excel file with proper structure to expected location

**Impact**: Application now loads correct data source with expected schema

### 2. Metrics Calculation Improvements

**File**: `core/metrics.py`

**Changes**:
1. Added module-level constants:
   - `VALID_SHOW_STATUS = ['REALIZADO', 'CONFIRMADO']`
   - `VALID_TRANSACTION_TYPES = ['ENTRADA', 'SAIDA']`
   - `VALID_PAYMENT_STATUS = ['PAGO', 'NÃO RECEBIDO', 'ESTORNADO', 'NÃO PAGO']`
   - `MUSICIAN_PAYOUT_CATEGORIES = ['CACHÊS-MÚSICOS', 'PAYOUT_MUSICOS']`

2. Fixed `_calculate_total_despesas()`:
   ```python
   # Before
   despesas = transactions_df[
       (transactions_df['tipo'] == 'SAIDA') & 
       (transactions_df['payment_status'] != 'ESTORNADO')
   ]
   
   # After
   despesas = transactions_df[
       (transactions_df['tipo'] == 'SAIDA') & 
       (transactions_df['payment_status'] == 'PAGO')
   ]
   ```

3. Enhanced `calculate_total_cache_musicos()`:
   ```python
   # Before
   cache_musicos = transactions_df[
       (transactions_df['tipo'] == 'SAIDA') & 
       (transactions_df['categoria'] == 'CACHÊS-MÚSICOS') &
       (transactions_df['payment_status'] == 'PAGO')
   ]
   
   # After
   cache_musicos = transactions_df[
       (transactions_df['tipo'] == 'SAIDA') & 
       (transactions_df['categoria'].isin(MUSICIAN_PAYOUT_CATEGORIES)) &
       (transactions_df['payment_status'] == 'PAGO')
   ]
   ```

4. Added `validate_data_integrity()` function

5. Added `get_validation_warnings()` method to FinancialMetrics class

**Impact**: Metrics now calculated consistently according to business rules

### 3. Test Suite

**File**: `tests/test_metrics_accuracy.py` (created)

**Changes**: Created comprehensive test suite with 4 test categories:
1. Data Integrity Validation
2. Metrics Calculation Accuracy
3. Payment Status Filtering
4. Category Matching

**Impact**: Automated verification that metrics match spreadsheet values

## Verification Results

All metrics now match the spreadsheet exactly:

| Metric | Expected (Spreadsheet) | Calculated (Dashboard) | Status |
|--------|----------------------|----------------------|---------|
| Total Receitas | R$ 45,209.86 | R$ 45,209.86 | ✅ Match |
| Total Despesas | R$ 40,502.35 | R$ 40,502.35 | ✅ Match |
| Caixa Atual | R$ 4,707.51 | R$ 4,707.51 | ✅ Match |
| Shows Realizados | 18 | 18 | ✅ Match |
| A Receber | R$ 0.00 | R$ 0.00 | ✅ Match |
| Cachê Músicos | R$ 22,911.06 | R$ 22,911.06 | ✅ Match |

### Test Results
```
✅ PASS - Data Integrity
✅ PASS - Metrics Calculation  
✅ PASS - Payment Status Filtering
✅ PASS - Category Matching
```

### Security Scan Results
```
✅ No security vulnerabilities detected (CodeQL analysis)
```

## Business Rules Compliance

The fix ensures compliance with documented business rules from README.md:

### Rule 4.1: Status de pagamento
> "Só entra em caixa: payment_status == PAGO"

**Compliance**: ✅ All metric calculations now filter for `payment_status == 'PAGO'`

### Rule 4.2: Reconhecimento de receita de shows
> "Receita só existe se: show.status == REALIZADO e pagamento == PAGO"

**Compliance**: ✅ `_calculate_total_entradas()` filters for `payment_status == 'PAGO'`

### Rule 4.4: Separação obrigatória de despesas
> "CACHÊS-MÚSICOS → KPI separado"

**Compliance**: ✅ Separate calculation with support for category variations

## Testing Strategy

### Unit Tests
- **Data Integrity**: Validates required columns and valid values
- **Calculation Accuracy**: Compares calculated metrics with known expected values
- **Filter Logic**: Verifies payment status filtering works correctly
- **Category Recognition**: Ensures musician payment categories are recognized

### Integration Testing
Run tests with: `python tests/test_metrics_accuracy.py`

Expected output: All 4 tests pass with exact value matching

## Maintenance Guidelines

### Adding New Categories
To add support for new category names:
1. Update the appropriate constant (e.g., `MUSICIAN_PAYOUT_CATEGORIES`)
2. The calculation logic will automatically include the new name
3. Add test case in `test_category_matching()`

### Modifying Valid Status Values
To add or modify valid status values:
1. Update the constant (`VALID_SHOW_STATUS`, `VALID_TRANSACTION_TYPES`, or `VALID_PAYMENT_STATUS`)
2. Update validation logic in `validate_data_integrity()` if needed
3. Update test expectations

### Data Structure Changes
If the spreadsheet structure changes:
1. Update `core/data_loader.py` to handle new columns or sheets
2. Update validation in `validate_data_integrity()`
3. Update or add tests to verify new structure

## Known Limitations

1. **Historical Data**: This fix applies to the current data structure. Historical data with different structures may need migration.

2. **Category Names**: Currently supports two naming conventions. Additional conventions require updating the constant.

3. **Excel Dependency**: Application requires Excel file at specific path. Consider adding configuration for flexible path.

## Future Improvements

1. **Configuration File**: Move constants to a configuration file for easier maintenance
2. **Automated Migration**: Add script to migrate old data format to new format
3. **Real-time Validation**: Add UI notifications when data validation warnings are detected
4. **Audit Log**: Track metric calculations with timestamps for debugging

## Conclusion

The financial dashboard now accurately reflects the underlying spreadsheet data. All calculations follow documented business rules, and comprehensive tests ensure continued accuracy. The codebase is more maintainable with extracted constants and improved encapsulation.

## Support

For questions or issues:
1. Check test results: `python tests/test_metrics_accuracy.py`
2. Review validation warnings via `get_validation_warnings()` method
3. Verify data file structure matches expected schema
4. Confirm payment_status values are from valid set

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-18  
**Author**: GitHub Copilot Agent
