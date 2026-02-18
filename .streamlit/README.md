# Configuração do Streamlit

Este diretório contém as configurações do Streamlit para a aplicação Rockbuzz Finance.

## Arquivos

### 📄 secrets.toml (NÃO INCLUÍDO NO GIT)

Este arquivo contém **credenciais sensíveis** e **NUNCA** deve ser commitado no Git.

**Para configurar localmente:**

1. Copie o arquivo de exemplo:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. Edite o arquivo `.streamlit/secrets.toml` e preencha com suas credenciais reais:
   - ID da planilha do Google Sheets (`spreadsheet_id`)
   - Credenciais completas da Service Account (`[google_credentials]`)
   - Chave secreta para JWT (`[jwt]`)

3. Siga o tutorial completo em: [`docs/SETUP_GOOGLE_SHEETS.md`](../docs/SETUP_GOOGLE_SHEETS.md)

**Para configurar no Streamlit Cloud:**

1. Faça deploy do seu app no Streamlit Cloud
2. Vá em **Settings** → **Secrets** do seu app
3. Copie **TODO** o conteúdo do seu arquivo `.streamlit/secrets.toml` local (já preenchido)
4. Cole no campo de Secrets (mantenha a mesma estrutura TOML)
5. Clique em **Save**
6. O app será redeployed automaticamente com as novas credenciais

⚠️ **IMPORTANTE**: O Streamlit Cloud lê secrets via `st.secrets` automaticamente. Não é necessário criar arquivo físico na nuvem.

### 📄 secrets.toml.example

Arquivo de **exemplo** que mostra a estrutura necessária do `secrets.toml`.

- ✅ Este arquivo PODE ser commitado (não contém credenciais reais)
- ✅ Use como referência para criar seu `secrets.toml`
- ✅ Contém comentários explicativos para cada campo
- ✅ Inclui checklist de verificação e troubleshooting

### 📄 config.toml

Configurações gerais do Streamlit (tema, servidor, etc).

- ✅ Este arquivo PODE ser commitado
- ✅ Contém apenas configurações não-sensíveis
- ✅ Personalize conforme necessário

## Como Obter as Credenciais

### Passo a Passo Rápido

1. **Criar projeto no Google Cloud**
   - Acesse [Google Cloud Console](https://console.cloud.google.com/)
   - Crie um novo projeto

2. **Habilitar APIs necessárias**
   - Google Sheets API
   - Google Drive API

3. **Criar Service Account**
   - Vá em "APIs & Services" → "Credentials"
   - Create Credentials → Service Account
   - Baixe o arquivo JSON de credenciais

4. **Configurar o secrets.toml**
   - Copie os valores do JSON para `.streamlit/secrets.toml`
   - Adicione o `spreadsheet_id` da sua planilha

5. **Compartilhar planilha**
   - Abra sua planilha no Google Sheets
   - Compartilhe com o email da Service Account (encontrado no `client_email`)
   - Dê permissão de **Editor**

**Tutorial detalhado:** [`docs/SETUP_GOOGLE_SHEETS.md`](../docs/SETUP_GOOGLE_SHEETS.md)

## Verificando a Configuração

Depois de configurar, você pode verificar se está tudo correto:

### ✅ Checklist de Verificação

- [ ] Arquivo `.streamlit/secrets.toml` existe (não commitado)
- [ ] Campo `spreadsheet_id` preenchido
- [ ] Seção `[google_credentials]` com todos os campos
- [ ] `private_key` completo (com BEGIN e END)
- [ ] Planilha compartilhada com `client_email`
- [ ] APIs habilitadas no Google Cloud

### 🧪 Testar a Conexão

1. Execute o app: `streamlit run app.py`
2. O app deve conectar automaticamente ao Google Sheets
3. Se houver erros, verifique os logs no terminal
4. Consulte [`docs/TROUBLESHOOTING.md`](../docs/TROUBLESHOOTING.md) para problemas comuns

## Deployment no Streamlit Cloud

### 📤 Primeira vez fazendo deploy

1. Faça push do código para GitHub (SEM o secrets.toml)
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte seu repositório GitHub
4. Configure o app:
   - **Repository**: seu repositório
   - **Branch**: main/master
   - **Main file**: app.py

5. **Configure os Secrets**:
   - Clique em **Advanced settings**
   - Na aba **Secrets**, cole o conteúdo do seu `.streamlit/secrets.toml`
   - Mantenha EXATAMENTE a mesma estrutura TOML
   - Clique em **Save**

6. Clique em **Deploy**

### 🔄 Atualizando Secrets no Streamlit Cloud

Se você precisar atualizar as credenciais:

1. Acesse seu app em share.streamlit.io
2. Clique em **Settings** → **Secrets**
3. Edite o conteúdo
4. Clique em **Save**
5. O app será redeployed automaticamente

### 🔍 Diagnosticando Problemas no Streamlit Cloud

Se o app não conectar ao Google Sheets no Streamlit Cloud:

1. **Verifique os logs**:
   - Clique nos três pontinhos (...) → **Manage app** → **Logs**
   - Procure por mensagens de erro de autenticação

2. **Erros comuns**:
   - **"google_credentials not found"**: Você não configurou a seção [google_credentials] nos Secrets
   - **"spreadsheet_id not found"**: Falta o campo spreadsheet_id no início dos Secrets
   - **"PERMISSION_DENIED"**: A planilha não está compartilhada com o client_email
   - **"invalid_grant"**: As credenciais estão corrompidas ou revogadas

3. **Formato dos Secrets**:
   ```toml
   # Deve ser EXATAMENTE assim:
   spreadsheet_id = "seu_id_aqui"
   
   [google_credentials]
   type = "service_account"
   project_id = "..."
   # ... outros campos
   ```

## Modo Desenvolvimento (Sem Google Sheets)

Se você quer apenas testar o app localmente sem configurar Google Sheets:

1. Crie um arquivo mínimo `.streamlit/secrets.toml`:
   ```bash
   touch .streamlit/secrets.toml
   ```

2. A aplicação usará automaticamente o arquivo Excel local (`data/Financas_RB.xlsx`) como fallback

**Limitações do modo desenvolvimento:**
- ❌ Não sincroniza dados com Google Sheets
- ❌ Múltiplos usuários não compartilham dados
- ✅ Funciona para testes locais
- ✅ Todas as funcionalidades básicas funcionam

## Segurança

⚠️ **IMPORTANTE:** Nunca compartilhe ou faça commit de arquivos contendo:
- Credenciais do Google Cloud
- IDs de projetos sensíveis
- Chaves privadas (private_key)
- Tokens de autenticação
- Senhas ou secrets

O arquivo `.gitignore` já está configurado para ignorar:
- `.streamlit/secrets.toml`
- `google_credentials.json`
- Outros arquivos sensíveis

**NUNCA**:
- ❌ Faça commit do secrets.toml
- ❌ Compartilhe credenciais em issues/PRs
- ❌ Cole credenciais em mensagens públicas
- ❌ Deixe credenciais em código

**SEMPRE**:
- ✅ Use secrets.toml ou variáveis de ambiente
- ✅ Mantenha credenciais fora do controle de versão
- ✅ Revogue e regere credenciais se houver vazamento
- ✅ Use permissões mínimas necessárias na Service Account

## Troubleshooting

### ❌ Erro: "Credenciais não configuradas"

**Causa**: O arquivo `.streamlit/secrets.toml` não existe ou está vazio

**Solução**:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edite o arquivo e preencha com suas credenciais
```

### ❌ Erro: "secrets.toml existe mas não contém [google_credentials]"

**Causa**: O arquivo existe mas falta a seção de credenciais

**Solução**:
1. Abra `.streamlit/secrets.toml`
2. Certifique-se de ter a seção completa `[google_credentials]`
3. Compare com `.streamlit/secrets.toml.example`

### ❌ Erro: "Campos obrigatórios ausentes"

**Causa**: Faltam campos na seção `[google_credentials]`

**Solução**:
1. Baixe o JSON de credenciais do Google Cloud Console
2. Copie TODOS os campos do JSON para o secrets.toml
3. Não deixe nenhum campo vazio ou com valores de exemplo

### ❌ Erro: "private_key com formato inválido"

**Causa**: A chave privada não está completa ou formatada incorretamente

**Solução**:
- Certifique-se que a chave começa com `-----BEGIN PRIVATE KEY-----`
- E termina com `-----END PRIVATE KEY-----`
- Use aspas triplas (""") para melhor legibilidade:
  ```toml
  private_key = """-----BEGIN PRIVATE KEY-----
  MIIEvQIB...
  -----END PRIVATE KEY-----
  """
  ```

### ❌ Erro: "PERMISSION_DENIED" ou "Planilha não encontrada"

**Causa**: A planilha não está compartilhada com a Service Account

**Solução**:
1. Abra a planilha no Google Sheets
2. Clique em "Compartilhar"
3. Adicione o email da Service Account (o valor de `client_email` nas credenciais)
4. Dê permissão de **Editor** (não apenas Visualizador)
5. Clique em "Enviar"

### ❌ Erro: "invalid_grant" ou "invalid jwt signature"

**Causa**: As credenciais foram revogadas ou estão corrompidas

**Solução**:
1. Acesse o Google Cloud Console
2. Verifique se a Service Account ainda existe
3. Gere uma nova chave JSON
4. Atualize o secrets.toml com as novas credenciais

## Recursos Adicionais

- 📚 [Documentação do Streamlit](https://docs.streamlit.io/)
- 🔐 [Gerenciamento de Secrets no Streamlit Cloud](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- ☁️ [Google Sheets API](https://developers.google.com/sheets/api)
- 🔑 [Service Accounts - Google Cloud](https://cloud.google.com/iam/docs/service-accounts)
- 📖 [Tutorial Completo - Setup](../docs/SETUP_GOOGLE_SHEETS.md)
- 🔧 [Guia de Troubleshooting](../docs/TROUBLESHOOTING.md)
