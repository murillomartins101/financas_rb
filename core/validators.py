"""
Validação de dados do sistema
Implementa validações para todas as entidades
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
import re
from core.constants import TransactionType, PaymentStatus, ShowStatus, PayoutModel

class DataValidator:
    """
    Validador de dados do sistema
    """
    
    @staticmethod
    def validate_transaction(transaction_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valida dados de uma transação
        
        Args:
            transaction_data: Dados da transação
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        required_fields = ['id', 'data', 'tipo', 'categoria', 'descricao', 'valor', 'payment_status']
        
        # Verificar campos obrigatórios
        for field in required_fields:
            if field not in transaction_data or transaction_data[field] is None:
                return False, f"Campo obrigatório faltando: {field}"
        
        # Validar tipo
        if transaction_data['tipo'] not in [t.value for t in TransactionType]:
            return False, f"Tipo inválido: {transaction_data['tipo']}"
        
        # Validar status de pagamento
        if transaction_data['payment_status'] not in [s.value for s in PaymentStatus]:
            return False, f"Status de pagamento inválido: {transaction_data['payment_status']}"
        
        # Validar valor
        try:
            valor = float(transaction_data['valor'])
            if valor <= 0:
                return False, "Valor deve ser positivo"
        except (ValueError, TypeError):
            return False, "Valor inválido"
        
        # Validar data
        if not DataValidator._validate_date(transaction_data['data']):
            return False, "Data inválida"
        
        # Validar categoria se for saída
        if transaction_data['tipo'] == 'SAIDA':
            if not transaction_data.get('categoria'):
                return False, "Categoria é obrigatória para saídas"
        
        return True, "Transação válida"
    
    @staticmethod
    def validate_show(show_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valida dados de um show
        
        Args:
            show_data: Dados do show
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        required_fields = ['show_id', 'data_show', 'casa', 'cidade', 'status']
        
        # Verificar campos obrigatórios
        for field in required_fields:
            if field not in show_data or show_data[field] is None:
                return False, f"Campo obrigatório faltando: {field}"
        
        # Validar status
        if show_data['status'] not in [s.value for s in ShowStatus]:
            return False, f"Status inválido: {show_data['status']}"
        
        # Validar data
        if not DataValidator._validate_date(show_data['data_show']):
            return False, "Data do show inválida"
        
        # Validar público (se fornecido)
        if 'publico' in show_data and show_data['publico'] is not None:
            try:
                publico = int(show_data['publico'])
                if publico < 0:
                    return False, "Público não pode ser negativo"
            except (ValueError, TypeError):
                return False, "Público inválido"
        
        # Validar cachê acordado (se fornecido)
        if 'cache_acordado' in show_data and show_data['cache_acordado'] is not None:
            try:
                cache = float(show_data['cache_acordado'])
                if cache < 0:
                    return False, "Cachê acordado não pode ser negativo"
            except (ValueError, TypeError):
                return False, "Cachê acordado inválido"
        
        return True, "Show válido"
    
    @staticmethod
    def validate_payout_rule(rule_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valida dados de uma regra de rateio
        
        Args:
            rule_data: Dados da regra
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        required_fields = ['rule_id', 'nome_regra', 'modelo', 'ativa']
        
        # Verificar campos obrigatórios
        for field in required_fields:
            if field not in rule_data or rule_data[field] is None:
                return False, f"Campo obrigatório faltando: {field}"
        
        # Validar modelo
        if rule_data['modelo'] not in [m.value for m in PayoutModel]:
            return False, f"Modelo inválido: {rule_data['modelo']}"
        
        # Validar percentuais se modelo for PERCENTUAL ou MISTO
        if rule_data['modelo'] in ['PERCENTUAL', 'MISTO']:
            if 'pct_caixa' in rule_data and rule_data['pct_caixa'] is not None:
                try:
                    pct = float(rule_data['pct_caixa'])
                    if pct < 0 or pct > 100:
                        return False, "Percentual do caixa deve estar entre 0 e 100"
                except (ValueError, TypeError):
                    return False, "Percentual do caixa inválido"
            
            if 'pct_musicos' in rule_data and rule_data['pct_musicos'] is not None:
                try:
                    pct = float(rule_data['pct_musicos'])
                    if pct < 0 or pct > 100:
                        return False, "Percentual de músicos deve estar entre 0 e 100"
                except (ValueError, TypeError):
                    return False, "Percentual de músicos inválido"
        
        # Validar datas de vigência
        if 'vigencia_inicio' in rule_data and rule_data['vigencia_inicio']:
            if not DataValidator._validate_date(rule_data['vigencia_inicio']):
                return False, "Data de início da vigência inválida"
        
        if 'vigencia_fim' in rule_data and rule_data['vigencia_fim']:
            if not DataValidator._validate_date(rule_data['vigencia_fim']):
                return False, "Data de fim da vigência inválida"
        
        # Verificar se data fim é posterior à data início
        if ('vigencia_inicio' in rule_data and rule_data['vigencia_inicio'] and 
            'vigencia_fim' in rule_data and rule_data['vigencia_fim']):
            try:
                inicio = DataValidator._parse_date(rule_data['vigencia_inicio'])
                fim = DataValidator._parse_date(rule_data['vigencia_fim'])
                if fim < inicio:
                    return False, "Data de fim deve ser posterior à data de início"
            except:
                pass
        
        return True, "Regra de rateio válida"
    
    @staticmethod
    def validate_member(member_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valida dados de um membro
        
        Args:
            member_data: Dados do membro
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        required_fields = ['member_id', 'nome']
        
        # Verificar campos obrigatórios
        for field in required_fields:
            if field not in member_data or member_data[field] is None:
                return False, f"Campo obrigatório faltando: {field}"
        
        # Validar nome
        if not member_data['nome'] or len(member_data['nome'].strip()) < 2:
            return False, "Nome inválido"
        
        # Validar status (se fornecido)
        if 'ativo' in member_data and member_data['ativo'] is not None:
            if member_data['ativo'] not in ['SIM', 'NÃO', 'ATIVO', 'INATIVO']:
                return False, "Status inválido. Use 'SIM', 'NÃO', 'ATIVO' ou 'INATIVO'"
        
        return True, "Membro válido"
    
    @staticmethod
    def validate_member_share(share_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valida dados de uma participação de membro
        
        Args:
            share_data: Dados da participação
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        required_fields = ['share_id', 'rule_id', 'member_id', 'tipo']
        
        # Verificar campos obrigatórios
        for field in required_fields:
            if field not in share_data or share_data[field] is None:
                return False, f"Campo obrigatório faltando: {field}"
        
        # Validar tipo
        if share_data['tipo'] not in ['PESO', 'FIXO']:
            return False, f"Tipo inválido: {share_data['tipo']}"
        
        # Validar valor baseado no tipo
        if share_data['tipo'] == 'PESO':
            if 'peso' not in share_data or share_data['peso'] is None:
                return False, "Peso é obrigatório para tipo PESO"
            
            try:
                peso = float(share_data['peso'])
                if peso <= 0:
                    return False, "Peso deve ser positivo"
            except (ValueError, TypeError):
                return False, "Peso inválido"
        
        elif share_data['tipo'] == 'FIXO':
            if 'valor_fixo' not in share_data or share_data['valor_fixo'] is None:
                return False, "Valor fixo é obrigatório para tipo FIXO"
            
            try:
                valor = float(share_data['valor_fixo'])
                if valor < 0:
                    return False, "Valor fixo não pode ser negativo"
            except (ValueError, TypeError):
                return False, "Valor fixo inválido"
        
        return True, "Participação válida"
    
    @staticmethod
    def validate_merchandising(merch_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valida dados de merchandising
        
        Args:
            merch_data: Dados do merchandising
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        required_fields = ['id', 'data', 'tipo', 'produto', 'quantidade', 'valor_unitario']
        
        # Verificar campos obrigatórios
        for field in required_fields:
            if field not in merch_data or merch_data[field] is None:
                return False, f"Campo obrigatório faltando: {field}"
        
        # Validar tipo
        if merch_data['tipo'] not in ['VENDA', 'COMPRA']:
            return False, f"Tipo inválido: {merch_data['tipo']}"
        
        # Validar data
        if not DataValidator._validate_date(merch_data['data']):
            return False, "Data inválida"
        
        # Validar quantidade
        try:
            quantidade = int(merch_data['quantidade'])
            if quantidade <= 0:
                return False, "Quantidade deve ser positiva"
        except (ValueError, TypeError):
            return False, "Quantidade inválida"
        
        # Validar valor unitário
        try:
            valor = float(merch_data['valor_unitario'])
            if valor <= 0:
                return False, "Valor unitário deve ser positivo"
        except (ValueError, TypeError):
            return False, "Valor unitário inválido"
        
        return True, "Merchandising válido"
    
    @staticmethod
    def _validate_date(date_value: Any) -> bool:
        """
        Valida se o valor é uma data válida
        
        Args:
            date_value: Valor a ser validado
            
        Returns:
            True se for data válida
        """
        if isinstance(date_value, datetime):
            return True
        
        if isinstance(date_value, str):
            try:
                # Tentar múltiplos formatos
                formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']
                for fmt in formats:
                    try:
                        datetime.strptime(date_value, fmt)
                        return True
                    except ValueError:
                        continue
            except:
                return False
        
        return False
    
    @staticmethod
    def _parse_date(date_value: Any) -> Optional[datetime]:
        """
        Converte valor para datetime
        
        Args:
            date_value: Valor a ser convertido
            
        Returns:
            datetime ou None
        """
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, str):
            try:
                formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']
                for fmt in formats:
                    try:
                        return datetime.strptime(date_value, fmt)
                    except ValueError:
                        continue
            except:
                pass
        
        return None
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, expected_columns: List[str]) -> Tuple[bool, str]:
        """
        Valida estrutura de um DataFrame
        
        Args:
            df: DataFrame a ser validado
            expected_columns: Colunas esperadas
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        if df.empty:
            return True, "DataFrame vazio (válido)"
        
        # Verificar colunas obrigatórias
        missing_columns = []
        for col in expected_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            return False, f"Colunas faltando: {', '.join(missing_columns)}"
        
        return True, "DataFrame válido"

def validate_transaction(transaction_data: Dict[str, Any]) -> bool:
    """
    Função pública para validar transação
    
    Args:
        transaction_data: Dados da transação
        
    Returns:
        True se válido
    """
    success, _ = DataValidator.validate_transaction(transaction_data)
    return success

def validate_show(show_data: Dict[str, Any]) -> bool:
    """
    Função pública para validar show
    
    Args:
        show_data: Dados do show
        
    Returns:
        True se válido
    """
    success, _ = DataValidator.validate_show(show_data)
    return success

def validate_payout_rule(rule_data: Dict[str, Any]) -> bool:
    """
    Função pública para validar regra de rateio
    
    Args:
        rule_data: Dados da regra
        
    Returns:
        True se válido
    """
    success, _ = DataValidator.validate_payout_rule(rule_data)
    return success

def get_validation_message(entity: str, data: Dict[str, Any]) -> str:
    """
    Obtém mensagem de validação detalhada
    
    Args:
        entity: Tipo de entidade
        data: Dados a serem validados
        
    Returns:
        Mensagem de validação
    """
    if entity == 'transaction':
        success, message = DataValidator.validate_transaction(data)
    elif entity == 'show':
        success, message = DataValidator.validate_show(data)
    elif entity == 'payout_rule':
        success, message = DataValidator.validate_payout_rule(data)
    elif entity == 'member':
        success, message = DataValidator.validate_member(data)
    elif entity == 'member_share':
        success, message = DataValidator.validate_member_share(data)
    elif entity == 'merchandising':
        success, message = DataValidator.validate_merchandising(data)
    else:
        return "Tipo de entidade inválido"
    
    if success:
        return f"✅ {message}"
    else:
        return f"❌ {message}"