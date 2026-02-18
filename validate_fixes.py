#!/usr/bin/env python3
"""
Script de validação das correções aplicadas
"""

import os
import sys
from pathlib import Path

def validate_init_file():
    """Valida que __init__.py está correto"""
    init_path = Path("core/__init__.py")
    old_path = Path("core/_init_.py")
    
    if not init_path.exists():
        print("❌ FALHA: core/__init__.py não encontrado")
        return False
    
    if old_path.exists():
        print("❌ FALHA: core/_init_.py ainda existe")
        return False
    
    print("✅ core/__init__.py: Nome correto")
    return True

def validate_syntax():
    """Valida sintaxe de todos os arquivos Python"""
    import py_compile
    
    errors = []
    files = [
        "app.py",
        "core/auth.py",
        "core/validators.py",
        "core/ui_components.py",
        "core/cache_manager.py",
        "pages/home.py",
        "pages/shows.py",
        "pages/transacoes.py",
        "pages/cadastros.py",
        "pages/relatorios.py",
    ]
    
    for file in files:
        try:
            py_compile.compile(file, doraise=True)
        except Exception as e:
            errors.append(f"{file}: {e}")
    
    if errors:
        print(f"❌ FALHA: {len(errors)} arquivos com erro de sintaxe")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print(f"✅ Sintaxe: {len(files)} arquivos validados")
    return True

def validate_main_calls():
    """Valida que páginas têm chamada ao main()"""
    pages = [
        "pages/home.py",
        "pages/shows.py",
        "pages/transacoes.py",
        "pages/cadastros.py",
        "pages/relatorios.py",
    ]
    
    missing = []
    for page in pages:
        with open(page, 'r') as f:
            content = f.read()
            if 'if __name__ == "__main__":' not in content:
                missing.append(page)
            elif 'main()' not in content.split('if __name__ == "__main__":')[1]:
                missing.append(page)
    
    if missing:
        print(f"❌ FALHA: {len(missing)} páginas sem chamada ao main()")
        for page in missing:
            print(f"   - {page}")
        return False
    
    print(f"✅ Main calls: {len(pages)} páginas validadas")
    return True

def validate_bare_except():
    """Valida que não há bare except nos arquivos corrigidos"""
    files = [
        "core/validators.py",
        "core/ui_components.py",
        "core/cache_manager.py",
    ]
    
    found = []
    for file in files:
        with open(file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                # Procurar por 'except:' sem tipo especificado
                stripped = line.strip()
                if stripped == 'except:':
                    found.append(f"{file}:{i}")
    
    if found:
        print(f"⚠️  AVISO: {len(found)} bare except encontrados")
        for location in found:
            print(f"   - {location}")
        return False
    
    print(f"✅ Exception handling: {len(files)} arquivos validados")
    return True

def validate_diagnostic_report():
    """Valida que o relatório foi criado"""
    report_path = Path("DIAGNOSTIC_REPORT.md")
    
    if not report_path.exists():
        print("❌ FALHA: DIAGNOSTIC_REPORT.md não encontrado")
        return False
    
    # Verificar tamanho mínimo
    size = report_path.stat().st_size
    if size < 5000:
        print(f"⚠️  AVISO: Relatório muito pequeno ({size} bytes)")
        return False
    
    print(f"✅ Relatório: {size:,} bytes")
    return True

def main():
    """Executa todas as validações"""
    print("=" * 60)
    print("🔍 VALIDAÇÃO DAS CORREÇÕES - Rockbuzz Finance")
    print("=" * 60)
    print()
    
    tests = [
        ("Nome do arquivo __init__.py", validate_init_file),
        ("Sintaxe Python", validate_syntax),
        ("Chamadas ao main()", validate_main_calls),
        ("Tratamento de exceções", validate_bare_except),
        ("Relatório de diagnóstico", validate_diagnostic_report),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ ERRO em '{name}': {e}")
            results.append(False)
        print()
    
    # Resumo
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ SUCESSO: {passed}/{total} validações passaram")
        print("=" * 60)
        return 0
    else:
        print(f"⚠️  PARCIAL: {passed}/{total} validações passaram")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
