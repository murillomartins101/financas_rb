"""
Constantes do sistema Rockbuzz Finance
Define todas as constantes usadas em todo o sistema
"""

from enum import Enum

class TransactionType(Enum):
    """Tipos de transações financeiras"""
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"

class PaymentStatus(Enum):
    """Status de pagamento das transações"""
    PAGO = "PAGO"
    NAO_RECEBIDO = "NÃO RECEBIDO"
    ESTORNADO = "ESTORNADO"

class ShowStatus(Enum):
    """Status dos shows"""
    REALIZADO = "REALIZADO"
    CONFIRMADO = "CONFIRMADO"
    CANCELADO = "CANCELADO"

class PayoutModel(Enum):
    """Modelos de rateio"""
    PERCENTUAL = "PERCENTUAL"
    MISTO = "MISTO"
    FIXO = "FIXO"

# Constantes de configuração
CACHE_TTL = 300  # 5 minutos em segundos
CACHE_FILE = "cache/rockbuzz_cache.pkl"

# Categorias de despesas operacionais (conforme especificação)
OPERATIONAL_EXPENSE_CATEGORIES = [
    "PRODUÇÃO",
    "LOGÍSTICA",
    "MARKETING",
    "ALUGUEL",
    "EQUIPE TÉCNICA",
    "FOTOGRAFIA",
    "ENSAIOS",
    "OUTROS"
]

# Categorias de cachês
CACHE_CATEGORY = "CACHÊS-MÚSICOS"

# Colunas das planilhas
SHOWS_COLUMNS = [
    'show_id', 'data_show', 'casa', 'cidade', 'status', 
    'publico', 'cache_acordado', 'observacao'
]

TRANSACTIONS_COLUMNS = [
    'id', 'data', 'tipo', 'categoria', 'subcategoria', 
    'descricao', 'valor', 'show_id', 'payment_status', 'conta'
]

PAYOUT_RULES_COLUMNS = [
    'rule_id', 'nome_regra', 'modelo', 'pct_caixa', 
    'pct_musicos', 'ativa', 'vigencia_inicio', 'vigencia_fim'
]

# URLs e configurações do Google Sheets
SPREADSHEET_ID = None  # Será carregado do secrets.toml
SHEET_NAMES = {
    'shows': 'shows',
    'transactions': 'transactions',
    'payout_rules': 'payout_rules',
    'show_payout_config': 'show_payout_config',
    'members': 'members',
    'member_shares': 'member_shares'
}