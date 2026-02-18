"""
Cálculo de KPIs e métricas financeiras
Implementa todas as métricas obrigatórias da especificação

CORREÇÕES IMPLEMENTADAS:
- Total Despesas agora filtra apenas payment_status == 'PAGO' (antes: != 'ESTORNADO')
- Cache Músicos suporta múltiplas nomenclaturas (CACHÊS-MÚSICOS, PAYOUT_MUSICOS)
- Adicionada validação de integridade de dados
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import streamlit as st
from scipy import stats
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')


def validate_data_integrity(data: Dict[str, pd.DataFrame]) -> Dict[str, List[str]]:
    """
    Valida a integridade dos dados carregados
    
    Args:
        data: Dicionário com DataFrames
        
    Returns:
        Dicionário com lista de warnings por categoria
    """
    warnings_dict = {
        'critical': [],
        'warnings': [],
        'info': []
    }
    
    # Validar shows
    if 'shows' in data and not data['shows'].empty:
        shows = data['shows']
        required_cols = ['show_id', 'data_show', 'status']
        missing = [c for c in required_cols if c not in shows.columns]
        if missing:
            warnings_dict['critical'].append(f"Shows: colunas ausentes: {missing}")
        
        # Validar status
        if 'status' in shows.columns:
            valid_status = ['REALIZADO', 'CONFIRMADO']
            invalid = shows[~shows['status'].isin(valid_status)]
            if len(invalid) > 0:
                warnings_dict['warnings'].append(
                    f"Shows: {len(invalid)} registros com status inválido (esperado: {valid_status})"
                )
    
    # Validar transactions
    if 'transactions' in data and not data['transactions'].empty:
        trans = data['transactions']
        required_cols = ['tipo', 'valor', 'payment_status']
        missing = [c for c in required_cols if c not in trans.columns]
        if missing:
            warnings_dict['critical'].append(f"Transactions: colunas ausentes: {missing}")
        
        # Validar tipo
        if 'tipo' in trans.columns:
            valid_tipos = ['ENTRADA', 'SAIDA']
            invalid = trans[~trans['tipo'].isin(valid_tipos)]
            if len(invalid) > 0:
                warnings_dict['warnings'].append(
                    f"Transactions: {len(invalid)} registros com tipo inválido (esperado: {valid_tipos})"
                )
        
        # Validar payment_status
        if 'payment_status' in trans.columns:
            valid_status = ['PAGO', 'NÃO RECEBIDO', 'ESTORNADO', 'NÃO PAGO']
            invalid = trans[~trans['payment_status'].isin(valid_status)]
            if len(invalid) > 0:
                warnings_dict['warnings'].append(
                    f"Transactions: {len(invalid)} registros com payment_status inválido"
                )
        
        # Validar valores
        if 'valor' in trans.columns:
            null_values = trans['valor'].isna().sum()
            if null_values > 0:
                warnings_dict['warnings'].append(
                    f"Transactions: {null_values} registros com valor nulo"
                )
    
    return warnings_dict


class FinancialMetrics:
    """
    Calculadora de métricas financeiras da banda
    """
    
    def __init__(self, data: Dict[str, pd.DataFrame]):
        self.data = data
        self.shows_df = data.get('shows', pd.DataFrame())
        self.transactions_df = data.get('transactions', pd.DataFrame())
        self.payout_rules_df = data.get('payout_rules', pd.DataFrame())
        self.members_df = data.get('members', pd.DataFrame())
        
        # Validar dados na inicialização
        self._validation_warnings = validate_data_integrity(data)
    
    def get_validation_warnings(self) -> Dict[str, List[str]]:
        """
        Retorna warnings de validação de dados
        
        Returns:
            Dicionário com listas de warnings por severidade
        """
        return self._validation_warnings
    
    def calculate_all_kpis(self, start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> Dict[str, float]:
        """
        Calcula todos os KPIs para o período especificado
        
        Args:
            start_date: Data inicial do filtro
            end_date: Data final do filtro
            
        Returns:
            Dicionário com todos os KPIs
        """
        # Aplicar filtro de datas
        filtered_shows, filtered_transactions = self._filter_data_by_date(start_date, end_date)
        
        kpis = {}
        
        # KPI 1: Total de shows realizados
        kpis['total_shows_realizados'] = self._calculate_total_shows_realizados(filtered_shows)
        
        # KPI 2: Total de entradas (R$)
        kpis['total_entradas'] = self._calculate_total_entradas(filtered_transactions)
        
        # KPI 3: Valor efetivo por show
        kpis['valor_efetivo_por_show'] = self._calculate_valor_efetivo_por_show(
            kpis['total_entradas'], kpis['total_shows_realizados']
        )
        
        # KPI 4: Total de cachê de músicos
        kpis['total_cache_musicos'] = self._calculate_total_cache_musicos(filtered_transactions)
        
        # KPI 5: Total geral de despesas
        kpis['total_despesas'] = self._calculate_total_despesas(filtered_transactions)
        
        # KPI 6: Caixa atual
        kpis['caixa_atual'] = self._calculate_caixa_atual(filtered_transactions)
        
        # KPI 7: A receber
        kpis['a_receber'] = self._calculate_a_receber(filtered_transactions)
        
        # KPI 8: Público total
        kpis['publico_total'] = self._calculate_publico_total(filtered_shows)
        
        # KPI 9: Público médio
        kpis['publico_medio'] = self._calculate_publico_medio(
            kpis['publico_total'], kpis['total_shows_realizados']
        )
        
        # KPI 10: % do caixa sobre receita
        kpis['percentual_caixa'] = self._calculate_percentual_caixa(
            kpis['caixa_atual'], kpis['total_entradas']
        )
        
        # KPI 11: Caixa estimado (considerando shows confirmados)
        kpis['caixa_estimado'] = self._calculate_caixa_estimado(
            kpis['caixa_atual'], filtered_shows
        )
        
        # KPI 12: Shows realizados sem entrada paga
        kpis['shows_sem_entrada_paga'] = self._calculate_shows_sem_entrada_paga(
            filtered_shows, filtered_transactions
        )
        
        # KPI 13: KPI de público (métrica composta)
        kpis['kpi_publico'] = self._calculate_kpi_publico(filtered_shows)
        
        # KPI 14: KPI de despesas fixas por mês
        kpis['despesas_fixas_mensais'] = self._calculate_despesas_fixas_mensais(filtered_transactions)
        
        return kpis
    
    def _filter_data_by_date(self, start_date: Optional[datetime],
                            end_date: Optional[datetime]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Filtra dados pelo período especificado
        
        Args:
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Tupla com (shows_filtrados, transações_filtradas)
        """
        shows_df = self.shows_df.copy()
        transactions_df = self.transactions_df.copy()
        
        # Converter datas
        if 'data_show' in shows_df.columns:
            shows_df['data_show'] = pd.to_datetime(shows_df['data_show'], errors='coerce')
        
        if 'data' in transactions_df.columns:
            transactions_df['data'] = pd.to_datetime(transactions_df['data'], errors='coerce')
        
        # Aplicar filtros
        if start_date and end_date:
            # Filtrar shows
            mask_shows = (shows_df['data_show'] >= start_date) & (shows_df['data_show'] <= end_date)
            shows_filtered = shows_df[mask_shows].copy()
            
            # Filtrar transações
            mask_trans = (transactions_df['data'] >= start_date) & (transactions_df['data'] <= end_date)
            trans_filtered = transactions_df[mask_trans].copy()
        else:
            shows_filtered = shows_df.copy()
            trans_filtered = transactions_df.copy()
        
        return shows_filtered, trans_filtered
    
    def _calculate_total_shows_realizados(self, shows_df: pd.DataFrame) -> int:
        """
        KPI 1: Total de shows realizados
        Considera apenas shows com status REALIZADO
        
        Args:
            shows_df: DataFrame de shows filtrado
            
        Returns:
            Número total de shows realizados
        """
        if shows_df.empty or 'status' not in shows_df.columns:
            return 0
        
        # Contar shows com status REALIZADO
        shows_realizados = shows_df[shows_df['status'] == 'REALIZADO']
        return len(shows_realizados)
    
    def _calculate_total_entradas(self, transactions_df: pd.DataFrame) -> float:
        """
        KPI 2: Total de entradas (R$)
        Soma valores de transações do tipo ENTRADA com payment_status PAGO
        
        Args:
            transactions_df: DataFrame de transações filtrado
            
        Returns:
            Valor total das entradas
        """
        if transactions_df.empty:
            return 0.0
        
        # Filtrar entradas pagas
        entradas_pagas = transactions_df[
            (transactions_df['tipo'] == 'ENTRADA') & 
            (transactions_df['payment_status'] == 'PAGO')
        ]
        
        # Somar valores
        if 'valor' in entradas_pagas.columns:
            return entradas_pagas['valor'].sum()
        return 0.0
    
    def _calculate_valor_efetivo_por_show(self, total_entradas: float, 
                                        total_shows: int) -> float:
        """
        KPI 3: Valor efetivo por show
        Divide o total de entradas pelo número de shows realizados
        
        Args:
            total_entradas: Valor total das entradas
            total_shows: Número total de shows realizados
            
        Returns:
            Valor médio por show
        """
        if total_shows > 0:
            return total_entradas / total_shows
        return 0.0
    
    def _calculate_total_cache_musicos(self, transactions_df: pd.DataFrame) -> float:
        """
        KPI 4: Total de cachê de músicos
        Soma valores de transações do tipo SAÍDA com categoria CACHÊS-MÚSICOS ou PAYOUT_MUSICOS
        
        IMPORTANTE: Suporta múltiplas convenções de nomenclatura:
        - CACHÊS-MÚSICOS (formato original)
        - PAYOUT_MUSICOS (formato alternativo)
        
        Args:
            transactions_df: DataFrame de transações filtrado
            
        Returns:
            Valor total de cachês de músicos
        """
        if transactions_df.empty:
            return 0.0
        
        # Filtrar cachês de músicos (suporta múltiplas nomenclaturas)
        cache_musicos = transactions_df[
            (transactions_df['tipo'] == 'SAIDA') & 
            (transactions_df['categoria'].isin(['CACHÊS-MÚSICOS', 'PAYOUT_MUSICOS'])) &
            (transactions_df['payment_status'] == 'PAGO')
        ]
        
        # Somar valores
        if 'valor' in cache_musicos.columns:
            return cache_musicos['valor'].sum()
        return 0.0
    
    def _calculate_total_despesas(self, transactions_df: pd.DataFrame) -> float:
        """
        KPI 5: Total geral de despesas
        Soma valores de todas as transações do tipo SAÍDA com status PAGO
        
        IMPORTANTE: Alterado para considerar apenas despesas PAGAS (payment_status == 'PAGO')
        para consistência com a regra de negócio documentada no README:
        "Só entra em caixa: payment_status == PAGO"
        
        Args:
            transactions_df: DataFrame de transações filtrado
            
        Returns:
            Valor total das despesas pagas
        """
        if transactions_df.empty:
            return 0.0
        
        # Filtrar despesas PAGAS (consistente com outras métricas)
        despesas = transactions_df[
            (transactions_df['tipo'] == 'SAIDA') & 
            (transactions_df['payment_status'] == 'PAGO')
        ]
        
        # Somar valores
        if 'valor' in despesas.columns:
            return despesas['valor'].sum()
        return 0.0
    
    def _calculate_caixa_atual(self, transactions_df: pd.DataFrame) -> float:
        """
        KPI 6: Caixa atual
        Calcula: (Entradas pagas) - (Saídas pagas)
        
        Args:
            transactions_df: DataFrame de transações filtrado
            
        Returns:
            Saldo atual de caixa
        """
        if transactions_df.empty:
            return 0.0
        
        # Entradas pagas
        entradas_pagas = transactions_df[
            (transactions_df['tipo'] == 'ENTRADA') & 
            (transactions_df['payment_status'] == 'PAGO')
        ]
        total_entradas = entradas_pagas['valor'].sum() if 'valor' in entradas_pagas.columns else 0.0
        
        # Saídas pagas
        saidas_pagas = transactions_df[
            (transactions_df['tipo'] == 'SAIDA') & 
            (transactions_df['payment_status'] == 'PAGO')
        ]
        total_saidas = saidas_pagas['valor'].sum() if 'valor' in saidas_pagas.columns else 0.0
        
        return total_entradas - total_saidas
    
    def _calculate_a_receber(self, transactions_df: pd.DataFrame) -> float:
        """
        KPI 7: A receber
        Soma valores de transações do tipo ENTRADA com status NÃO RECEBIDO
        
        Args:
            transactions_df: DataFrame de transações filtrado
            
        Returns:
            Valor total a receber
        """
        if transactions_df.empty:
            return 0.0
        
        # Filtrar valores a receber
        a_receber = transactions_df[
            (transactions_df['tipo'] == 'ENTRADA') & 
            (transactions_df['payment_status'] == 'NÃO RECEBIDO')
        ]
        
        # Somar valores
        if 'valor' in a_receber.columns:
            return a_receber['valor'].sum()
        return 0.0
    
    def _calculate_publico_total(self, shows_df: pd.DataFrame) -> int:
        """
        KPI 8: Público total
        Soma o público de todos os shows realizados
        
        Args:
            shows_df: DataFrame de shows filtrado
            
        Returns:
            Total de público
        """
        if shows_df.empty or 'publico' not in shows_df.columns:
            return 0
        
        # Filtrar shows realizados
        shows_realizados = shows_df[shows_df['status'] == 'REALIZADO']
        
        # Somar público
        return int(shows_realizados['publico'].sum())
    
    def _calculate_publico_medio(self, publico_total: int, 
                               total_shows: int) -> float:
        """
        KPI 9: Público médio
        Divide o público total pelo número de shows realizados
        
        Args:
            publico_total: Total de público
            total_shows: Número total de shows realizados
            
        Returns:
            Público médio por show
        """
        if total_shows > 0:
            return publico_total / total_shows
        return 0.0
    
    def _calculate_percentual_caixa(self, caixa_atual: float,
                                  total_entradas: float) -> float:
        """
        KPI 10: % do caixa sobre receita
        Calcula: (Caixa atual / Total de entradas) * 100
        
        Args:
            caixa_atual: Saldo atual de caixa
            total_entradas: Valor total das entradas
            
        Returns:
            Percentual do caixa sobre receita
        """
        if total_entradas > 0:
            return (caixa_atual / total_entradas) * 100
        return 0.0
    
    def _calculate_caixa_estimado(self, caixa_atual: float,
                                shows_df: pd.DataFrame) -> float:
        """
        KPI 11: Caixa estimado
        Adiciona cachês acordados de shows CONFIRMADOS ao caixa atual
        
        Args:
            caixa_atual: Saldo atual de caixa
            shows_df: DataFrame de shows filtrado
            
        Returns:
            Caixa estimado futuro
        """
        if shows_df.empty or 'cache_acordado' not in shows_df.columns:
            return caixa_atual
        
        # Somar cachês de shows confirmados
        shows_confirmados = shows_df[shows_df['status'] == 'CONFIRMADO']
        cache_confirmado = shows_confirmados['cache_acordado'].sum()
        
        return caixa_atual + cache_confirmado
    
    def _calculate_shows_sem_entrada_paga(self, shows_df: pd.DataFrame,
                                        transactions_df: pd.DataFrame) -> int:
        """
        KPI 12: Shows realizados sem entrada paga
        Conta shows REALIZADOS que não têm transação de ENTRADA PAGA associada
        
        Args:
            shows_df: DataFrame de shows filtrado
            transactions_df: DataFrame de transações filtrado
            
        Returns:
            Número de shows sem entrada paga
        """
        if shows_df.empty:
            return 0
        
        # IDs de shows com entradas pagas
        shows_com_entrada = transactions_df[
            (transactions_df['tipo'] == 'ENTRADA') & 
            (transactions_df['payment_status'] == 'PAGO') &
            (transactions_df['show_id'].notna())
        ]['show_id'].unique()
        
        # Filtrar shows realizados sem entrada paga
        shows_realizados = shows_df[shows_df['status'] == 'REALIZADO']
        shows_sem_entrada = shows_realizados[
            ~shows_realizados['show_id'].isin(shows_com_entrada)
        ]
        
        return len(shows_sem_entrada)
    
    def _calculate_kpi_publico(self, shows_df: pd.DataFrame) -> float:
        """
        KPI 13: KPI de público
        Métrica composta: (Público médio * Frequência de shows) / Meta de público
        
        Args:
            shows_df: DataFrame de shows filtrado
            
        Returns:
            Score do KPI de público (0-100)
        """
        if shows_df.empty:
            return 0.0
        
        # Calcular público médio dos últimos 3 meses
        three_months_ago = datetime.now() - timedelta(days=90)
        recent_shows = shows_df[
            (shows_df['status'] == 'REALIZADO') & 
            (shows_df['data_show'] >= three_months_ago)
        ]
        
        if recent_shows.empty or 'publico' not in recent_shows.columns:
            return 0.0
        
        publico_medio_recente = recent_shows['publico'].mean()
        
        # Calcular frequência de shows (shows por mês)
        shows_por_mes = len(recent_shows) / 3  # últimos 3 meses
        
        # Meta de público (ajustável)
        meta_publico = 100  # meta de 100 pessoas por show
        
        # Calcular KPI
        kpi = (publico_medio_recente * shows_por_mes) / meta_publico * 100
        return min(kpi, 100)  # Limitar a 100
    
    def _calculate_despesas_fixas_mensais(self, transactions_df: pd.DataFrame) -> float:
        """
        KPI 14: KPI de despesas fixas por mês
        Calcula a média mensal de despesas fixas
        
        Args:
            transactions_df: DataFrame de transações filtrado
            
        Returns:
            Média mensal de despesas fixas
        """
        if transactions_df.empty:
            return 0.0
        
        # Definir categorias de despesas fixas
        categorias_fixas = [
            'ALUGUEL', 'INTERNET', 'ENERGIA', 'ÁGUA', 
            'MANUTENÇÃO', 'ASSINATURAS', 'SEGURO'
        ]
        
        # Filtrar despesas fixas
        despesas_fixas = transactions_df[
            (transactions_df['tipo'] == 'SAIDA') & 
            (transactions_df['categoria'].isin(categorias_fixas)) &
            (transactions_df['payment_status'] == 'PAGO')
        ]
        
        if despesas_fixas.empty:
            return 0.0
        
        # Agrupar por mês
        despesas_fixas['mes'] = despesas_fixas['data'].dt.to_period('M')
        despesas_por_mes = despesas_fixas.groupby('mes')['valor'].sum()
        
        # Calcular média
        if len(despesas_por_mes) > 0:
            return despesas_por_mes.mean()
        return 0.0
    
    def calculate_profitability_by_show(self) -> pd.DataFrame:
        """
        Calcula rentabilidade por show
        
        Returns:
            DataFrame com análise de rentabilidade por show
        """
        if self.shows_df.empty or self.transactions_df.empty:
            return pd.DataFrame()
        
        # Filtrar shows realizados
        shows_realizados = self.shows_df[self.shows_df['status'] == 'REALIZADO'].copy()
        
        resultados = []
        
        for _, show in shows_realizados.iterrows():
            show_id = show['show_id']
            
            # Receitas do show
            receitas = self.transactions_df[
                (self.transactions_df['show_id'] == show_id) &
                (self.transactions_df['tipo'] == 'ENTRADA') &
                (self.transactions_df['payment_status'] == 'PAGO')
            ]['valor'].sum()
            
            # Despesas do show
            despesas = self.transactions_df[
                (self.transactions_df['show_id'] == show_id) &
                (self.transactions_df['tipo'] == 'SAIDA') &
                (self.transactions_df['payment_status'] == 'PAGO')
            ]['valor'].sum()
            
            # Lucro
            lucro = receitas - despesas
            
            # Margem
            margem = (lucro / receitas * 100) if receitas > 0 else 0
            
            resultados.append({
                'show_id': show_id,
                'data_show': show['data_show'],
                'casa': show['casa'],
                'cidade': show['cidade'],
                'publico': show.get('publico', 0),
                'receitas': receitas,
                'despesas': despesas,
                'lucro': lucro,
                'margem': margem,
                'lucro_por_publico': lucro / show.get('publico', 1) if show.get('publico', 0) > 0 else 0
            })
        
        return pd.DataFrame(resultados)
    
    def calculate_cash_flow_forecast(self, months: int = 6) -> pd.DataFrame:
        """
        Calcula projeção de fluxo de caixa
        
        Args:
            months: Número de meses para projetar
            
        Returns:
            DataFrame com projeção mensal
        """
        if self.transactions_df.empty:
            return pd.DataFrame()
        
        # Preparar dados históricos
        transacoes = self.transactions_df.copy()
        transacoes['mes'] = transacoes['data'].dt.to_period('M')
        
        # Agrupar por mês
        fluxo_mensal = transacoes.groupby('mes').apply(
            lambda x: pd.Series({
                'entradas': x[x['tipo'] == 'ENTRADA']['valor'].sum(),
                'saidas': x[x['tipo'] == 'SAIDA']['valor'].sum(),
                'saldo': x[x['tipo'] == 'ENTRADA']['valor'].sum() - x[x['tipo'] == 'SAIDA']['valor'].sum()
            })
        ).reset_index()
        
        # Projeção usando média móvel
        if len(fluxo_mensal) >= 3:
            fluxo_mensal['projecao'] = fluxo_mensal['saldo'].rolling(window=3, min_periods=1).mean()
        else:
            fluxo_mensal['projecao'] = fluxo_mensal['saldo']
        
        return fluxo_mensal

def calculate_kpis_with_explanation(data: Dict[str, pd.DataFrame], 
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> Dict:
    """
    Função principal para cálculo de KPIs com explicações
    
    Args:
        data: Dicionário com DataFrames
        start_date: Data inicial do filtro
        end_date: Data final do filtro
        
    Returns:
        Dicionário com KPIs e explicações
    """
    metrics = FinancialMetrics(data)
    kpis = metrics.calculate_all_kpis(start_date, end_date)
    
    # Adicionar explicações
    explanations = {
        'total_shows_realizados': {
            'valor': kpis['total_shows_realizados'],
            'explicacao': 'Número de shows com status REALIZADO no período',
            'formula': 'COUNT(shows.status == "REALIZADO")',
            'unidade': 'shows'
        },
        'total_entradas': {
            'valor': kpis['total_entradas'],
            'explicacao': 'Soma de todas as entradas com status PAGO',
            'formula': 'SUM(transactions[tipo=="ENTRADA" & payment_status=="PAGO"].valor)',
            'unidade': 'R$'
        },
        'valor_efetivo_por_show': {
            'valor': kpis['valor_efetivo_por_show'],
            'explicacao': 'Média de receita por show realizado',
            'formula': 'total_entradas / total_shows_realizados',
            'unidade': 'R$/show'
        },
        'total_cache_musicos': {
            'valor': kpis['total_cache_musicos'],
            'explicacao': 'Total pago em cachês para músicos',
            'formula': 'SUM(transactions[categoria IN ("CACHÊS-MÚSICOS", "PAYOUT_MUSICOS") & payment_status=="PAGO"].valor)',
            'unidade': 'R$'
        },
        'total_despesas': {
            'valor': kpis['total_despesas'],
            'explicacao': 'Total de todas as despesas pagas',
            'formula': 'SUM(transactions[tipo=="SAIDA" & payment_status=="PAGO"].valor)',
            'unidade': 'R$'
        },
        'caixa_atual': {
            'valor': kpis['caixa_atual'],
            'explicacao': 'Saldo atual: Entradas pagas - Saídas pagas',
            'formula': 'SUM(entradas_pagas) - SUM(saidas_pagas)',
            'unidade': 'R$'
        },
        'a_receber': {
            'valor': kpis['a_receber'],
            'explicacao': 'Valor total de entradas com status NÃO RECEBIDO',
            'formula': 'SUM(transactions[tipo=="ENTRADA" & payment_status=="NÃO RECEBIDO"].valor)',
            'unidade': 'R$'
        },
        'publico_total': {
            'valor': kpis['publico_total'],
            'explicacao': 'Total de público em todos os shows realizados',
            'formula': 'SUM(shows[status=="REALIZADO"].publico)',
            'unidade': 'pessoas'
        },
        'publico_medio': {
            'valor': kpis['publico_medio'],
            'explicacao': 'Média de público por show realizado',
            'formula': 'publico_total / total_shows_realizados',
            'unidade': 'pessoas/show'
        },
        'percentual_caixa': {
            'valor': kpis['percentual_caixa'],
            'explicacao': 'Percentual do caixa em relação às entradas totais',
            'formula': '(caixa_atual / total_entradas) * 100',
            'unidade': '%'
        },
        'caixa_estimado': {
            'valor': kpis['caixa_estimado'],
            'explicacao': 'Caixa atual + Cachês de shows CONFIRMADOS',
            'formula': 'caixa_atual + SUM(shows[status=="CONFIRMADO"].cache_acordado)',
            'unidade': 'R$'
        },
        'shows_sem_entrada_paga': {
            'valor': kpis['shows_sem_entrada_paga'],
            'explicacao': 'Shows realizados sem recebimento registrado',
            'formula': 'COUNT(shows_realizados sem transação ENTRADA PAGA associada)',
            'unidade': 'shows'
        },
        'kpi_publico': {
            'valor': kpis['kpi_publico'],
            'explicacao': 'Índice de performance de público (0-100)',
            'formula': '(público_médio * frequência_shows) / meta_público * 100',
            'unidade': 'score'
        },
        'despesas_fixas_mensais': {
            'valor': kpis['despesas_fixas_mensais'],
            'explicacao': 'Média mensal de despesas fixas',
            'formula': 'MÉDIA(despesas_fixas agrupadas por mês)',
            'unidade': 'R$/mês'
        }
    }
    
    return explanations