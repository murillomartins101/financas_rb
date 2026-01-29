"""
Pagina de relatorios e projecoes com analises preditivas
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

from core.data_loader import data_loader

DARK_THEME = {
    'bg': '#0d1117',
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
    'grid_color': '#21262d'
}

def calculate_trend(values):
    """Calcula tendencia linear simples"""
    if len(values) < 2:
        return 0
    x = np.arange(len(values))
    coeffs = np.polyfit(x, values, 1)
    return coeffs[0]

def forecast_values(values, periods=3):
    """Projeta valores futuros baseado em tendencia"""
    if len(values) < 2:
        return [values[-1] if len(values) > 0 else 0] * periods
    
    x = np.arange(len(values))
    coeffs = np.polyfit(x, values, 1)
    
    future_x = np.arange(len(values), len(values) + periods)
    forecast = np.polyval(coeffs, future_x)
    return [max(0, v) for v in forecast]

def main():
    """Pagina de relatorios com analises preditivas"""
    st.title("Relatorios e Projecoes")
    
    with st.spinner("Carregando dados..."):
        data = data_loader.load_all_data()
    
    if not data or 'transactions' not in data:
        st.error("Nao foi possivel carregar os dados")
        return
    
    transactions_df = data.get('transactions', pd.DataFrame()).copy()
    shows_df = data.get('shows', pd.DataFrame()).copy()
    
    if transactions_df.empty:
        st.warning("Nenhuma transacao encontrada para analise")
        return
    
    if 'data' in transactions_df.columns:
        transactions_df['data'] = pd.to_datetime(transactions_df['data'], errors='coerce')
        transactions_df = transactions_df.dropna(subset=['data'])
        transactions_df['mes'] = transactions_df['data'].dt.to_period('M')
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_receitas = transactions_df[transactions_df['tipo'] == 'ENTRADA']['valor'].sum() if 'tipo' in transactions_df.columns else 0
    total_despesas = transactions_df[transactions_df['tipo'] == 'SAIDA']['valor'].sum() if 'tipo' in transactions_df.columns else 0
    saldo = total_receitas - total_despesas
    margem = (saldo / total_receitas * 100) if total_receitas > 0 else 0
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid {DARK_THEME['accent_green']};">
            <p style="color: {DARK_THEME['text_secondary']}; margin: 0; font-size: 0.85rem;">TOTAL RECEITAS</p>
            <h2 style="color: {DARK_THEME['accent_green']}; margin: 5px 0;">R$ {total_receitas:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid {DARK_THEME['accent_red']};">
            <p style="color: {DARK_THEME['text_secondary']}; margin: 0; font-size: 0.85rem;">TOTAL DESPESAS</p>
            <h2 style="color: {DARK_THEME['accent_red']}; margin: 5px 0;">R$ {total_despesas:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        saldo_color = DARK_THEME['accent_green'] if saldo >= 0 else DARK_THEME['accent_red']
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid {saldo_color};">
            <p style="color: {DARK_THEME['text_secondary']}; margin: 0; font-size: 0.85rem;">SALDO</p>
            <h2 style="color: {saldo_color}; margin: 5px 0;">R$ {saldo:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid {DARK_THEME['accent_cyan']};">
            <p style="color: {DARK_THEME['text_secondary']}; margin: 0; font-size: 0.85rem;">MARGEM</p>
            <h2 style="color: {DARK_THEME['accent_cyan']}; margin: 5px 0;">{margem:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
        border: 1px solid {DARK_THEME['card_border']};
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    ">
        <h3 style="color: {DARK_THEME['text_primary']}; margin-bottom: 0.5rem;">Analise Preditiva - Projecao de Receitas e Despesas</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if 'mes' in transactions_df.columns:
        monthly_receitas = transactions_df[transactions_df['tipo'] == 'ENTRADA'].groupby('mes')['valor'].sum()
        monthly_despesas = transactions_df[transactions_df['tipo'] == 'SAIDA'].groupby('mes')['valor'].sum()
        
        all_months = sorted(set(monthly_receitas.index) | set(monthly_despesas.index))
        
        receitas_values = [monthly_receitas.get(m, 0) for m in all_months]
        despesas_values = [monthly_despesas.get(m, 0) for m in all_months]
        
        forecast_receitas = forecast_values(receitas_values, 3)
        forecast_despesas = forecast_values(despesas_values, 3)
        
        if all_months:
            last_month = all_months[-1]
            future_months = []
            for i in range(1, 4):
                next_month = last_month + i
                future_months.append(next_month)
            
            months_str = [str(m) for m in all_months]
            future_months_str = [str(m) for p in future_months for m in [p]]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=months_str,
                y=receitas_values,
                mode='lines+markers',
                name='Receitas (Real)',
                line=dict(color=DARK_THEME['accent_green'], width=3),
                marker=dict(size=8)
            ))
            
            fig.add_trace(go.Scatter(
                x=months_str,
                y=despesas_values,
                mode='lines+markers',
                name='Despesas (Real)',
                line=dict(color=DARK_THEME['accent_red'], width=3),
                marker=dict(size=8)
            ))
            
            fig.add_trace(go.Scatter(
                x=[months_str[-1]] + future_months_str,
                y=[receitas_values[-1]] + forecast_receitas,
                mode='lines+markers',
                name='Receitas (Projecao)',
                line=dict(color=DARK_THEME['accent_green'], width=2, dash='dash'),
                marker=dict(size=6, symbol='diamond')
            ))
            
            fig.add_trace(go.Scatter(
                x=[months_str[-1]] + future_months_str,
                y=[despesas_values[-1]] + forecast_despesas,
                mode='lines+markers',
                name='Despesas (Projecao)',
                line=dict(color=DARK_THEME['accent_red'], width=2, dash='dash'),
                marker=dict(size=6, symbol='diamond')
            ))
            
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=400,
                xaxis_title="Mes",
                yaxis_title="Valor (R$)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            col_proj1, col_proj2, col_proj3 = st.columns(3)
            
            with col_proj1:
                trend_receitas = calculate_trend(receitas_values)
                trend_icon = "+" if trend_receitas > 0 else ""
                trend_color = DARK_THEME['accent_green'] if trend_receitas >= 0 else DARK_THEME['accent_red']
                st.markdown(f"""
                <div style="
                    background: rgba(63, 185, 80, 0.1);
                    border: 1px solid {DARK_THEME['accent_green']};
                    border-radius: 8px;
                    padding: 1rem;
                    text-align: center;
                ">
                    <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.8rem;">TENDENCIA RECEITAS</div>
                    <div style="color: {trend_color}; font-size: 1.5rem; font-weight: 700; margin: 8px 0;">
                        {trend_icon}R$ {trend_receitas:,.2f}/mes
                    </div>
                    <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.75rem;">
                        Projecao prox. mes: R$ {forecast_receitas[0]:,.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_proj2:
                trend_despesas = calculate_trend(despesas_values)
                trend_icon = "+" if trend_despesas > 0 else ""
                trend_color = DARK_THEME['accent_red'] if trend_despesas > 0 else DARK_THEME['accent_green']
                st.markdown(f"""
                <div style="
                    background: rgba(248, 81, 73, 0.1);
                    border: 1px solid {DARK_THEME['accent_red']};
                    border-radius: 8px;
                    padding: 1rem;
                    text-align: center;
                ">
                    <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.8rem;">TENDENCIA DESPESAS</div>
                    <div style="color: {trend_color}; font-size: 1.5rem; font-weight: 700; margin: 8px 0;">
                        {trend_icon}R$ {trend_despesas:,.2f}/mes
                    </div>
                    <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.75rem;">
                        Projecao prox. mes: R$ {forecast_despesas[0]:,.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_proj3:
                saldo_projetado = forecast_receitas[0] - forecast_despesas[0]
                saldo_color = DARK_THEME['accent_cyan'] if saldo_projetado >= 0 else DARK_THEME['accent_red']
                st.markdown(f"""
                <div style="
                    background: rgba(57, 197, 207, 0.1);
                    border: 1px solid {DARK_THEME['accent_cyan']};
                    border-radius: 8px;
                    padding: 1rem;
                    text-align: center;
                ">
                    <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.8rem;">SALDO PROJETADO</div>
                    <div style="color: {saldo_color}; font-size: 1.5rem; font-weight: 700; margin: 8px 0;">
                        R$ {saldo_projetado:,.2f}
                    </div>
                    <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.75rem;">
                        Proximo mes
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_analysis1, col_analysis2 = st.columns(2)
    
    with col_analysis1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
            border: 1px solid {DARK_THEME['card_border']};
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        ">
            <h4 style="color: {DARK_THEME['text_primary']}; margin-bottom: 0.5rem;">Distribuicao de Despesas por Categoria</h4>
        </div>
        """, unsafe_allow_html=True)
        
        if 'categoria' in transactions_df.columns:
            despesas_cat = transactions_df[transactions_df['tipo'] == 'SAIDA'].groupby('categoria')['valor'].sum().sort_values(ascending=False)
            
            if not despesas_cat.empty:
                fig = go.Figure(go.Pie(
                    values=despesas_cat.values,
                    labels=despesas_cat.index,
                    hole=0.5,
                    marker=dict(colors=[DARK_THEME['accent_red'], DARK_THEME['accent_orange'], DARK_THEME['accent_purple'], DARK_THEME['accent_blue'], DARK_THEME['accent_cyan']]),
                    textinfo='percent+label',
                    textposition='outside'
                ))
                fig.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=350,
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados de categorias")
        else:
            st.info("Coluna de categoria nao disponivel")
    
    with col_analysis2:
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
            border: 1px solid {DARK_THEME['card_border']};
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        ">
            <h4 style="color: {DARK_THEME['text_primary']}; margin-bottom: 0.5rem;">Evolucao Mensal do Saldo</h4>
        </div>
        """, unsafe_allow_html=True)
        
        if 'mes' in transactions_df.columns:
            monthly_receitas = transactions_df[transactions_df['tipo'] == 'ENTRADA'].groupby('mes')['valor'].sum()
            monthly_despesas = transactions_df[transactions_df['tipo'] == 'SAIDA'].groupby('mes')['valor'].sum()
            
            all_months = sorted(set(monthly_receitas.index) | set(monthly_despesas.index))
            saldos = []
            for m in all_months:
                rec = monthly_receitas.get(m, 0)
                desp = monthly_despesas.get(m, 0)
                saldos.append(rec - desp)
            
            if saldos:
                months_str = [str(m) for m in all_months]
                colors = [DARK_THEME['accent_green'] if s >= 0 else DARK_THEME['accent_red'] for s in saldos]
                
                fig = go.Figure(go.Bar(
                    x=months_str,
                    y=saldos,
                    marker=dict(color=colors),
                    text=[f'R$ {v:,.0f}' for v in saldos],
                    textposition='outside'
                ))
                fig.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=350,
                    xaxis_title="Mes",
                    yaxis_title="Saldo (R$)"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Dados insuficientes")
        else:
            st.info("Dados mensais nao disponiveis")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
        border: 1px solid {DARK_THEME['card_border']};
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    ">
        <h3 style="color: {DARK_THEME['text_primary']}; margin-bottom: 0.5rem;">Insights e Recomendacoes</h3>
    </div>
    """, unsafe_allow_html=True)
    
    insights = []
    
    if margem > 20:
        insights.append(("Margem Saudavel", f"Sua margem de {margem:.1f}% esta acima de 20%, indicando boa saude financeira.", DARK_THEME['accent_green']))
    elif margem > 0:
        insights.append(("Margem Positiva", f"Sua margem de {margem:.1f}% esta positiva, mas pode ser melhorada.", DARK_THEME['accent_orange']))
    else:
        insights.append(("Atencao", f"Sua margem de {margem:.1f}% esta negativa. Revise suas despesas.", DARK_THEME['accent_red']))
    
    if 'mes' in transactions_df.columns and len(all_months) >= 2:
        trend_receitas = calculate_trend(receitas_values)
        if trend_receitas > 0:
            insights.append(("Receitas em Alta", f"Suas receitas estao crescendo em media R$ {trend_receitas:,.2f} por mes.", DARK_THEME['accent_green']))
        else:
            insights.append(("Receitas em Queda", f"Suas receitas estao diminuindo em media R$ {abs(trend_receitas):,.2f} por mes.", DARK_THEME['accent_red']))
    
    if not shows_df.empty and 'publico' in shows_df.columns:
        publico_medio = shows_df['publico'].mean()
        if publico_medio > 0:
            insights.append(("Publico", f"Seu publico medio por show e de {publico_medio:,.0f} pessoas.", DARK_THEME['accent_purple']))
    
    for title, text, color in insights:
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.5rem;
        ">
            <strong style="color: {color};">{title}</strong>
            <p style="color: {DARK_THEME['text_secondary']}; margin: 0.5rem 0 0 0;">{text}</p>
        </div>
        """, unsafe_allow_html=True)
