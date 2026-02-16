# 🚀 Guia de Início Rápido - Rockbuzz Finance

Este guia ajuda você a configurar e executar o Rockbuzz Finance pela primeira vez.

## ⚡ Início Rápido (5 minutos)

### Opção 1: Modo Desenvolvimento (Sem Google Sheets)

Se você quer apenas testar o sistema localmente:

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar aplicação
streamlit run app.py
```

✅ **Pronto!** O sistema usará o arquivo Excel local (`data/Financas_RB.xlsx`)

**Limitações:**
- ❌ Dados não sincronizam com Google Sheets
- ❌ Múltiplos usuários não compartilham dados
- ✅ Perfeito para testes locais

---

### Opção 2: Com Google Sheets (Produção)

Para usar com sincronização no Google Sheets:

#### Passo 1: Instalar Dependências

```bash
pip install -r requirements.txt
```

#### Passo 2: Configurar Credenciais

```bash
# Copiar arquivo de exemplo
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

#### Passo 3: Obter Credenciais do Google Cloud

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um projeto
3. Habilite as APIs:
   - Google Sheets API
   - Google Drive API
4. Crie uma Service Account
5. Baixe o arquivo JSON de credenciais

**Tutorial detalhado:** [docs/SETUP_GOOGLE_SHEETS.md](docs/SETUP_GOOGLE_SHEETS.md)

#### Passo 4: Preencher secrets.toml

Abra `.streamlit/secrets.toml` e preencha com os valores do arquivo JSON:

```toml
spreadsheet_id = "SEU_ID_DA_PLANILHA_AQUI"

[google_credentials]
type = "service_account"
project_id = "valor-do-json"
private_key_id = "valor-do-json"
private_key = "valor-do-json-com-quebras-de-linha"
client_email = "valor-do-json"
client_id = "valor-do-json"
# ... outros campos
```

#### Passo 5: Compartilhar Planilha

1. Abra sua planilha do Google Sheets
2. Clique em "Compartilhar"
3. Adicione o **client_email** da Service Account
4. Dê permissão de **"Editor"**

#### Passo 6: Executar

```bash
streamlit run app.py
```

---

## 🔑 Login Padrão

Após iniciar a aplicação, use estas credenciais para fazer login:

- **Usuário:** `admin`
- **Senha:** Verifique no arquivo `core/auth.py` (modo desenvolvimento)

---

## 📋 Estrutura do Projeto

```
financas_rb/
├── .streamlit/
│   ├── secrets.toml.example    # ✅ Template de configuração
│   ├── secrets.toml            # ❌ Suas credenciais (não commitado)
│   ├── config.toml             # ✅ Configurações do Streamlit
│   └── README.md               # 📚 Guia de configuração
│
├── docs/
│   ├── SETUP_GOOGLE_SHEETS.md  # 📘 Tutorial completo
│   └── TROUBLESHOOTING.md      # 🔧 Solução de problemas
│
├── core/                       # 🧩 Lógica de negócio
├── pages/                      # 📄 Páginas da aplicação
├── data/                       # 📊 Dados locais
└── app.py                      # 🚀 Arquivo principal
```

---

## ❓ Problemas Comuns

### Erro: "Nenhuma fonte de credenciais encontrada"

**Solução:**
```bash
# Opção A: Criar secrets.toml
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edite o arquivo e preencha suas credenciais

# Opção B: Usar arquivo JSON local
# Coloque google_credentials.json na raiz do projeto
```

### Erro: "ModuleNotFoundError"

**Solução:**
```bash
pip install -r requirements.txt
```

### Erro: "PERMISSION_DENIED" no Google Sheets

**Solução:**
- Compartilhe a planilha com o email da Service Account (client_email)
- Dê permissão de "Editor"

### Erro de configuração do Streamlit

**Solução:**
```bash
# Limpar cache
streamlit cache clear

# Executar com cache limpo
streamlit run app.py --clear-cache
```

---

## 📚 Recursos Adicionais

### Documentação Completa

- 📘 [Setup Google Sheets](docs/SETUP_GOOGLE_SHEETS.md) - Configuração detalhada
- 🔧 [Troubleshooting](docs/TROUBLESHOOTING.md) - Solução de problemas
- 📝 [Changelog](docs/CHANGES.md) - Histórico de mudanças
- 💡 [UI Improvements](docs/UI_IMPROVEMENTS.md) - Melhorias de interface

### Links Úteis

- 🌐 [Streamlit Docs](https://docs.streamlit.io/)
- ☁️ [Google Cloud Console](https://console.cloud.google.com/)
- 📊 [Google Sheets API](https://developers.google.com/sheets/api)
- 🔐 [Streamlit Secrets](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)

---

## 🆘 Precisa de Ajuda?

1. **Consulte a documentação:**
   - `.streamlit/README.md` - Configuração básica
   - `docs/TROUBLESHOOTING.md` - Problemas comuns

2. **Verifique os logs:**
   ```bash
   streamlit run app.py --logger.level=debug
   ```

3. **Teste a conexão:**
   - Na interface do app, clique em "🔄 Testar Conexão" no sidebar
   - Veja os logs detalhados para diagnóstico

4. **Abra uma issue:**
   - Inclua: versão do Python, versão do Streamlit, SO
   - Inclua: mensagem de erro completa
   - Inclua: estrutura do secrets.toml (SEM credenciais)

---

## ✅ Checklist de Configuração

Use este checklist para garantir que tudo está configurado:

### Modo Desenvolvimento (Excel Local)
- [ ] Python 3.10+ instalado
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Arquivo `data/Financas_RB.xlsx` existe
- [ ] Aplicação executada com `streamlit run app.py`

### Modo Produção (Google Sheets)
- [ ] Todas as etapas do modo desenvolvimento
- [ ] Projeto criado no Google Cloud Console
- [ ] APIs habilitadas (Sheets + Drive)
- [ ] Service Account criada
- [ ] Arquivo JSON de credenciais baixado
- [ ] Arquivo `.streamlit/secrets.toml` criado e preenchido
- [ ] ID da planilha configurado
- [ ] Planilha compartilhada com client_email
- [ ] Permissão "Editor" concedida
- [ ] Teste de conexão realizado com sucesso

---

## 🎉 Próximos Passos

Depois de configurar e executar:

1. **Explore o Dashboard:**
   - Página Home: Visão geral financeira
   - Shows: Gerenciar apresentações
   - Transações: Controle de receitas/despesas
   - Relatórios: Análises e projeções
   - Cadastros: CRUD completo

2. **Customize:**
   - Ajuste o tema em `.streamlit/config.toml`
   - Configure regras de rateio
   - Adicione membros da banda

3. **Monitore:**
   - Acompanhe KPIs em tempo real
   - Gere relatórios financeiros
   - Analise tendências

**Bom uso! 🎸💰**
