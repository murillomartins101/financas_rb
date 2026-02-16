# JWT Signature Error - Troubleshooting Guide

## Problem
When trying to authenticate with Google Sheets API, you may encounter:
```
Erro ao ler financas (transactions): ('invalid_grant: Invalid JWT Signature.', {'error': 'invalid_grant', 'error_description': 'Invalid JWT Signature.'})
```

## Root Cause
This error was caused by a conflict between the deprecated `oauth2client` library and the modern `google-auth` library used by the current code.

## Solution
The issue has been fixed in this update by:
1. Removing the deprecated `oauth2client` library from requirements.txt
2. Using only the modern `google-auth>=2.0.0` library
3. Improving error handling to provide better diagnostics

## If You Still See This Error

If you encounter JWT signature errors after this update, here are the possible causes and solutions:

### 1. Service Account Key Revoked or Deleted
**Symptoms:** Error persists even after updating code
**Solution:**
1. Go to Google Cloud Console → IAM & Admin → Service Accounts
2. Check if your service account still exists
3. If deleted, create a new service account and download new credentials
4. Update your credentials file or secrets.toml

### 2. System Clock Out of Sync
**Symptoms:** Intermittent authentication failures
**Solution:**
1. Check your system time: `date`
2. Ensure time is accurate (JWT tokens are time-sensitive, tolerance is ~5 minutes)
3. Sync your system clock with NTP if needed

### 3. Corrupted or Incomplete Credentials
**Symptoms:** Consistent authentication failures
**Solution:**
1. Verify your credentials file is complete
2. Check that `private_key` includes all content between:
   ```
   -----BEGIN PRIVATE KEY-----
   ... (full key content) ...
   -----END PRIVATE KEY-----
   ```
3. If using secrets.toml, ensure all `\n` characters are preserved
4. Download a fresh copy of credentials from Google Cloud Console

### 4. Missing universe_domain Field
**Symptoms:** Warnings in logs about missing optional fields
**Solution:**
The code now automatically adds the default value `googleapis.com` if missing, but you can update your credentials to include:
```json
{
  ...
  "universe_domain": "googleapis.com"
}
```

## How to Update Your Credentials

### Option 1: Using a JSON File (Recommended for Local Development)
1. Download service account key from Google Cloud Console
2. Save as `google_credentials.json` in the project root
3. Or use any filename (e.g., `financasrb-xxx.json`) - it will be auto-detected

### Option 2: Using secrets.toml (Recommended for Streamlit Cloud)
1. Create `.streamlit/secrets.toml` file
2. Add your credentials:
```toml
[google_credentials]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-sa@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
universe_domain = "googleapis.com"

spreadsheet_id = "your-spreadsheet-id-here"
```

### Option 3: Using Environment Variables
```bash
export GOOGLE_CREDENTIALS_JSON='{"type": "service_account", ...}'
export SPREADSHEET_ID="your-spreadsheet-id"
```

## Verification

To verify your authentication is working:
1. Start your application
2. Check the logs for:
   - "Credenciais carregadas com sucesso" (Credentials loaded successfully)
   - "Cliente gspread autorizado com sucesso" (gspread client authorized successfully)
3. If you see any errors, check the detailed logs for specific issues

## Additional Help

For more details on setting up Google Sheets integration, see:
- `docs/SETUP_GOOGLE_SHEETS.md`
- `secrets.toml.example`

## Changes Made in This Fix

### Files Modified
- `requirements.txt`: Removed `oauth2client>=4.1.3`, added `google-auth>=2.0.0`
- `core/google_cloud.py`: Enhanced error handling and credential loading
- `core/google_sheets.py`: Improved error messages for JWT issues
- `secrets.toml`: Updated with correct credentials from `financasrb-ddd33bb9d63f.json` (Feb 2026)

### Key Improvements
- ✅ No more library conflicts
- ✅ Auto-detection of credential files
- ✅ Better error messages with actionable solutions
- ✅ Support for optional fields like `universe_domain`
- ✅ Detailed logging for troubleshooting
- ✅ Credentials synchronized between JSON file and secrets.toml

### Latest Fix (February 2026)
**Issue:** "Invalid JWT Signature" error was caused by outdated/incorrect credentials in `secrets.toml`
**Solution:** Updated `secrets.toml` to use the correct and current Service Account credentials from `financasrb-ddd33bb9d63f.json`
- Updated `private_key_id` from `abe1d9e890262b831a89bb50a177049f7465d50d` to `ddd33bb9d63fa8be3c0e8278b791f5036b829335`
- Updated `private_key` with the corresponding valid key
- Both credentials now match the active Service Account in Google Cloud Console

### Latest Fix (February 16, 2026) - Additional Safeguards
**Issue:** Potential JWT Signature errors from malformed private_key credentials
**Solution:** Added robust private_key normalization in `core/google_cloud.py`
- Added validation to detect if private_key has literal `\n` strings instead of real newlines
- Automatically converts literal `\n` to real newlines when detected (< 10 real newlines but contains `\n`)
- Removed misleading `replace('\\n', '\n')` from `teste_conexao.py` that could cause confusion
- Added detailed logging to track normalization when it occurs
- This ensures JWT signatures work correctly regardless of how credentials are loaded

**What Changed:**
1. `core/google_cloud.py`: Added smart private_key normalization before creating Credentials object
2. `core/teste_conexao.py`: Removed unnecessary and potentially confusing private_key replacement
3. Both implementations now correctly handle credentials from TOML, JSON, and environment variables

