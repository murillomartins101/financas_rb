ROCKBUZZ FINANCE (VERSÃO FINAL)

## 🚀 INÍCIO RÁPIDO

**Novo usuário?** Comece aqui: [QUICKSTART.md](QUICKSTART.md)

**Problemas com credenciais?** Veja: [.streamlit/README.md](.streamlit/README.md)

**Erros ou problemas?** Consulte: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

1. OBJETIVO DO SISTEMA
Criar um dashboard financeiro em Python (Streamlit) que permita:
	• Acesso via login (mobile e desktop)
	• Todos os integrantes podem inserir dados
	• Análise financeira real da banda
	• Separação clara entre receitas, despesas operacionais e cachês
	• Avaliação de rentabilidade por show
	• Controle de caixa, valores a receber e projeções
	• Aplicação de regras de rateio por show
	• KPIs claros + gráficos analíticos e preditivos
	• Cadastro e edição de registros diretamente no sistema (CRUD)
	• Sincronização com Google Sheets via Google Cloud

2. TECNOLOGIA E ARQUITETURA
Stack obrigatória
	• Python 3.10+
	• Streamlit
	• Pandas / NumPy
	• Plotly
	• Google Cloud (Service Account)
	• Google Sheets API
	• Estrutura modular de código
Arquitetura mínima do projeto
rockbuzz_finance/
│
├── app.py
├── streamlit/
│   ├── secrets.toml
│   └── config.toml
├── assets/
│   ├── logo.png
│   ├── favicon.ico
│   └── styles.css
├── pages/
│   ├── 00_🏠_Home.py
│   ├── 01_🎸_Shows.py
│   ├── 02_💰_Transações.py
│   ├── 03_📊_Relatórios & projeções.py
│   ├── 04_📝_Cadastro de Registros.py   ← **CRUD**
│
├── core/
│   ├── auth.py
│   ├── config_store.py
│   ├── constants.py
│   ├── data_loader.py
│   ├── data_writer.py
│   ├── google_cloud.py
│   ├── google_sheets.py
│   ├── filters.py
│   ├── metrics.py
│   ├── ui_components.py
│   ├── validators.py
│   └── cache_manager.py
│
├── models/
│   ├── transaction.py
│   ├── show.py
│   ├── payout.py
│   ├── member.py
│   └── merch.py
│
├── utils/
│   ├── date_utils.py
│   ├── file_utils.py
│   └── log_utils.py
│
├── data/
│   └── Financas_RB.xlsx
│
├── tests/
│   ├── test_metrics.py
│   ├── test_validators.py
│   └── test_google_sheets.py
│
└── requirements.txt

Regras importantes
	• Nenhuma regra de negócio nas páginas
	• Páginas apenas consomem funções prontas
	• Google Sheets será a fonte oficial 

3. FONTES DE DADOS (PLANILHAS)
Aba shows
	• show_id
	• data_show
	• casa
	• cidade
	• status → REALIZADO | CONFIRMADO
	• publico
	• cache_acordado
	• observacao
Aba transactions
	• id
	• data
	• tipo → ENTRADA | SAIDA
	• categoria
	• subcategoria
	• descricao
	• valor
	• show_id (opcional)
	• payment_status → PAGO | NÃO RECEBIDO | ESTORNADO
	• conta
Aba payout_rules
	• rule_id
	• nome_regra
	• modelo → PERCENTUAL | MISTO
	• pct_caixa
	• pct_musicos
	• ativa
	• vigencia_inicio
	• vigencia_fim
Aba show_payout_config
	• show_id
	• rule_id
Aba members
	• member_id
	• nome
	• ativo
Aba member_shares
	• share_id
	• rule_id
	• member_id
	• tipo → PESO | FIXO
	• peso ou valor_fixo

4. REGRAS DE NEGÓCIO (CRÍTICAS)
4.1 Status de pagamento
	• Só entra em caixa: payment_status == "PAGO"
	• ESTORNADO → ignorar
	• NÃO RECEBIDO → vai para A RECEBER
4.2 Reconhecimento de receita de shows
Receita só existe se:
	• show.status == REALIZADO
	• pagamento == PAGO
Shows CONFIRMADOS entram apenas em projeções.
4.3 Merchandising
	• Vendas = receita
	• Compras = custo
	• Ambos impactam caixa e resultado global
4.4 Separação obrigatória de despesas
	• CACHÊS-MÚSICOS → KPI separado
	• Despesas operacionais incluem: 
		○ Produção
		○ Logística
		○ Marketing
		○ Aluguel
		○ Equipe técnica
		○ Fotografia
		○ Ensaios
		○ Outros

5. FILTROS (OBRIGATÓRIO)
Filtro global de período:
	• Mês atual
	• Mês anterior
	• Últimos 6 meses
	• Ano atual
	• Ano anterior
	• Todo período
Todos KPIs e gráficos devem respeitar o filtro.

6. KPIs OBRIGATÓRIOS
	1. Total de shows realizados
	2. Total de entradas (R$)
	3. Valor efetivo por show
	4. Total de cachê de músicos
	5. Total geral de despesas
	6. Caixa atual
	7. A receber
	8. Público total
	9. Público médio
	10. % do caixa sobre receita
	11. Caixa estimado (considerando shows confirmados)
	12. Shows realizados sem entrada paga
	13. KPI de público
	14. KPI de despesas fixas por mês

7. GRÁFICOS (ANALÍTICOS + PREDITIVOS)
	1. Tendência de entradas por show
	2. Tendência de caixa
	3. Previsão de entrada dos próximos shows
	4. Gráfico preditivo de despesas
Métodos estatísticos devem ser explícitos (média móvel, regressão linear etc.).

8. UI / UX
	• Sidebar fixa escura com logo
	• Dashboard claro e legível
	• KPIs em cards
	• Gráficos responsivos
	• Layout profissional

9. BOAS PRÁTICAS OBRIGATÓRIAS
	• Código comentado
	• Funções puras para métricas
	• Validação de dados
	• Nenhuma regra financeira na interface
	• Projeto pronto para crescer

10. RESULTADO ESPERADO
	• Código completo funcional
	• Dashboard financeiramente correto
	• KPIs confiáveis
	• Base sólida para evolução futura

11. CADASTRO DE REGISTROS (CRUD COMPLETO)
Página: 04_📝_Cadastro de Registros.py
Entidades editáveis
	• Shows
	• Transações
	• Regras de rateio
	• Configuração de rateio por show
	• Membros
	• Merchandising
Requisitos
	• Formulários com validação
	• Botões: Salvar, Editar, Excluir
	• Logs de auditoria
	• Escrita no Google Sheets
	• Atualização do cache
	• Mensagens amigáveis

12. INTEGRAÇÃO COM GOOGLE CLOUD + GOOGLE SHEETS
Objetivo
Google Sheets será a fonte oficial.
Componentes
core/google_cloud.py
	• Carrega credenciais
	• Inicializa cliente
	• Gerencia tokens
core/google_sheets.py
Funções obrigatórias:
	• read_sheet
	• write_row
	• update_row
	• delete_row
	• sync_all
core/data_loader.py
	• Tenta Sheets
	• Se falhar, usa Excel
core/data_writer.py
	• Escrita centralizada
	• Logs
	• Validações
Requisitos técnicos
	• Autenticação via Service Account
	• Estrutura idêntica ao Excel
	• Controle de concorrência
	• Cache local

13. SINCRONIZAÇÃO E CACHE
	• Cache atualizado a cada 5 minutos
	• Cache atualizado após qualquer alteração
	• Cache salvo em .pkl
	• Páginas nunca acessam Sheets diretamente

14. SEGURANÇA E AUTENTICAÇÃO
	• Login obrigatório
	• Permissões: admin / membro
	• Admin edita tudo
	• Membro só insere transações e merch
	• Tokens expiram

15. SOLUÇÃO DE PROBLEMAS
Se você encontrar erros ao executar a aplicação, consulte o guia de troubleshooting:
	• docs/TROUBLESHOOTING.md - Guia completo de solução de problemas
	• docs/SETUP_GOOGLE_SHEETS.md - Configuração do Google Sheets
	• docs/CHANGES.md - Histórico de mudanças

Erros comuns:
	• KeyError em st.secrets: Configure .streamlit/secrets.toml corretamente
	• Erro de conexão Google Sheets: Verifique credenciais e permissões
	• ModuleNotFoundError: Execute pip install -r requirements.txt

