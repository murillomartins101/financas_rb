# Guia de Solução de Problemas (Troubleshooting)

## KeyError: 'initialize' ou outros erros relacionados a st.secrets

### Problema
Ao executar a aplicação, você recebe um erro como:
```
KeyError: 'initialize'
```
ou
```
KeyError: [alguma_chave]
```
relacionado a `st.secrets`.

### Causas Possíveis

1. **Arquivo secrets.toml não existe ou está no local errado**
   - O arquivo deve estar em `.streamlit/secrets.toml`
   - Não na raiz do projeto, mas dentro da pasta `.streamlit`

2. **Arquivo secrets.toml mal formatado**
   - Sintaxe TOML incorreta
   - Aspas não fechadas
   - Seções mal definidas

3. **Cache do Streamlit corrompido**
   - Dados em cache antigos causando problemas

### Soluções

#### Solução 1: Criar/Verificar o arquivo secrets.toml

1. Crie a pasta `.streamlit` se não existir:
   ```bash
   mkdir -p .streamlit
   ```

2. Copie o arquivo de exemplo:
   ```bash
   cp secrets.toml.example .streamlit/secrets.toml
   ```

3. Edite `.streamlit/secrets.toml` com suas credenciais reais

4. Verifique a estrutura do arquivo:
   ```toml
   # ID da planilha
   spreadsheet_id = "seu_id_aqui"
   
   # Credenciais do Google
   [google_credentials]
   type = "service_account"
   project_id = "seu-projeto"
   private_key_id = "sua-chave-id"
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "email@projeto.iam.gserviceaccount.com"
   client_id = "123456789"
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
   ```

#### Solução 2: Limpar o cache do Streamlit

Execute no terminal:
```bash
streamlit cache clear
```

Ou adicione a flag `--clear-cache` ao executar:
```bash
streamlit run app.py --clear-cache
```

#### Solução 3: Usar arquivo JSON local (alternativa ao secrets.toml)

Se você tem dificuldades com o secrets.toml, pode usar um arquivo JSON:

1. Coloque suas credenciais do Google em `google_credentials.json` na raiz do projeto
2. Configure a variável de ambiente para o spreadsheet_id:
   ```bash
   export SPREADSHEET_ID="seu_id_aqui"
   ```

#### Solução 4: Verificar a versão do Streamlit

Certifique-se de estar usando uma versão compatível:
```bash
streamlit --version
```

Deve ser >= 1.32. Se não for, atualize:
```bash
pip install --upgrade streamlit
```

#### Solução 5: Verificar permissões de arquivo

No Windows:
```powershell
icacls .streamlit\secrets.toml
```

No Linux/Mac:
```bash
ls -la .streamlit/secrets.toml
```

O arquivo deve ser legível pelo usuário atual.

### Executando sem Google Sheets (apenas Excel local)

Se você não quer configurar Google Sheets agora, a aplicação pode funcionar apenas com o arquivo Excel local:

1. Certifique-se de que o arquivo `data/Financas_RB.xlsx` existe
2. Crie um `.streamlit/secrets.toml` mínimo:
   ```toml
   # Arquivo vazio ou com configurações mínimas
   ```
3. A aplicação automaticamente usará o Excel como fallback

### Outros Erros Comuns

#### ImportError ou ModuleNotFoundError

**Problema**: Módulos Python não encontrados

**Solução**:
```bash
pip install -r requirements.txt
```

#### PermissionError ao acessar arquivos

**Problema**: Sem permissão para ler/escrever arquivos

**Solução**:
- No Windows: Execute o prompt como administrador
- No Linux/Mac: Verifique as permissões com `chmod`

#### Erro de conexão com Google Sheets

**Problema**: Não consegue conectar ao Google Sheets

**Solução**:
1. Verifique se as APIs estão habilitadas no Google Cloud Console
2. Verifique se a planilha foi compartilhada com o email da service account
3. Verifique sua conexão com a internet

### Ainda com problemas?

1. Execute a aplicação em modo verbose para ver logs detalhados:
   ```bash
   streamlit run app.py --logger.level=debug
   ```

2. Verifique os logs de inicialização no console

3. Abra uma issue no repositório com:
   - Versão do Streamlit (`streamlit --version`)
   - Versão do Python (`python --version`)
   - Sistema operacional
   - Mensagem de erro completa
   - Estrutura do seu arquivo secrets.toml (SEM as credenciais reais)

### Suporte Adicional

- Consulte a documentação do Streamlit: https://docs.streamlit.io/
- Guia de configuração do Google Sheets: `docs/SETUP_GOOGLE_SHEETS.md`
- Documentação de mudanças: `docs/CHANGES.md`
