# Guia de Configuração - Google Sheets

Este guia descreve como configurar a conexão do Rockbuzz Finance com o Google Sheets.

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Criar Service Account no Google Cloud](#criar-service-account)
3. [Configurar Credenciais](#configurar-credenciais)
4. [Configurar Planilha](#configurar-planilha)
5. [Testar Conexão](#testar-conexão)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Pré-requisitos

Antes de começar, você precisa:

- Uma conta do Google (Gmail)
- Acesso ao [Google Cloud Console](https://console.cloud.google.com/)
- Uma planilha do Google Sheets criada (pode usar a template do projeto)
- Permissões de administrador no projeto

---

## 🔐 Criar Service Account

### Passo 1: Criar Projeto no Google Cloud

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Clique em **"Select a project"** → **"New Project"**
3. Nome do projeto: `rockbuzz-finance` (ou nome de sua preferência)
4. Clique em **"Create"**
5. Aguarde a criação do projeto e selecione-o

### Passo 2: Habilitar APIs Necessárias

1. No menu lateral, vá em **"APIs & Services"** → **"Library"**
2. Procure por **"Google Sheets API"**
   - Clique no resultado
   - Clique em **"Enable"**
3. Procure por **"Google Drive API"**
   - Clique no resultado
   - Clique em **"Enable"**

### Passo 3: Criar Service Account

1. No menu lateral, vá em **"APIs & Services"** → **"Credentials"**
2. Clique em **"Create Credentials"** → **"Service Account"**
3. Preencha os dados:
   - **Service account name**: `rockbuzz-finance-sa`
   - **Service account ID**: será gerado automaticamente
   - **Description**: `Service account para acesso ao Google Sheets`
4. Clique em **"Create and Continue"**
5. Em **"Grant this service account access to project"**:
   - Role: **Editor** (ou **Viewer** se quiser apenas leitura)
   - Clique em **"Continue"**
6. Clique em **"Done"**

### Passo 4: Criar Chave JSON

1. Na lista de Service Accounts, clique na que você acabou de criar
2. Vá na aba **"Keys"**
3. Clique em **"Add Key"** → **"Create new key"**
4. Selecione **"JSON"**
5. Clique em **"Create"**
6. Um arquivo JSON será baixado automaticamente - **guarde este arquivo com segurança!**

---

## ⚙️ Configurar Credenciais

Você tem duas opções para configurar as credenciais:

### Opção 1: Arquivo JSON Local (Recomendado para Desenvolvimento)

1. Renomeie o arquivo JSON baixado para `google_credentials.json`
2. Coloque o arquivo na **raiz do projeto** (mesmo diretório do `app.py`)
3. ⚠️ **IMPORTANTE**: Este arquivo contém credenciais sensíveis! Certifique-se de que ele está no `.gitignore`

### Opção 2: secrets.toml (Recomendado para Produção/Streamlit Cloud)

1. Crie o diretório `.streamlit` na raiz do projeto (se não existir):
   ```bash
   mkdir .streamlit
   ```

2. Copie o arquivo de exemplo:
   ```bash
   cp secrets.toml.example .streamlit/secrets.toml
   ```

3. Abra o arquivo JSON das credenciais e copie os valores para `.streamlit/secrets.toml`:
   
   ```toml
   spreadsheet_id = "SEU_SPREADSHEET_ID"
   
   [google_credentials]
   type = "service_account"
   project_id = "valor do JSON"
   private_key_id = "valor do JSON"
   private_key = "valor do JSON (incluindo \\n)"
   client_email = "valor do JSON"
   client_id = "valor do JSON"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "valor do JSON"
   ```

4. ⚠️ **IMPORTANTE**: O campo `private_key` deve manter as quebras de linha (`\n`)

---

## 📊 Configurar Planilha

### Passo 1: Obter ID da Planilha

1. Abra sua planilha do Google Sheets
2. Copie o ID da URL:
   ```
   https://docs.google.com/spreadsheets/d/SEU_SPREADSHEET_ID_AQUI/edit
                                         ^^^^^^^^^^^^^^^^^^^^^
   ```
3. Cole este ID no campo `spreadsheet_id` do seu `secrets.toml` ou configure como variável de ambiente

### Passo 2: Compartilhar Planilha com Service Account

Este é o passo **MAIS IMPORTANTE**! 🔥

1. Na sua planilha do Google Sheets, clique em **"Share"** (Compartilhar)
2. No campo de email, cole o **client_email** da sua Service Account
   - Você encontra este email no arquivo JSON das credenciais
   - Formato: `nome@projeto-id.iam.gserviceaccount.com`
3. Selecione permissão: **"Editor"**
4. **DESMARQUE** a opção "Notify people" (não é necessário enviar email)
5. Clique em **"Share"** (Compartilhar)

⚠️ **Sem este passo, você receberá erro "PERMISSION_DENIED"!**

### Passo 3: Verificar Estrutura das Abas

Certifique-se de que sua planilha tem as seguintes abas com a estrutura correta:

1. **shows**
   - Colunas: show_id, data_show, casa, cidade, status, publico, cache_acordado, observacao

2. **transactions**
   - Colunas: id, data, tipo, categoria, subcategoria, descricao, valor, show_id, payment_status, conta

3. **payout_rules**
   - Colunas: rule_id, nome_regra, modelo, pct_caixa, pct_musicos, ativa, vigencia_inicio, vigencia_fim

4. **show_payout_config**
   - Colunas: show_id, rule_id

5. **members**
   - Colunas: member_id, nome, ativo

6. **member_shares**
   - Colunas: share_id, rule_id, member_id, tipo, peso ou valor_fixo

---

## ✅ Testar Conexão

### Via Interface do Sistema

1. Inicie o aplicativo:
   ```bash
   streamlit run app.py
   ```

2. Faça login no sistema

3. No sidebar, procure a seção **"Conexão"**

4. Clique no botão **"🔄 Testar Conexão"**

5. Verifique o resultado:
   - ✅ **Sucesso**: Conexão estabelecida, mostra número de abas
   - ❌ **Erro**: Veja a mensagem de erro e siga as sugestões

### Via Python (Teste Manual)

Crie um arquivo `test_connection.py`:

```python
from core.google_cloud import google_cloud_manager

# Tentar inicializar
success = google_cloud_manager.initialize(show_messages=True)

if success:
    print("✅ Conexão estabelecida com sucesso!")
    
    # Testar acesso
    test = google_cloud_manager.test_connection_live()
    print(f"Planilha: {google_cloud_manager.spreadsheet.title}")
    print(f"Abas: {test['worksheets']}")
else:
    print("❌ Falha na conexão")
    status = google_cloud_manager.get_connection_status()
    print(f"Erro: {status['error']}")
    print(f"Sugestão: {status['suggestion']}")
```

Execute:
```bash
streamlit run test_connection.py
```

---

## 🌐 Deployment no Streamlit Cloud

Após configurar as credenciais localmente, você pode fazer deploy do app no Streamlit Cloud.

### Pré-requisitos

- Código da aplicação em um repositório GitHub (público ou privado)
- Arquivo `.streamlit/secrets.toml` configurado localmente (NÃO commitado)
- Credenciais da Service Account funcionando localmente

### Passo 1: Preparar o Repositório

1. Certifique-se de que o arquivo `secrets.toml` **NÃO** está commitado:
   ```bash
   git status
   # secrets.toml NÃO deve aparecer na lista
   ```

2. Verifique se o `.gitignore` contém:
   ```
   .streamlit/secrets.toml
   google_credentials.json
   ```

3. Faça push do código para GitHub:
   ```bash
   git push origin main
   ```

### Passo 2: Fazer Deploy no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io)

2. Faça login com sua conta GitHub

3. Clique em **"New app"**

4. Configure o app:
   - **Repository**: Selecione seu repositório
   - **Branch**: main (ou a branch que você usa)
   - **Main file path**: app.py

5. Clique em **"Advanced settings"**

### Passo 3: Configurar Secrets no Streamlit Cloud

Esta é a parte **MAIS IMPORTANTE** do deployment! 🔥

1. Na seção **Advanced settings**, vá para a aba **"Secrets"**

2. Abra o arquivo `.streamlit/secrets.toml` local (o que você configurou)

3. Copie **TODO** o conteúdo do arquivo

4. Cole no campo de texto do Streamlit Cloud

5. **IMPORTANTE**: Mantenha a **MESMA ESTRUTURA TOML**:
   ```toml
   # Deve estar exatamente assim:
   spreadsheet_id = "seu_id_aqui"
   
   [google_credentials]
   type = "service_account"
   project_id = "..."
   private_key_id = "..."
   private_key = """-----BEGIN PRIVATE KEY-----
   ...
   -----END PRIVATE KEY-----
   """
   client_email = "..."
   # ... outros campos
   
   [jwt]
   secret_key = "..."
   # ... outros campos
   ```

6. Clique em **"Save"**

7. Clique em **"Deploy!"**

### Passo 4: Verificar o Deploy

1. Aguarde o build completar (2-5 minutos)

2. O app será aberto automaticamente

3. Teste a conexão com Google Sheets

4. Se houver erros, veja os logs:
   - Clique nos três pontinhos (...) → **"Manage app"** → **"Logs"**

### Atualizando Secrets no Streamlit Cloud

Se você precisar atualizar as credenciais depois do deploy:

1. Acesse seu app em share.streamlit.io

2. Clique em **Settings** → **Secrets**

3. Edite o conteúdo

4. Clique em **"Save"**

5. O app será redeployed automaticamente

### Troubleshooting no Streamlit Cloud

#### ❌ Erro: "google_credentials not found"

**Causa**: A seção `[google_credentials]` não está nos Secrets

**Solução**:
1. Acesse Settings → Secrets
2. Certifique-se de ter a linha `[google_credentials]`
3. E todos os campos abaixo dela
4. Salve e aguarde o redeploy

#### ❌ Erro: "spreadsheet_id not found"

**Causa**: Falta o campo `spreadsheet_id` no início dos Secrets

**Solução**:
1. Acesse Settings → Secrets
2. Adicione no INÍCIO (antes de qualquer `[]`):
   ```toml
   spreadsheet_id = "seu_id_aqui"
   ```
3. Salve e aguarde o redeploy

#### ❌ Erro: "PERMISSION_DENIED"

**Causa**: A planilha não está compartilhada com a Service Account

**Solução**:
1. A planilha deve ser compartilhada mesmo quando o app está na nuvem
2. Compartilhe com o `client_email` da Service Account
3. Dê permissão de "Editor"

#### ❌ Erro: "Invalid TOML format"

**Causa**: Os Secrets no Streamlit Cloud têm erro de sintaxe TOML

**Solução**:
1. Verifique se todas as aspas estão fechadas
2. Verifique se o `private_key` está com aspas triplas (""")
3. Não deixe campos vazios
4. Copie novamente do seu `secrets.toml` local que funciona

#### 📋 Ver Logs de Erro

Para diagnosticar problemas no Streamlit Cloud:

1. Clique nos três pontinhos (...) no canto superior direito
2. Selecione **"Manage app"**
3. Clique na aba **"Logs"**
4. Procure por mensagens de erro relacionadas a credenciais
5. Use os logs para identificar qual campo está faltando ou incorreto

### Diferenças: Local vs Streamlit Cloud

| Aspecto | Local | Streamlit Cloud |
|---------|-------|-----------------|
| Arquivo de config | `.streamlit/secrets.toml` | Settings → Secrets (interface web) |
| Como é lido | `st.secrets` lê arquivo local | `st.secrets` lê do banco do Streamlit Cloud |
| Formato | Arquivo TOML | String TOML (mesmo formato) |
| Atualização | Editar arquivo e reiniciar app | Salvar Secrets (redeploy automático) |
| Segurança | Protegido pelo `.gitignore` | Criptografado pelo Streamlit Cloud |

### Boas Práticas para Streamlit Cloud

✅ **Faça**:
- Teste as credenciais localmente primeiro
- Copie exatamente o conteúdo do `secrets.toml` local
- Mantenha uma cópia segura das credenciais
- Use senhas fortes no campo `jwt.secret_key`

❌ **Não faça**:
- Commitar o `secrets.toml` no Git
- Compartilhar os Secrets publicamente
- Usar credenciais de produção em apps de teste

---

## 🔧 Troubleshooting

### Erro: "Credenciais do Google Cloud não configuradas"

**Causa**: O sistema não encontrou nenhum arquivo de credenciais.

**Solução**:
1. Verifique se existe `google_credentials.json` na raiz do projeto OU
2. Verifique se existe `.streamlit/secrets.toml` com as credenciais OU
3. Configure a variável de ambiente `GOOGLE_CREDENTIALS_JSON`

### Erro: "Campos obrigatórios ausentes"

**Causa**: O arquivo de credenciais está incompleto.

**Solução**:
1. Compare seu arquivo com o `secrets.toml.example`
2. Certifique-se de que todos os campos obrigatórios estão preenchidos
3. Baixe novamente o arquivo JSON do Google Cloud se necessário

### Erro: "Credenciais inválidas" ou "private_key com formato inválido"

**Causa**: O campo `private_key` não está formatado corretamente.

**Solução**:
1. O campo deve começar com `-----BEGIN PRIVATE KEY-----`
2. Deve incluir as quebras de linha (`\n`)
3. No TOML, use aspas triplas se necessário:
   ```toml
   private_key = """-----BEGIN PRIVATE KEY-----
   MIIEvQIBADANBgkqhkiG9w0BAQEFAASC...
   -----END PRIVATE KEY-----
   """
   ```

### Erro: "PERMISSION_DENIED" ou "Permissão negada"

**Causa**: A planilha não foi compartilhada com a Service Account.

**Solução**:
1. Abra a planilha no Google Sheets
2. Clique em "Compartilhar"
3. Adicione o `client_email` da Service Account
4. Dê permissão de "Editor"
5. Aguarde alguns segundos e teste novamente

### Erro: "Planilha não encontrada" ou "SpreadsheetNotFound"

**Causa**: O `spreadsheet_id` está incorreto ou a planilha foi deletada.

**Solução**:
1. Verifique o ID na URL da planilha
2. Certifique-se de copiar apenas o ID (sem outros caracteres)
3. Verifique se a planilha ainda existe
4. Verifique se você está logado na conta Google correta

### Erro: "client_email inválido"

**Causa**: O formato do email da Service Account está errado.

**Solução**:
1. O email deve terminar com `.iam.gserviceaccount.com`
2. Copie exatamente como aparece no JSON das credenciais
3. Não adicione espaços ou caracteres extras

### Erro: "spreadsheet_id muito curto"

**Causa**: O ID da planilha está incompleto.

**Solução**:
1. IDs válidos têm aproximadamente 44 caracteres
2. Verifique se copiou o ID completo da URL
3. Não inclua `/edit` ou outros parâmetros, apenas o ID

### APIs não habilitadas

**Causa**: As APIs do Google Sheets ou Drive não estão ativadas.

**Solução**:
1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Selecione seu projeto
3. Vá em "APIs & Services" → "Library"
4. Procure e habilite:
   - Google Sheets API
   - Google Drive API

### Timeout ou erro de rede

**Causa**: Problema de conectividade ou firewall.

**Solução**:
1. Verifique sua conexão com a internet
2. Tente novamente (o sistema tem retry automático)
3. Verifique se seu firewall não está bloqueando googleapis.com
4. Em ambientes corporativos, pode ser necessário configurar proxy

---

## 📚 Recursos Adicionais

- [Documentação Google Sheets API](https://developers.google.com/sheets/api)
- [Documentação gspread](https://docs.gspread.org/)
- [Service Accounts - Google Cloud](https://cloud.google.com/iam/docs/service-accounts)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)

---

## 🆘 Suporte

Se você seguiu todos os passos e ainda está com problemas:

1. Clique em "🔄 Testar Conexão" no sidebar
2. Expanda "🔍 Ver logs de diagnóstico"
3. Copie os logs e procure ajuda com essas informações
4. Verifique o arquivo `secrets.toml.example` para garantir que não está faltando nenhum campo

---

## ✅ Checklist de Configuração

Use este checklist para garantir que tudo foi configurado corretamente:

- [ ] Projeto criado no Google Cloud Console
- [ ] Google Sheets API habilitada
- [ ] Google Drive API habilitada
- [ ] Service Account criada
- [ ] Arquivo JSON de credenciais baixado
- [ ] Credenciais configuradas no sistema (JSON local ou secrets.toml)
- [ ] Planilha do Google Sheets criada
- [ ] ID da planilha copiado e configurado
- [ ] Planilha compartilhada com o client_email da Service Account
- [ ] Permissão "Editor" concedida
- [ ] Estrutura das abas criada corretamente
- [ ] Teste de conexão realizado com sucesso

Se todos os itens estão marcados, sua integração está completa! 🎉
