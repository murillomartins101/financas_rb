# Diretório .streamlit

Este diretório contém arquivos de configuração para a aplicação Streamlit.

## Arquivos

### secrets.toml (OBRIGATÓRIO)

Este arquivo contém credenciais sensíveis e **NÃO deve ser commitado** no repositório (já está no `.gitignore`).

**Para criar este arquivo:**

```bash
# Na raiz do projeto, execute:
cp secrets.toml.example .streamlit/secrets.toml
```

Em seguida, edite `.streamlit/secrets.toml` e substitua os valores de exemplo pelos seus valores reais:

- `spreadsheet_id`: ID da planilha do Google Sheets
- `[google_credentials]`: Credenciais da Service Account do Google Cloud
- `[passwords]`: Senhas dos usuários do sistema

**Guia completo de configuração:** [`docs/SETUP_GOOGLE_SHEETS.md`](../docs/SETUP_GOOGLE_SHEETS.md)

### config.toml (OPCIONAL)

Arquivo de configuração opcional para personalizar a aparência e comportamento do Streamlit.

Exemplo:
```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"

[server]
headless = true
port = 8501
```

Documentação: https://docs.streamlit.io/library/advanced-features/configuration

## Estrutura Esperada

```
.streamlit/
├── secrets.toml      # Credenciais (não commitado)
└── config.toml       # Configurações opcionais (pode ser commitado)
```

## Solução de Problemas

Se você receber erros relacionados a `st.secrets`:

1. Verifique se o arquivo `.streamlit/secrets.toml` existe
2. Certifique-se de que está no formato TOML válido
3. Confirme que todos os campos obrigatórios estão preenchidos
4. Consulte: [`docs/TROUBLESHOOTING.md`](../docs/TROUBLESHOOTING.md)

## Segurança

⚠️ **IMPORTANTE:**
- Nunca commit o arquivo `secrets.toml` no repositório
- Não compartilhe credenciais publicamente
- Mantenha backups seguros das suas credenciais
- Em produção, use o gerenciador de secrets do Streamlit Cloud
