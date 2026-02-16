# 🔧 Configuração Completa - Correção do Erro JWT Signature

## ✅ O QUE FOI CORRIGIDO

Todas as correções já foram aplicadas neste commit. Os seguintes problemas foram identificados e resolvidos:

1. **Sintaxe TOML Incorreta** ❌ → ✅ Corrigido
   - Estava usando sintaxe JSON (`"chave": valor`) em vez de TOML (`chave = valor`)

2. **Credenciais Desatualizadas** ❌ → ✅ Sincronizado
   - O `secrets.toml` tinha uma chave diferente do arquivo JSON correto
   - Agora usa as credenciais do `financasrb-ddd33bb9d63f.json`

3. **Estrutura de Diretórios** ❌ → ✅ Criado
   - Criado `.streamlit/secrets.toml` no local esperado pelo Streamlit

4. **Arquivos Sensíveis no Git** ❌ → ✅ Protegido
   - Removidos arquivos de credenciais do controle de versão
   - Atualizado `.gitignore` para prevenir commits futuros

## 🎯 O QUE VOCÊ PRECISA FAZER AGORA

### Passo 1: Verificar os Arquivos Locais

Após fazer pull destas mudanças, você deve ter:

1. **`.streamlit/secrets.toml`** - ⚠️ ESTE ARQUIVO NÃO ESTÁ NO GIT POR SEGURANÇA
   - Você precisa criar este arquivo manualmente
   - Use o conteúdo abaixo (substitua com suas credenciais reais)

2. **Arquivo JSON de credenciais** - ⚠️ TAMBÉM NÃO ESTÁ NO GIT
   - Mantenha seu arquivo `financasrb-ddd33bb9d63f.json` (ou similar)
   - Ou crie/atualize o arquivo `.streamlit/secrets.toml`

### Passo 2: Criar `.streamlit/secrets.toml`

**Opção A: Se você tem o arquivo JSON de credenciais**

```bash
# Copie o conteúdo do seu arquivo JSON para o formato TOML
# Use o exemplo abaixo como referência
```

**Opção B: Criar manualmente**

Crie o arquivo `.streamlit/secrets.toml` com o seguinte conteúdo:

```toml
# ==============================================================================
# ID DA PLANILHA DO GOOGLE SHEETS
# ==============================================================================
spreadsheet_id = "1TZDj3ZNfFluXLTlc4hkkvMb0gs17WskzwS9LapR44eI"

# ==============================================================================
# CREDENCIAIS DA SERVICE ACCOUNT DO GOOGLE CLOUD
# ==============================================================================
# ⚠️ IMPORTANTE: Use sintaxe TOML, NÃO JSON!
# CORRETO:   chave = "valor"
# INCORRETO: "chave": "valor"

[google_credentials]
type = "service_account"
project_id = "financasrb"
private_key_id = "ddd33bb9d63fa8be3c0e8278b791f5036b829335"
private_key = "-----BEGIN PRIVATE KEY-----\nSUA_CHAVE_PRIVADA_COMPLETA_AQUI\n-----END PRIVATE KEY-----\n"
client_email = "financasrb@financasrb.iam.gserviceaccount.com"
client_id = "115775122546153691615"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/financasrb%40financasrb.iam.gserviceaccount.com"
universe_domain = "googleapis.com"

[passwords]
admin = "seu_hash_aqui"
```

**⚠️ ATENÇÃO**: Substitua `SUA_CHAVE_PRIVADA_COMPLETA_AQUI` pela chave privada completa do seu arquivo JSON.

### Passo 3: Verificar as Credenciais

Execute o script de teste para verificar se tudo está funcionando:

```bash
python3 test_auth.py
```

**Resultado esperado:**
```
================================================================================
TESTE DE AUTENTICAÇÃO GOOGLE SHEETS
================================================================================

✓ Arquivo de credenciais encontrado
✓ Arquivo JSON carregado com sucesso
✓ Todos os campos obrigatórios presentes
✓ Credenciais criadas com sucesso
✓ Cliente autorizado com sucesso
✓ Planilha aberta com sucesso
✓ X aba(s) encontrada(s)

================================================================================
✅ TESTE CONCLUÍDO COM SUCESSO!
================================================================================
```

### Passo 4: Verificar Permissões da Planilha

Certifique-se de que a planilha está compartilhada com a Service Account:

1. Abra sua planilha no Google Sheets
2. Clique em "Compartilhar"
3. Adicione o email: `financasrb@financasrb.iam.gserviceaccount.com`
4. Dê permissão de "Editor"
5. Salve

### Passo 5: Iniciar a Aplicação

```bash
streamlit run app.py
```

## 🔍 TROUBLESHOOTING

### Erro: "Credenciais não configuradas"

**Causa:** O arquivo `.streamlit/secrets.toml` não foi criado.

**Solução:** Siga o Passo 2 acima.

### Erro: "Invalid JWT Signature"

**Causa:** A chave privada no `secrets.toml` está incorreta ou incompleta.

**Soluções:**
1. Verifique se a `private_key` está completa (inclui BEGIN e END)
2. Verifique se os `\n` estão presentes (quebras de linha)
3. Compare com o arquivo JSON original
4. Se necessário, gere uma nova chave no Google Cloud Console

### Erro: "PERMISSION_DENIED"

**Causa:** A planilha não está compartilhada com a Service Account.

**Solução:** Siga o Passo 4 acima.

### Erro: Sintaxe TOML inválida

**Causa:** Você pode ter usado sintaxe JSON no arquivo TOML.

**Solução:** 
```toml
# ❌ ERRADO (sintaxe JSON)
[google_credentials]
  "type": "service_account",
  "project_id": "financasrb",

# ✅ CORRETO (sintaxe TOML)
[google_credentials]
type = "service_account"
project_id = "financasrb"
```

## 📚 DOCUMENTAÇÃO ADICIONAL

- `docs/SETUP_GOOGLE_SHEETS.md` - Guia completo de configuração
- `docs/JWT_SIGNATURE_FIX.md` - Detalhes da correção aplicada
- `secrets.toml.example` - Exemplo de arquivo de configuração

## 🔐 SEGURANÇA

**IMPORTANTE:** Nunca faça commit dos seguintes arquivos:
- `.streamlit/secrets.toml`
- `secrets.toml`
- `financasrb-*.json`
- `google_credentials.json`

Estes arquivos já estão no `.gitignore` para sua proteção.

## ✅ RESUMO

| Item | Status |
|------|--------|
| Sintaxe TOML corrigida | ✅ Feito |
| Credenciais sincronizadas | ✅ Feito |
| .streamlit/secrets.toml criado | ⚠️ Você precisa criar |
| Arquivos sensíveis protegidos | ✅ Feito |
| Documentação atualizada | ✅ Feito |
| Script de teste criado | ✅ Feito |

## 🎉 PRÓXIMOS PASSOS

1. ✅ Pull este commit
2. ⚠️ Crie `.streamlit/secrets.toml` com suas credenciais
3. ✅ Execute `python3 test_auth.py`
4. ✅ Verifique permissões da planilha
5. ✅ Execute `streamlit run app.py`
6. ✅ Tudo funcionando!

---

**Dúvidas?** Consulte `docs/SETUP_GOOGLE_SHEETS.md` ou `docs/JWT_SIGNATURE_FIX.md`
