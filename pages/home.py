"""
Pagina inicial do dashboard - Design Moderno Dark Theme
Exibe KPIs principais com sparklines, graficos de area, pizza e analises
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

from core.data_loader import data_loader
from core.metrics import calculate_kpis_with_explanation
from core.filters import DataFilter, display_current_filters

DARK_THEME = {
    'bg_color': '#0d1117',
    'card_bg': '#161b22',
    'card_border': '#30363d',
    'text_primary': '#c9d1d9',
    'text_secondary': '#8b949e',
    'accent_blue': '#58a6ff',
    'accent_green': '#3fb950',
    'accent_red': '#f85149',
    'accent_purple': '#a371f7',
    'accent_orange': '#d29922',
    'accent_cyan': '#39c5cf',
    'grid_color': '#21262d',
}

def create_sparkline(values, color='#58a6ff', height=50):
    """Cria um mini grafico sparkline para os cards de KPI"""
    if not values or len(values) < 2:
        values = [0, 0, 0, 0, 0]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        y=values,
        mode='lines',
        fill='tozeroy',
        line=dict(color=color, width=2),
        fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.2)',
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False
    )
    
    return fig

def render_kpi_card_with_sparkline(title, value, sparkline_data, delta=None, delta_text=None, color='#58a6ff', prefix='R$ ', comparison_period=None):
    """Renderiza um card de KPI com sparkline integrado"""
    
    delta_html = ""
    if delta is not None:
        delta_color = DARK_THEME['accent_green'] if delta >= 0 else DARK_THEME['accent_red']
        delta_symbol = "+" if delta >= 0 else ""
        delta_display = delta_text if delta_text else f"{delta_symbol}{delta:.1f}%"
        comparison_text = comparison_period if comparison_period else "em relacao ao mes anterior"
        delta_html = f'''<div style="color: {delta_color}; font-size: 0.85rem; margin-top: 4px;">
            {delta_display}
            <span style="color: {DARK_THEME['text_secondary']}; font-size: 0.75rem;"> {comparison_text}</span>
        </div>'''
    
    if isinstance(value, (int, float)):
        if abs(value) >= 1000000:
            formatted_value = f"{prefix}{value/1000000:.1f}M"
        elif abs(value) >= 1000:
            formatted_value = f"{prefix}{value/1000:.1f}K"
        else:
            formatted_value = f"{prefix}{value:,.0f}" if isinstance(value, int) else f"{prefix}{value:,.2f}"
    else:
        formatted_value = str(value)
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
        border: 1px solid {DARK_THEME['card_border']};
        border-radius: 12px;
        padding: 1.2rem;
        height: 100%;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    ">
        <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px;">
            {title}
        </div>
        <div style="color: {color}; font-size: 1.8rem; font-weight: 700; margin: 8px 0;">
            {formatted_value}
        </div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)
    
    if sparkline_data and len(sparkline_data) > 1:
        fig = create_sparkline(sparkline_data, color)
        st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})

def create_area_chart(df, x_col, y_col, title, color='#58a6ff', show_gradient=True):
    """Cria grafico de area com tema dark"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='lines',
        fill='tozeroy' if show_gradient else None,
        line=dict(color=color, width=2),
        fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.3)',
        name=title
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(color=DARK_THEME['text_primary'], size=14)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=DARK_THEME['text_secondary']),
        height=250,
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(
            showgrid=True,
            gridcolor=DARK_THEME['grid_color'],
            linecolor=DARK_THEME['card_border'],
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=DARK_THEME['grid_color'],
            linecolor=DARK_THEME['card_border'],
            tickfont=dict(size=10)
        ),
        showlegend=False,
        hovermode='x unified'
    )
    
    return fig

def create_multi_line_chart(df, x_col, y_cols, title, colors=None):
    """Cria grafico de multiplas linhas"""
    if colors is None:
        colors = [DARK_THEME['accent_blue'], DARK_THEME['accent_green'], DARK_THEME['accent_purple']]
    
    fig = go.Figure()
    
    for i, y_col in enumerate(y_cols):
        if y_col in df.columns:
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode='lines+markers',
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=6),
                name=y_col
            ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(color=DARK_THEME['text_primary'], size=14)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=DARK_THEME['text_secondary']),
        height=300,
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(
            showgrid=True,
            gridcolor=DARK_THEME['grid_color'],
            linecolor=DARK_THEME['card_border']
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=DARK_THEME['grid_color'],
            linecolor=DARK_THEME['card_border']
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            font=dict(size=10)
        ),
        hovermode='x unified'
    )
    
    return fig

def create_pie_chart(labels, values, title, colors=None):
    """Cria grafico de pizza com tema dark"""
    if colors is None:
        colors = [
            DARK_THEME['accent_blue'],
            DARK_THEME['accent_green'],
            DARK_THEME['accent_purple'],
            DARK_THEME['accent_orange'],
            DARK_THEME['accent_cyan'],
            DARK_THEME['accent_red']
        ]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=colors[:len(labels)]),
        textinfo='percent',
        textfont=dict(color='white', size=11),
        hovertemplate='<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(text=title, font=dict(color=DARK_THEME['text_primary'], size=14)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=DARK_THEME['text_secondary']),
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(
            orientation='v',
            yanchor='middle',
            y=0.5,
            xanchor='left',
            x=1.05,
            font=dict(size=10, color=DARK_THEME['text_secondary'])
        ),
        showlegend=True
    )
    
    return fig

def create_gauge_chart(value, max_value, title, color='#58a6ff'):
    """Cria grafico de gauge/medidor"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title=dict(text=title, font=dict(color=DARK_THEME['text_primary'], size=14)),
        number=dict(font=dict(color=color, size=24), suffix='%'),
        gauge=dict(
            axis=dict(
                range=[0, max_value],
                tickcolor=DARK_THEME['text_secondary'],
                tickfont=dict(color=DARK_THEME['text_secondary'])
            ),
            bar=dict(color=color),
            bgcolor=DARK_THEME['grid_color'],
            bordercolor=DARK_THEME['card_border'],
            steps=[
                dict(range=[0, max_value * 0.3], color='rgba(248, 81, 73, 0.3)'),
                dict(range=[max_value * 0.3, max_value * 0.7], color='rgba(210, 153, 34, 0.3)'),
                dict(range=[max_value * 0.7, max_value], color='rgba(63, 185, 80, 0.3)')
            ]
        )
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=DARK_THEME['text_secondary']),
        height=200,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def get_monthly_data(transactions_df):
    """Agrupa transacoes por mes"""
    if transactions_df.empty or 'data' not in transactions_df.columns:
        return pd.DataFrame()
    
    df = transactions_df.copy()
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.dropna(subset=['data'])
    
    if df.empty:
        return pd.DataFrame()
    
    df['mes'] = df['data'].dt.to_period('M').astype(str)
    
    monthly = df.groupby(['mes', 'tipo']).agg({'valor': 'sum'}).reset_index()
    monthly_pivot = monthly.pivot(index='mes', columns='tipo', values='valor').fillna(0).reset_index()
    
    if 'ENTRADA' not in monthly_pivot.columns:
        monthly_pivot['ENTRADA'] = 0
    if 'SAIDA' not in monthly_pivot.columns:
        monthly_pivot['SAIDA'] = 0
    
    monthly_pivot['saldo'] = monthly_pivot['ENTRADA'] - monthly_pivot['SAIDA']
    monthly_pivot = monthly_pivot.sort_values('mes')
    
    return monthly_pivot

def get_category_distribution(transactions_df, tipo='SAIDA'):
    """Obtem distribuicao por categoria"""
    if transactions_df.empty:
        return pd.DataFrame()
    
    df = transactions_df[
        (transactions_df['tipo'] == tipo) & 
        (transactions_df['payment_status'] == 'PAGO')
    ].copy()
    
    if df.empty or 'categoria' not in df.columns:
        return pd.DataFrame()
    
    category_dist = df.groupby('categoria')['valor'].sum().reset_index()
    category_dist = category_dist.sort_values('valor', ascending=False)
    
    return category_dist

def render_recent_transactions_table(transactions_df, limit=5):
    """Renderiza tabela de transacoes recentes"""
    if transactions_df.empty:
        st.info("Nenhuma transacao encontrada")
        return
    
    df = transactions_df.copy()
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df = df.sort_values('data', ascending=False).head(limit)
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
        border: 1px solid {DARK_THEME['card_border']};
        border-radius: 12px;
        padding: 1rem;
        margin-top: 0.5rem;
    ">
        <h4 style="color: {DARK_THEME['text_primary']}; margin-bottom: 1rem; font-size: 14px;">
            Transacoes Recentes
        </h4>
    """, unsafe_allow_html=True)
    
    for _, row in df.iterrows():
        tipo = row.get('tipo', '')
        valor = row.get('valor', 0)
        descricao = row.get('descricao', 'Sem descricao')[:30]
        data = row.get('data', '')
        
        if isinstance(data, pd.Timestamp):
            data_str = data.strftime('%d/%m')
        else:
            data_str = str(data)[:10]
        
        color = DARK_THEME['accent_green'] if tipo == 'ENTRADA' else DARK_THEME['accent_red']
        symbol = '+' if tipo == 'ENTRADA' else '-'
        
        st.markdown(f"""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid {DARK_THEME['grid_color']};
        ">
            <div>
                <div style="color: {DARK_THEME['text_primary']}; font-size: 0.9rem;">{descricao}</div>
                <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.75rem;">{data_str}</div>
            </div>
            <div style="color: {color}; font-weight: 600;">
                {symbol}R$ {valor:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_upcoming_shows_list(shows_df, limit=5):
    """Renderiza lista de proximos shows"""
    if shows_df.empty:
        st.info("Nenhum show encontrado")
        return
    
    df = shows_df.copy()
    df['data_show'] = pd.to_datetime(df['data_show'], errors='coerce')
    
    today = datetime.now()
    upcoming = df[
        (df['status'] == 'CONFIRMADO') & 
        (df['data_show'] >= today)
    ].sort_values('data_show').head(limit)
    
    if upcoming.empty:
        st.info("Nenhum show confirmado")
        return
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
        border: 1px solid {DARK_THEME['card_border']};
        border-radius: 12px;
        padding: 1rem;
        margin-top: 0.5rem;
    ">
        <h4 style="color: {DARK_THEME['text_primary']}; margin-bottom: 1rem; font-size: 14px;">
            Proximos Shows
        </h4>
    """, unsafe_allow_html=True)
    
    for _, row in upcoming.iterrows():
        casa = row.get('casa', 'Local nao definido')
        cidade = row.get('cidade', '')
        data_show = row.get('data_show', '')
        cache = row.get('cache_acordado', 0)
        
        if isinstance(data_show, pd.Timestamp):
            data_str = data_show.strftime('%d/%m/%Y')
        else:
            data_str = str(data_show)[:10]
        
        st.markdown(f"""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid {DARK_THEME['grid_color']};
        ">
            <div>
                <div style="color: {DARK_THEME['text_primary']}; font-size: 0.9rem;">{casa}</div>
                <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.75rem;">{cidade} - {data_str}</div>
            </div>
            <div style="color: {DARK_THEME['accent_green']}; font-weight: 600;">
                R$ {cache:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    """Funcao principal da pagina Home - Dashboard Moderno"""
    
    with st.spinner("Carregando dados..."):
        data = data_loader.load_all_data()
    
    if not data or 'transactions' not in data or data['transactions'].empty:
        st.error("Nao foi possivel carregar os dados financeiros.")
        st.info("Por favor, verifique a conexao com o Google Sheets ou o arquivo Excel local.")
        return
    
    filtered_data = DataFilter.apply_global_filters(data)
    
    display_current_filters()
    
    transactions_df = filtered_data.get('transactions', pd.DataFrame())
    shows_df = filtered_data.get('shows', pd.DataFrame())
    
    start_date = st.session_state.get('filter_start_date')
    end_date = st.session_state.get('filter_end_date')
    
    kpis = calculate_kpis_with_explanation(filtered_data, start_date, end_date)
    
    total_entradas = kpis.get('total_entradas', {}).get('valor', 0)
    total_despesas = kpis.get('total_despesas', {}).get('valor', 0)
    caixa_atual = kpis.get('caixa_atual', {}).get('valor', 0)
    a_receber = kpis.get('a_receber', {}).get('valor', 0)
    total_shows = kpis.get('total_shows_realizados', {}).get('valor', 0)
    publico_medio = kpis.get('publico_medio', {}).get('valor', 0)
    
    monthly_data = get_monthly_data(transactions_df)
    
    entradas_trend = monthly_data['ENTRADA'].tolist() if not monthly_data.empty and 'ENTRADA' in monthly_data.columns else [0]
    despesas_trend = monthly_data['SAIDA'].tolist() if not monthly_data.empty and 'SAIDA' in monthly_data.columns else [0]
    saldo_trend = monthly_data['saldo'].tolist() if not monthly_data.empty and 'saldo' in monthly_data.columns else [0]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta_receitas = ((entradas_trend[-1] - entradas_trend[-2]) / entradas_trend[-2] * 100) if len(entradas_trend) > 1 and entradas_trend[-2] != 0 else 0
        render_kpi_card_with_sparkline(
            "Total Receitas",
            total_entradas,
            entradas_trend,
            delta=delta_receitas,
            color=DARK_THEME['accent_green']
        )
    
    with col2:
        delta_despesas = ((despesas_trend[-1] - despesas_trend[-2]) / despesas_trend[-2] * 100) if len(despesas_trend) > 1 and despesas_trend[-2] != 0 else 0
        render_kpi_card_with_sparkline(
            "Total Despesas",
            total_despesas,
            despesas_trend,
            delta=delta_despesas,
            color=DARK_THEME['accent_red']
        )
    
    with col3:
        render_kpi_card_with_sparkline(
            "Caixa Atual",
            caixa_atual,
            saldo_trend,
            color=DARK_THEME['accent_blue']
        )
    
    with col4:
        margem = ((total_entradas - total_despesas) / total_entradas * 100) if total_entradas > 0 else 0
        render_kpi_card_with_sparkline(
            "Margem de Lucro",
            f"{margem:.1f}%",
            saldo_trend,
            prefix='',
            color=DARK_THEME['accent_purple']
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # KPI de Valor Efetivo por Show
    valor_bruto_shows = 0
    custos_operacionais = 0
    
    # Calcular valor bruto dos shows (receitas de shows)
    if not transactions_df.empty:
        receitas_shows = transactions_df[
            (transactions_df['tipo'] == 'ENTRADA') & 
            (transactions_df['payment_status'] == 'PAGO')
        ]
        if not receitas_shows.empty:
            valor_bruto_shows = receitas_shows['valor'].sum()
        
        # Calcular custos operacionais (despesas pagas)
        despesas = transactions_df[
            (transactions_df['tipo'] == 'SAIDA') & 
            (transactions_df['payment_status'] == 'PAGO')
        ]
        if not despesas.empty:
            custos_operacionais = despesas['valor'].sum()
    
    valor_efetivo = valor_bruto_shows - custos_operacionais
    percentual_retido = (valor_efetivo / valor_bruto_shows * 100) if valor_bruto_shows > 0 else 0
    
    col_valor1, col_valor2, col_valor3 = st.columns(3)
    
    with col_valor1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
            border: 1px solid {DARK_THEME['card_border']};
            border-radius: 12px;
            padding: 1.2rem;
            border-left: 4px solid {DARK_THEME['accent_green']};
        ">
            <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.8rem; text-transform: uppercase;">
                VALOR BRUTO
            </div>
            <div style="color: {DARK_THEME['accent_green']}; font-size: 1.6rem; font-weight: 700; margin: 8px 0;">
                R$ {valor_bruto_shows:,.2f}
            </div>
            <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.75rem;">
                Total de receitas recebidas
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_valor2:
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
            border: 1px solid {DARK_THEME['card_border']};
            border-radius: 12px;
            padding: 1.2rem;
            border-left: 4px solid {DARK_THEME['accent_red']};
        ">
            <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.8rem; text-transform: uppercase;">
                CUSTOS OPERACIONAIS
            </div>
            <div style="color: {DARK_THEME['accent_red']}; font-size: 1.6rem; font-weight: 700; margin: 8px 0;">
                R$ {custos_operacionais:,.2f}
            </div>
            <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.75rem;">
                Equipe, equipamentos, posts patrocinados, etc.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_valor3:
        valor_color = DARK_THEME['accent_cyan'] if valor_efetivo >= 0 else DARK_THEME['accent_red']
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
            border: 1px solid {DARK_THEME['card_border']};
            border-radius: 12px;
            padding: 1.2rem;
            border-left: 4px solid {valor_color};
        ">
            <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.8rem; text-transform: uppercase;">
                SALDO LÍQUIDO
            </div>
            <div style="color: {valor_color}; font-size: 1.6rem; font-weight: 700; margin: 8px 0;">
                R$ {valor_efetivo:,.2f}
            </div>
            <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.75rem;">
                {percentual_retido:.1f}% do valor bruto retido
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
            border: 1px solid {DARK_THEME['card_border']};
            border-radius: 12px;
            padding: 1rem;
        ">
            <h4 style="color: {DARK_THEME['text_primary']}; margin: 0 0 0.5rem 0; font-size: 14px;">
                Evolucao das Receitas
            </h4>
        """, unsafe_allow_html=True)
        
        if not monthly_data.empty:
            fig = create_area_chart(
                monthly_data, 'mes', 'ENTRADA',
                '',
                color=DARK_THEME['accent_green']
            )
            st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
        else:
            st.info("Dados insuficientes para o grafico")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
            border: 1px solid {DARK_THEME['card_border']};
            border-radius: 12px;
            padding: 1rem;
        ">
            <h4 style="color: {DARK_THEME['text_primary']}; margin: 0 0 0.5rem 0; font-size: 14px;">
                Evolucao das Despesas
            </h4>
        """, unsafe_allow_html=True)
        
        if not monthly_data.empty:
            fig = create_area_chart(
                monthly_data, 'mes', 'SAIDA',
                '',
                color=DARK_THEME['accent_red']
            )
            st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
        else:
            st.info("Dados insuficientes para o grafico")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
            border: 1px solid {DARK_THEME['card_border']};
            border-radius: 12px;
            padding: 1rem;
        ">
            <h4 style="color: {DARK_THEME['text_primary']}; margin: 0 0 0.5rem 0; font-size: 14px;">
                Distribuicao de Despesas
            </h4>
        """, unsafe_allow_html=True)
        
        category_dist = get_category_distribution(transactions_df, 'SAIDA')
        
        if not category_dist.empty:
            top_categories = category_dist.head(6)
            fig = create_pie_chart(
                top_categories['categoria'].tolist(),
                top_categories['valor'].tolist(),
                ''
            )
            st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
        else:
            st.info("Sem dados de categorias")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
            border: 1px solid {DARK_THEME['card_border']};
            border-radius: 12px;
            padding: 1rem;
        ">
            <h4 style="color: {DARK_THEME['text_primary']}; margin: 0 0 0.5rem 0; font-size: 14px;">
                Receitas vs Despesas
            </h4>
        """, unsafe_allow_html=True)
        
        if not monthly_data.empty and len(monthly_data) > 1:
            fig = create_multi_line_chart(
                monthly_data, 'mes', ['ENTRADA', 'SAIDA'],
                '',
                colors=[DARK_THEME['accent_green'], DARK_THEME['accent_red']]
            )
            st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
        else:
            st.info("Dados insuficientes")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
            border: 1px solid {DARK_THEME['card_border']};
            border-radius: 12px;
            padding: 1rem;
        ">
            <h4 style="color: {DARK_THEME['text_primary']}; margin: 0 0 0.5rem 0; font-size: 14px;">
                Saude Financeira
            </h4>
        """, unsafe_allow_html=True)
        
        fig = create_gauge_chart(
            min(margem, 100) if margem > 0 else 0,
            100,
            '',
            color=DARK_THEME['accent_cyan']
        )
        st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        render_recent_transactions_table(transactions_df, limit=5)
    
    with col2:
        render_upcoming_shows_list(shows_df, limit=5)
    
    with col3:
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
            border: 1px solid {DARK_THEME['card_border']};
            border-radius: 12px;
            padding: 1rem;
            margin-top: 0.5rem;
        ">
            <h4 style="color: {DARK_THEME['text_primary']}; margin-bottom: 1rem; font-size: 14px;">
                Resumo Rapido
            </h4>
            <div style="padding: 8px 0; border-bottom: 1px solid {DARK_THEME['grid_color']};">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: {DARK_THEME['text_secondary']};">Shows Realizados</span>
                    <span style="color: {DARK_THEME['accent_blue']}; font-weight: 600;">{total_shows}</span>
                </div>
            </div>
            <div style="padding: 8px 0; border-bottom: 1px solid {DARK_THEME['grid_color']};">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: {DARK_THEME['text_secondary']};">Publico Medio</span>
                    <span style="color: {DARK_THEME['accent_purple']}; font-weight: 600;">{publico_medio:.0f}</span>
                </div>
            </div>
            <div style="padding: 8px 0; border-bottom: 1px solid {DARK_THEME['grid_color']};">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: {DARK_THEME['text_secondary']};">A Receber</span>
                    <span style="color: {DARK_THEME['accent_green']}; font-weight: 600;">R$ {a_receber:,.2f}</span>
                </div>
            </div>
            <div style="padding: 8px 0;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: {DARK_THEME['text_secondary']};">Lucro Liquido</span>
                    <span style="color: {DARK_THEME['accent_cyan']}; font-weight: 600;">R$ {(total_entradas - total_despesas):,.2f}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Atualizar Dados", width='stretch'):
        data_loader.load_all_data(force_refresh=True)
        st.rerun()

if __name__ == "__main__":
    main()
