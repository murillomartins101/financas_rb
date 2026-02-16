# Configuração do Streamlit

Este diretório contém as configurações do Streamlit para a aplicação Rockbuzz Finance.

## Arquivos

### 📄 secrets.toml (NÃO INCLUÍDO NO GIT)

Este arquivo contém **credenciais sensíveis** e **NUNCA** deve ser commitado no Git.

**Para configurar:**

1. Copie o arquivo de exemplo:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

2. Edite o arquivo `.streamlit/secrets.toml` e preencha com suas credenciais reais:
   - ID da planilha do Google Sheets
   - Credenciais da Service Account do Google Cloud
   - Chave secreta para JWT

3. Siga o tutorial completo em: [`docs/SETUP_GOOGLE_SHEETS.md`](../docs/SETUP_GOOGLE_SHEETS.md)

### 📄 secrets.toml.example

Arquivo de **exemplo** que mostra a estrutura necessária do `secrets.toml`.

- ✅ Este arquivo PODE ser commitado (não contém credenciais reais)
- ✅ Use como referência para criar seu `secrets.toml`
- ✅ Contém comentários explicativos para cada campo

### 📄 config.toml

Configurações gerais do Streamlit (tema, servidor, etc).

- ✅ Este arquivo PODE ser commitado
- ✅ Contém apenas configurações não-sensíveis
- ✅ Personalize conforme necessário

## Como Obter as Credenciais

### Opção 1: Google Cloud Service Account (Recomendado)

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto
3. Habilite as APIs:
   - Google Sheets API
   - Google Drive API
4. Crie uma Service Account
5. Baixe o arquivo JSON de credenciais
6. Copie os valores para `.streamlit/secrets.toml`
7. Compartilhe a planilha com o email da Service Account

**Tutorial detalhado:** [`docs/SETUP_GOOGLE_SHEETS.md`](../docs/SETUP_GOOGLE_SHEETS.md)

### Opção 2: Arquivo JSON Local

Alternativamente, você pode usar um arquivo JSON local:

1. Coloque o arquivo de credenciais do Google Cloud como `google_credentials.json` na raiz do projeto
2. Configure o `spreadsheet_id` via variável de ambiente:
   ```bash
   export SPREADSHEET_ID="seu_id_aqui"
   ```

**Nota:** O arquivo `google_credentials.json` já está no `.gitignore` e não será commitado.

## Modo Desenvolvimento (Sem Google Sheets)

Se você quer apenas testar o app localmente sem configurar Google Sheets:

1. Crie um arquivo vazio `.streamlit/secrets.toml`:
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
- Chaves privadas
- Tokens de autenticação
- Senhas ou secrets

O arquivo `.gitignore` já está configurado para ignorar:
- `.streamlit/secrets.toml`
- `google_credentials.json`
- Outros arquivos sensíveis

## Troubleshooting

Se você está tendo problemas com credenciais:

1. **Erro "Nenhuma fonte de credenciais encontrada"**
   - Verifique se criou o arquivo `.streamlit/secrets.toml`
   - Ou se criou o arquivo `google_credentials.json` na raiz

2. **Erro "Campos obrigatórios ausentes"**
   - Compare seu arquivo com `.streamlit/secrets.toml.example`
   - Certifique-se de que todos os campos estão preenchidos

3. **Erro "PERMISSION_DENIED"**
   - Compartilhe a planilha com o email da Service Account
   - Dê permissão de "Editor"

**Guia completo:** [`docs/TROUBLESHOOTING.md`](../docs/TROUBLESHOOTING.md)

## Recursos Adicionais

- 📚 [Documentação do Streamlit](https://docs.streamlit.io/)
- 🔐 [Gerenciamento de Secrets no Streamlit](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
- ☁️ [Google Sheets API](https://developers.google.com/sheets/api)
- 🔑 [Service Accounts - Google Cloud](https://cloud.google.com/iam/docs/service-accounts)
