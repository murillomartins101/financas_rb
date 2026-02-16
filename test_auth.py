#!/usr/bin/env python3
"""
Script simples para testar autenticação com Google Sheets
"""

import sys
import json
from pathlib import Path
from google.oauth2.service_account import Credentials
import gspread

def test_credentials():
    """Testa as credenciais do Google Cloud"""
    
    print("=" * 80)
    print("TESTE DE AUTENTICAÇÃO GOOGLE SHEETS")
    print("=" * 80)
    
    # Tentar carregar do arquivo JSON
    json_files = list(Path(".").glob("financasrb-*.json"))
    
    if not json_files:
        print("\n❌ ERRO: Nenhum arquivo de credenciais encontrado (financasrb-*.json)")
        return False
    
    json_file = json_files[0]
    print(f"\n✓ Arquivo de credenciais encontrado: {json_file.name}")
    
    try:
        with open(json_file, 'r') as f:
            creds_dict = json.load(f)
        
        print(f"✓ Arquivo JSON carregado com sucesso")
        print(f"  - project_id: {creds_dict.get('project_id')}")
        print(f"  - client_email: {creds_dict.get('client_email')}")
        print(f"  - private_key_id: {creds_dict.get('private_key_id')}")
        
        # Validar campos obrigatórios
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 
                          'client_email', 'client_id', 'auth_uri', 'token_uri']
        missing = [f for f in required_fields if f not in creds_dict]
        
        if missing:
            print(f"\n❌ ERRO: Campos obrigatórios ausentes: {', '.join(missing)}")
            return False
        
        print(f"✓ Todos os campos obrigatórios presentes")
        
        # Tentar criar credenciais
        print("\n⏳ Criando objeto de credenciais...")
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        print("✓ Credenciais criadas com sucesso")
        
        # Tentar autorizar cliente
        print("\n⏳ Autorizando cliente gspread...")
        client = gspread.authorize(credentials)
        print("✓ Cliente autorizado com sucesso")
        
        # Tentar abrir planilha
        # Primeiro tenta ler do secrets, depois variável de ambiente, depois usa o padrão
        spreadsheet_id = None
        try:
            # Tentar carregar do secrets.toml
            import streamlit as st
            if hasattr(st, 'secrets') and 'spreadsheet_id' in st.secrets:
                spreadsheet_id = st.secrets.get('spreadsheet_id')
        except:
            pass
        
        # Fallback para variável de ambiente
        if not spreadsheet_id:
            import os
            spreadsheet_id = os.getenv('SPREADSHEET_ID')
        
        # Fallback para ID padrão (pode ser passado como argumento)
        if not spreadsheet_id:
            spreadsheet_id = "1TZDj3ZNfFluXLTlc4hkkvMb0gs17WskzwS9LapR44eI"
        
        print(f"\n⏳ Tentando abrir planilha (ID: {spreadsheet_id})...")
        spreadsheet = client.open_by_key(spreadsheet_id)
        print(f"✓ Planilha aberta com sucesso: '{spreadsheet.title}'")
        
        # Listar abas
        worksheets = spreadsheet.worksheets()
        print(f"\n✓ {len(worksheets)} aba(s) encontrada(s):")
        for ws in worksheets:
            print(f"  - {ws.title} ({ws.row_count} linhas x {ws.col_count} colunas)")
        
        print("\n" + "=" * 80)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 80)
        return True
        
    except FileNotFoundError:
        print(f"\n❌ ERRO: Arquivo não encontrado: {json_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"\n❌ ERRO: JSON inválido: {e}")
        return False
    except Exception as e:
        error_str = str(e)
        print(f"\n❌ ERRO: {error_str}")
        
        # Diagnóstico específico para erros comuns
        if "invalid_grant" in error_str.lower() or "invalid jwt signature" in error_str.lower():
            print("\n📋 DIAGNÓSTICO:")
            print("  - Causa: Assinatura JWT inválida")
            print("  - Possíveis razões:")
            print("    1. A chave foi revogada no Google Cloud Console")
            print("    2. O relógio do sistema está dessincronizado")
            print("    3. A chave privada está corrompida")
            print("\n💡 SOLUÇÕES:")
            print("  1. Verifique se a Service Account existe no Google Cloud Console")
            print("  2. Gere uma nova chave JSON e substitua o arquivo")
            print("  3. Verifique a hora do sistema com: date")
        elif "PERMISSION_DENIED" in error_str or "403" in error_str:
            print("\n📋 DIAGNÓSTICO:")
            print("  - Causa: Permissão negada")
            print("\n💡 SOLUÇÕES:")
            print("  1. Compartilhe a planilha com o email da Service Account:")
            print(f"     {creds_dict.get('client_email')}")
            print("  2. Dê permissão de 'Editor' para a Service Account")
        elif "Spreadsheet not found" in error_str:
            print("\n📋 DIAGNÓSTICO:")
            print("  - Causa: Planilha não encontrada")
            print("\n💡 SOLUÇÕES:")
            print("  1. Verifique se o ID da planilha está correto")
            print("  2. Verifique se a planilha não foi deletada")
        
        return False

if __name__ == "__main__":
    success = test_credentials()
    sys.exit(0 if success else 1)
