"""
Componentes de UI reutilizáveis
Implementa cards de KPI, filtros, gráficos e sidebar
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional, Tuple
import numpy as np

def setup_page_config():
    """
    Configuração global da página Streamlit
    """
    st.set_page_config(
        page_title="Rockbuzz Finance",
        page_icon="🎸",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/seu-usuario/rockbuzz-finance',
            'Report a bug': 'https://github.com/seu-usuario/rockbuzz-finance/issues',
            'About': "Dashboard Financeiro Profissional para Bandas"
        }
    )
    
    # CSS personalizado
    try:
        with open("assets/styles.css", "r") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except:
        # CSS fallback
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #FF4B4B;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)

def render_sidebar():
    """
    Renderiza sidebar com logo, navegação e filtros - Versão Corrigida
    """
    with st.sidebar:
        # Logo e título
        col1, col2 = st.columns([1, 3])
        with col1:
            try:
                st.image("assets/logo.png", width=50)
            except:
                st.markdown("🎸")
        with col2:
            st.markdown("### Rockbuzz Finance")
        
        st.divider()
        
        # Informações do usuário
        if st.session_state.get("authenticated", False):
            user_name = st.session_state.get("user_name", "Usuário")
            user_role = st.session_state.get("user_role", "membro")
            
            st.markdown(f"**👤 {user_name}**")
            st.caption(f"_{user_role}_")
            
            if st.button("🚪 Sair", use_container_width=True, type="secondary"):
                from core.auth import logout
                logout()
        
        st.divider()
        
        # Navegação principal
        st.markdown("### 📋 Navegação")
        
        # Páginas principais
        menu_pages = {
            "🏠 Home": "Home",
            "🎸 Shows": "Shows",
            "💰 Transações": "Transacoes",
            "📊 Relatórios & Projeções": "Relatorios",
            "📝 Cadastro de Registros": "Cadastros"
        }
        
        for label, page in menu_pages.items():
            if st.button(
                label, 
                key=f"menu_{page}",
                use_container_width=True,
                type="secondary" if st.session_state.get("current_page") == page else "primary"
            ):
                st.session_state.current_page = page
                st.rerun()
        
        st.divider()
        
        # Análises rápidas (subpáginas)
        st.markdown("### 📈 Análises")
        
        quick_analyses = {
            "📉 Receitas vs Despesas": "ReceitasDespesas",
            "💸 Despesas Detalhadas": "Despesas",
            "💰 Receitas Detalhadas": "Receitas"
        }
        
        for label, page in quick_analyses.items():
            if st.button(
                label,
                key=f"quick_{page}",
                use_container_width=True,
                type="secondary"
            ):
                st.session_state.current_page = page
                st.rerun()
        
        st.divider()
        
        # Filtros globais
        render_global_filters()
        
        st.divider()
        
        # Status do sistema
        col_status1, col_status2 = st.columns(2)
        
        with col_status1:
            if st.session_state.get("data_source"):
                st.caption(f"📊 {st.session_state.data_source}")
        
        with col_status2:
            if st.session_state.get("last_cache_update"):
                last_update = st.session_state.last_cache_update
                if isinstance(last_update, str):
                    from datetime import datetime
                    last_update = datetime.fromisoformat(last_update)
                st.caption(f"🔄 {last_update.strftime('%H:%M')}")
        
        # Botão para atualizar
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            from core.data_loader import data_loader
            data_loader.load_all_data(force_refresh=True)
            st.rerun()
        
        # Status do sistema
        if st.session_state.get("data_source"):
            st.caption(f"📊 Fonte: {st.session_state.data_source}")
        
        if st.session_state.get("last_cache_update"):
            last_update = st.session_state.last_cache_update
            if isinstance(last_update, str):
                last_update = datetime.fromisoformat(last_update)
            st.caption(f"🔄 Atualizado: {last_update.strftime('%H:%M')}")

def render_global_filters():
    """
    Renderiza filtros globais de período
    """
    st.subheader("📅 Filtros de Período")
    
    period_options = {
        "Mês atual": "current_month",
        "Mês anterior": "last_month",
        "Últimos 6 meses": "last_6_months",
        "Ano atual": "current_year",
        "Ano anterior": "last_year",
        "Todo período": "all_time"
    }
    
    selected_period = st.selectbox(
        "Selecione o período",
        list(period_options.keys()),
        index=0,
        key="global_period_filter"
    )
    
    # Calcular datas baseadas no período selecionado
    today = datetime.now()
    start_date, end_date = get_period_dates(selected_period)
    
    # Armazenar no session state
    st.session_state.filter_period = selected_period
    st.session_state.filter_start_date = start_date
    st.session_state.filter_end_date = end_date
    
    # Mostrar período selecionado
    if start_date and end_date:
        st.caption(f"Período: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")

def get_period_dates(period: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Calcula datas de início e fim baseadas no período selecionado
    
    Args:
        period: Período selecionado
        
    Returns:
        Tupla com (data_inicio, data_fim)
    """
    today = datetime.now()
    
    if period == "Mês atual":
        start_date = today.replace(day=1)
        end_date = today
    elif period == "Mês anterior":
        start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        end_date = today.replace(day=1) - timedelta(days=1)
    elif period == "Últimos 6 meses":
        start_date = today - timedelta(days=180)
        end_date = today
    elif period == "Ano atual":
        start_date = today.replace(month=1, day=1)
        end_date = today
    elif period == "Ano anterior":
        start_date = today.replace(year=today.year-1, month=1, day=1)
        end_date = today.replace(year=today.year-1, month=12, day=31)
    else:  # Todo período
        start_date = None
        end_date = None
    
    return start_date, end_date

def render_kpi_card(title: str, value, 
                   format_str: str = "{:,.2f}",
                   delta: Optional[float] = None,
                   help_text: str = "",
                   icon: str = "📊"):
    """
    Renderiza um card de KPI estilizado
    
    Args:
        title: Título do KPI
        value: Valor a ser exibido
        format_str: String de formatação
        delta: Valor delta para mostrar variação
        help_text: Texto de ajuda
        icon: Ícone do card
    """
    # Formatar valor
    if isinstance(value, (int, float)):
        if value >= 1000000:
            formatted_value = f"R$ {value/1000000:.1f}M"
        elif value >= 1000:
            formatted_value = f"R$ {value/1000:.1f}K"
        else:
            formatted_value = format_str.format(value)
    else:
        formatted_value = str(value)
    
    # Determinar cor do delta
    delta_color = ""
    delta_symbol = ""
    if delta is not None:
        if delta > 0:
            delta_color = "positive"
            delta_symbol = "▲"
        elif delta < 0:
            delta_color = "negative"
            delta_symbol = "▼"
    
    # Criar card
    with st.container():
        col1, col2 = st.columns([1, 4])
        
        with col1:
            st.markdown(f"<h1 style='text-align: center;'>{icon}</h1>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"<div class='kpi-label'>{title}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='kpi-value'>{formatted_value}</div>", unsafe_allow_html=True)
            
            if delta is not None and delta != 0:
                delta_text = f"{delta_symbol} {abs(delta):.1f}%"
                st.markdown(f"<div class='{delta_color}' style='font-size: 0.8rem;'>{delta_text}</div>", 
                          unsafe_allow_html=True)
        
        if help_text:
            st.caption(help_text)

def render_kpi_grid(kpis: Dict[str, Dict], columns: int = 4):
    """
    Renderiza grid de cards de KPI
    
    Args:
        kpis: Dicionário com KPIs
        columns: Número de colunas no grid
    """
    kpi_items = list(kpis.items())
    
    for i in range(0, len(kpi_items), columns):
        cols = st.columns(columns)
        
        for j in range(columns):
            if i + j < len(kpi_items):
                kpi_name, kpi_data = kpi_items[i + j]
                
                with cols[j]:
                    render_kpi_card(
                        title=kpi_data.get('explicacao', kpi_name),
                        value=kpi_data.get('valor', 0),
                        format_str="{:,.2f}" if kpi_data.get('unidade') == 'R$' else "{:.0f}",
                        help_text=f"Fórmula: {kpi_data.get('formula', '')}"
                    )

def create_revenue_trend_chart(transactions_df: pd.DataFrame, 
                             shows_df: pd.DataFrame) -> go.Figure:
    """
    Cria gráfico de tendência de entradas por show
    
    Args:
        transactions_df: DataFrame de transações
        shows_df: DataFrame de shows
        
    Returns:
        Figura Plotly
    """
    # Preparar dados
    transacoes_entrada = transactions_df[
        (transactions_df['tipo'] == 'ENTRADA') & 
        (transactions_df['payment_status'] == 'PAGO')
    ].copy()
    
    if transacoes_entrada.empty:
        return create_empty_chart("Sem dados de entrada")
    
    # Agrupar por show
    entradas_por_show = transacoes_entrada.groupby('show_id')['valor'].sum().reset_index()
    
    # Juntar com informações do show
    entradas_por_show = entradas_por_show.merge(
        shows_df[['show_id', 'data_show', 'casa', 'cidade']],
        on='show_id',
        how='left'
    )
    
    # Ordenar por data
    entradas_por_show = entradas_por_show.sort_values('data_show')
    
    # Criar gráfico
    fig = go.Figure()
    
    # Adicionar linha de tendência
    fig.add_trace(go.Scatter(
        x=entradas_por_show['data_show'],
        y=entradas_por_show['valor'],
        mode='lines+markers',
        name='Entradas',
        line=dict(color='#667eea', width=3),
        marker=dict(size=10, color='#764ba2')
    ))
    
    # Calcular média móvel (3 períodos)
    if len(entradas_por_show) >= 3:
        entradas_por_show['media_movel'] = entradas_por_show['valor'].rolling(window=3).mean()
        
        fig.add_trace(go.Scatter(
            x=entradas_por_show['data_show'],
            y=entradas_por_show['media_movel'],
            mode='lines',
            name='Média Móvel (3)',
            line=dict(color='#FF4B4B', width=2, dash='dash')
        ))
    
    # Layout
    fig.update_layout(
        title="Tendência de Entradas por Show",
        xaxis_title="Data do Show",
        yaxis_title="Valor (R$)",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig

def create_cash_flow_chart(transactions_df: pd.DataFrame) -> go.Figure:
    """
    Cria gráfico de fluxo de caixa
    
    Args:
        transactions_df: DataFrame de transações
        
    Returns:
        Figura Plotly
    """
    if transactions_df.empty:
        return create_empty_chart("Sem dados de transações")
    
    # Preparar dados
    transacoes = transactions_df.copy()
    transacoes['mes'] = transacoes['data'].dt.to_period('M').astype(str)
    
    # Agrupar por mês
    fluxo_mensal = transacoes.groupby('mes').apply(
        lambda x: pd.Series({
            'entradas': x[x['tipo'] == 'ENTRADA']['valor'].sum(),
            'saidas': x[x['tipo'] == 'SAIDA']['valor'].sum(),
            'saldo': x[x['tipo'] == 'ENTRADA']['valor'].sum() - x[x['tipo'] == 'SAIDA']['valor'].sum()
        })
    ).reset_index()
    
    # Ordenar por mês
    fluxo_mensal = fluxo_mensal.sort_values('mes')
    
    # Criar gráfico de barras empilhadas
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=fluxo_mensal['mes'],
        y=fluxo_mensal['entradas'],
        name='Entradas',
        marker_color='#00CC96'
    ))
    
    fig.add_trace(go.Bar(
        x=fluxo_mensal['mes'],
        y=fluxo_mensal['saidas'],
        name='Saídas',
        marker_color='#EF553B'
    ))
    
    # Adicionar linha de saldo acumulado
    fluxo_mensal['saldo_acumulado'] = fluxo_mensal['saldo'].cumsum()
    
    fig.add_trace(go.Scatter(
        x=fluxo_mensal['mes'],
        y=fluxo_mensal['saldo_acumulado'],
        name='Saldo Acumulado',
        mode='lines+markers',
        line=dict(color='#636EFA', width=3),
        yaxis='y2'
    ))
    
    # Layout
    fig.update_layout(
        title="Fluxo de Caixa Mensal",
        xaxis_title="Mês",
        yaxis_title="Valor (R$)",
        barmode='group',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        yaxis2=dict(
            title="Saldo Acumulado (R$)",
            overlaying='y',
            side='right'
        )
    )
    
    return fig

def create_revenue_forecast_chart(shows_df: pd.DataFrame) -> go.Figure:
    """
    Cria gráfico de previsão de entradas dos próximos shows
    
    Args:
        shows_df: DataFrame de shows
        
    Returns:
        Figura Plotly
    """
    # Filtrar shows confirmados
    shows_confirmados = shows_df[shows_df['status'] == 'CONFIRMADO'].copy()
    
    if shows_confirmados.empty:
        return create_empty_chart("Sem shows confirmados")
    
    # Ordenar por data
    shows_confirmados = shows_confirmados.sort_values('data_show')
    
    # Criar gráfico
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=shows_confirmados['data_show'],
        y=shows_confirmados['cache_acordado'],
        name='Cachê Acordado',
        marker_color='#AB63FA',
        text=shows_confirmados['casa'],
        hovertemplate="<b>%{text}</b><br>" +
                     "Data: %{x}<br>" +
                     "Cachê: R$ %{y:,.2f}<extra></extra>"
    ))
    
    # Adicionar previsão (80% do cachê acordado como receita esperada)
    shows_confirmados['receita_estimada'] = shows_confirmados['cache_acordado'] * 0.8
    
    fig.add_trace(go.Scatter(
        x=shows_confirmados['data_show'],
        y=shows_confirmados['receita_estimada'],
        name='Receita Estimada (80%)',
        mode='markers',
        marker=dict(size=12, color='#FFA15A'),
        hovertemplate="<b>Receita Estimada</b><br>" +
                     "Data: %{x}<br>" +
                     "Valor: R$ %{y:,.2f}<extra></extra>"
    ))
    
    # Layout
    fig.update_layout(
        title="Previsão de Entradas - Próximos Shows",
        xaxis_title="Data do Show",
        yaxis_title="Valor (R$)",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig

def create_expense_prediction_chart(transactions_df: pd.DataFrame) -> go.Figure:
    """
    Cria gráfico preditivo de despesas usando regressão linear
    
    Args:
        transactions_df: DataFrame de transações
        
    Returns:
        Figura Plotly
    """
    # Filtrar despesas
    despesas = transactions_df[
        (transactions_df['tipo'] == 'SAIDA') & 
        (transactions_df['payment_status'] == 'PAGO')
    ].copy()
    
    if despesas.empty or len(despesas) < 6:  # Mínimo de 6 pontos para previsão
        return create_empty_chart("Dados insuficientes para previsão")
    
    # Agrupar por mês
    despesas['mes_num'] = despesas['data'].dt.to_period('M').astype(str)
    despesas_mensais = despesas.groupby('mes_num')['valor'].sum().reset_index()
    
    # Converter mês para número sequencial
    despesas_mensais['mes_seq'] = range(len(despesas_mensais))
    
    # Ajustar modelo de regressão linear
    X = despesas_mensais[['mes_seq']].values
    y = despesas_mensais['valor'].values
    
    # Usar regressão linear do scikit-learn
    from sklearn.linear_model import LinearRegression
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Fazer previsão para próximos 3 meses
    future_months = 3
    X_future = np.array(range(len(despesas_mensais), len(despesas_mensais) + future_months)).reshape(-1, 1)
    y_pred = model.predict(X_future)
    
    # Criar gráfico
    fig = go.Figure()
    
    # Dados históricos
    fig.add_trace(go.Scatter(
        x=despesas_mensais['mes_num'],
        y=despesas_mensais['valor'],
        mode='lines+markers',
        name='Despesas Históricas',
        line=dict(color='#EF553B', width=3),
        marker=dict(size=8)
    ))
    
    # Linha de tendência
    fig.add_trace(go.Scatter(
        x=despesas_mensais['mes_num'],
        y=model.predict(X),
        mode='lines',
        name='Tendência Linear',
        line=dict(color='#00CC96', width=2, dash='dash')
    ))
    
    # Previsão
    future_dates = [f"M+{i+1}" for i in range(future_months)]
    
    fig.add_trace(go.Scatter(
        x=future_dates,
        y=y_pred,
        mode='lines+markers',
        name='Previsão (3 meses)',
        line=dict(color='#AB63FA', width=3, dash='dot'),
        marker=dict(size=10, symbol='diamond')
    ))
    
    # Adicionar intervalo de confiança (simplificado)
    std_dev = np.std(y - model.predict(X))
    fig.add_trace(go.Scatter(
        x=future_dates + future_dates[::-1],
        y=list(y_pred + std_dev) + list(y_pred - std_dev)[::-1],
        fill='toself',
        fillcolor='rgba(171, 99, 250, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Intervalo de Confiança',
        showlegend=True
    ))
    
    # Layout
    fig.update_layout(
        title="Previsão de Despesas - Regressão Linear",
        xaxis_title="Período",
        yaxis_title="Valor (R$)",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )
    
    return fig

def create_empty_chart(message: str) -> go.Figure:
    """
    Cria gráfico vazio com mensagem
    
    Args:
        message: Mensagem a ser exibida
        
    Returns:
        Figura Plotly vazia
    """
    fig = go.Figure()
    
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16)
    )
    
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=300
    )
    
    return fig

def render_footer():
    """
    Renderiza rodapé da aplicação
    """
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("🎸 Rockbuzz Finance v1.0")
    
    with col2:
        st.caption("Dashboard Financeiro Profissional")
    
    with col3:
        from datetime import datetime
        st.caption(f"© {datetime.now().year} - Todos os direitos reservados")