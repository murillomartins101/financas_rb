"""
Pagina de gestao e analise de shows - Visual Melhorado
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

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

def main():
    """Pagina de shows com visual melhorado"""
    st.title("Shows - Rockbuzz Finance")
    
    with st.spinner("Carregando dados..."):
        data = data_loader.load_all_data()
    
    if not data or 'shows' not in data or data['shows'].empty:
        st.error("Nao foi possivel carregar os dados de shows")
        return
    
    shows_df = data['shows'].copy()
    transactions_df = data.get('transactions', pd.DataFrame()).copy()
    
    if 'data_show' in shows_df.columns:
        shows_df['data_show'] = pd.to_datetime(shows_df['data_show'], errors='coerce')
    
    total_shows = len(shows_df)
    shows_realizados = len(shows_df[shows_df['status'] == 'REALIZADO']) if 'status' in shows_df.columns else 0
    shows_confirmados = len(shows_df[shows_df['status'] == 'CONFIRMADO']) if 'status' in shows_df.columns else 0
    cache_total = shows_df['cache_acordado'].sum() if 'cache_acordado' in shows_df.columns else 0
    publico_total = shows_df['publico'].sum() if 'publico' in shows_df.columns else 0
    publico_medio = shows_df['publico'].mean() if 'publico' in shows_df.columns and not shows_df['publico'].isna().all() else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid {DARK_THEME['accent_blue']};">
            <p style="color: {DARK_THEME['text_secondary']}; margin: 0; font-size: 0.85rem;">TOTAL SHOWS</p>
            <h2 style="color: {DARK_THEME['accent_blue']}; margin: 5px 0;">{total_shows}</h2>
            <p style="color: {DARK_THEME['text_secondary']}; margin: 0; font-size: 0.75rem;">Realizados: {shows_realizados}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid {DARK_THEME['accent_green']};">
            <p style="color: {DARK_THEME['text_secondary']}; margin: 0; font-size: 0.85rem;">CACHE TOTAL</p>
            <h2 style="color: {DARK_THEME['accent_green']}; margin: 5px 0;">R$ {cache_total:,.2f}</h2>
            <p style="color: {DARK_THEME['text_secondary']}; margin: 0; font-size: 0.75rem;">Confirmados: {shows_confirmados}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid {DARK_THEME['accent_purple']};">
            <p style="color: {DARK_THEME['text_secondary']}; margin: 0; font-size: 0.85rem;">PUBLICO TOTAL</p>
            <h2 style="color: {DARK_THEME['accent_purple']}; margin: 5px 0;">{publico_total:,.0f}</h2>
            <p style="color: {DARK_THEME['text_secondary']}; margin: 0; font-size: 0.75rem;">pessoas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid {DARK_THEME['accent_orange']};">
            <p style="color: {DARK_THEME['text_secondary']}; margin: 0; font-size: 0.85rem;">PUBLICO MEDIO</p>
            <h2 style="color: {DARK_THEME['accent_orange']}; margin: 5px 0;">{publico_medio:,.0f}</h2>
            <p style="color: {DARK_THEME['text_secondary']}; margin: 0; font-size: 0.75rem;">por show</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    valor_bruto_shows = 0
    custos_operacionais = 0
    
    if not transactions_df.empty:
        receitas_shows = transactions_df[
            (transactions_df['tipo'] == 'ENTRADA') & 
            (transactions_df['payment_status'] == 'PAGO')
        ]
        if not receitas_shows.empty:
            valor_bruto_shows = receitas_shows['valor'].sum()
        
        despesas = transactions_df[
            (transactions_df['tipo'] == 'SAIDA') & 
            (transactions_df['payment_status'] == 'PAGO')
        ]
        if not despesas.empty:
            custos_operacionais = despesas['valor'].sum()
    
    valor_efetivo = valor_bruto_shows - custos_operacionais
    percentual_retido = (valor_efetivo / valor_bruto_shows * 100) if valor_bruto_shows > 0 else 0
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
        border: 1px solid {DARK_THEME['card_border']};
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    ">
        <h3 style="color: {DARK_THEME['text_primary']}; margin-bottom: 1rem;">Resultados</h3>
    """, unsafe_allow_html=True)
    
    col_valor1, col_valor2, col_valor3 = st.columns(3)
    
    with col_valor1:
        st.markdown(f"""
        <div style="
            background: rgba(63, 185, 80, 0.1);
            border: 1px solid {DARK_THEME['accent_green']};
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        ">
            <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.8rem; text-transform: uppercase;">
                VALOR BRUTO
            </div>
            <div style="color: {DARK_THEME['accent_green']}; font-size: 1.8rem; font-weight: 700; margin: 8px 0;">
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
            background: rgba(248, 81, 73, 0.1);
            border: 1px solid {DARK_THEME['accent_red']};
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        ">
            <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.8rem; text-transform: uppercase;">
                CUSTOS OPERACIONAIS
            </div>
            <div style="color: {DARK_THEME['accent_red']}; font-size: 1.8rem; font-weight: 700; margin: 8px 0;">
                R$ {custos_operacionais:,.2f}
            </div>
            <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.75rem;">
                Equipe, equipamentos, posts, etc.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_valor3:
        valor_color = DARK_THEME['accent_cyan'] if valor_efetivo >= 0 else DARK_THEME['accent_red']
        st.markdown(f"""
        <div style="
            background: rgba(57, 197, 207, 0.1);
            border: 1px solid {valor_color};
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        ">
            <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.8rem; text-transform: uppercase;">
                VALOR EFETIVO
            </div>
            <div style="color: {valor_color}; font-size: 1.8rem; font-weight: 700; margin: 8px 0;">
                R$ {valor_efetivo:,.2f}
            </div>
            <div style="color: {DARK_THEME['text_secondary']}; font-size: 0.75rem;">
                {percentual_retido:.1f}% do valor bruto retido
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        if 'publico' in shows_df.columns and 'data_show' in shows_df.columns:
            shows_with_publico = shows_df.dropna(subset=['publico', 'data_show'])
            if not shows_with_publico.empty:
                shows_sorted = shows_with_publico.sort_values('data_show')
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=shows_sorted['data_show'],
                    y=shows_sorted['publico'],
                    mode='lines+markers',
                    fill='tozeroy',
                    line=dict(color=DARK_THEME['accent_purple'], width=3),
                    marker=dict(size=8, color=DARK_THEME['accent_purple']),
                    fillcolor='rgba(163, 113, 247, 0.2)',
                    name='Publico'
                ))
                fig.update_layout(
                    title="Evolucao do Publico por Show",
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=350,
                    xaxis_title="Data",
                    yaxis_title="Publico",
                    showlegend=False
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("Dados de publico insuficientes")
        else:
            st.info("Dados de publico nao disponiveis")
    
    with col_chart2:
        if 'cache_acordado' in shows_df.columns and 'data_show' in shows_df.columns:
            shows_with_cache = shows_df.dropna(subset=['cache_acordado', 'data_show'])
            if not shows_with_cache.empty:
                shows_sorted = shows_with_cache.sort_values('data_show')
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=shows_sorted['data_show'],
                    y=shows_sorted['cache_acordado'],
                    marker=dict(
                        color=shows_sorted['cache_acordado'],
                        colorscale='Greens',
                        showscale=False
                    ),
                    text=[f'R$ {v:,.0f}' for v in shows_sorted['cache_acordado']],
                    textposition='outside'
                ))
                fig.update_layout(
                    title="Cache por Show",
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=350,
                    xaxis_title="Data",
                    yaxis_title="Cache (R$)",
                    showlegend=False
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("Dados de cache insuficientes")
        else:
            st.info("Dados de cache nao disponiveis")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_chart3, col_chart4 = st.columns(2)
    
    with col_chart3:
        if 'status' in shows_df.columns:
            status_counts = shows_df['status'].value_counts()
            colors = [DARK_THEME['accent_green'], DARK_THEME['accent_blue'], DARK_THEME['accent_orange'], DARK_THEME['accent_red']]
            
            fig = go.Figure(go.Pie(
                values=status_counts.values,
                labels=status_counts.index,
                hole=0.5,
                marker=dict(colors=colors[:len(status_counts)]),
                textinfo='percent+label',
                textposition='outside'
            ))
            fig.update_layout(
                title="Distribuicao por Status",
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=350,
                showlegend=False
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Dados de status nao disponiveis")
    
    with col_chart4:
        if 'publico' in shows_df.columns and 'cache_acordado' in shows_df.columns:
            shows_valid = shows_df.dropna(subset=['publico', 'cache_acordado'])
            if not shows_valid.empty and len(shows_valid) > 1:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=shows_valid['publico'],
                    y=shows_valid['cache_acordado'],
                    mode='markers',
                    marker=dict(
                        size=12,
                        color=shows_valid['cache_acordado'],
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="Cache")
                    ),
                    text=shows_valid.get('local', shows_valid.index),
                    hovertemplate='Publico: %{x}<br>Cache: R$ %{y:,.2f}<extra></extra>'
                ))
                fig.update_layout(
                    title="Relacao Publico x Cache",
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=350,
                    xaxis_title="Publico",
                    yaxis_title="Cache (R$)"
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("Dados insuficientes para correlacao")
        else:
            st.info("Dados de publico/cache nao disponiveis")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if 'publico' in shows_df.columns:
        top_shows = shows_df.nlargest(10, 'publico')[['data_show', 'local', 'publico', 'cache_acordado', 'status']].copy() if 'local' in shows_df.columns else shows_df.nlargest(10, 'publico')
        
        if not top_shows.empty:
            st.markdown(f"""
            <div style="
                background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
                border: 1px solid {DARK_THEME['card_border']};
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 1rem;
            ">
                <h4 style="color: {DARK_THEME['text_primary']}; margin-bottom: 0.5rem;">Top 10 Shows por Publico</h4>
            </div>
            """, unsafe_allow_html=True)
            
            fig = go.Figure(go.Bar(
                x=top_shows['publico'],
                y=top_shows.get('local', top_shows.index.astype(str)),
                orientation='h',
                marker=dict(
                    color=top_shows['publico'],
                    colorscale='Purples',
                    showscale=False
                ),
                text=[f'{v:,.0f}' for v in top_shows['publico']],
                textposition='auto'
            ))
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=400,
                yaxis=dict(autorange="reversed"),
                xaxis_title="Publico",
                yaxis_title=""
            )
            st.plotly_chart(fig, width='stretch')
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(145deg, {DARK_THEME['card_bg']} 0%, #21262d 100%);
        border: 1px solid {DARK_THEME['card_border']};
        border-radius: 12px;
        padding: 1rem;
    ">
        <h4 style="color: {DARK_THEME['text_primary']}; margin-bottom: 0.5rem;">Lista de Shows</h4>
    </div>
    """, unsafe_allow_html=True)
    
    if 'data_show' in shows_df.columns:
        shows_display = shows_df.copy()
        shows_display['data_show'] = shows_display['data_show'].dt.strftime('%d/%m/%Y')
    else:
        shows_display = shows_df.copy()
    
    colunas_possiveis = ['data_show', 'local', 'cidade', 'publico', 'cache_acordado', 'status']
    colunas_disponiveis = [col for col in colunas_possiveis if col in shows_display.columns]
    
    if colunas_disponiveis:
        st.dataframe(
            shows_display[colunas_disponiveis].sort_values('data_show' if 'data_show' in shows_display.columns else colunas_disponiveis[0], ascending=False),
            width='stretch',
            height=400
        )
    else:
        st.dataframe(shows_display, width='stretch', height=400)

if __name__ == "__main__":
    main()
