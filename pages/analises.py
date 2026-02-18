"""
Página dedicada para análises detalhadas de Receitas e Despesas.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from core.data_loader import data_loader


def show_receitas_vs_despesas(data):
    """Página de análise Receitas vs Despesas"""
    st.header("Análise Comparativa: Receitas vs. Despesas")

    if not data or 'transactions' not in data:
        st.error("Não foi possível carregar os dados de transações.")
        return

    # Filtrar transações pagas
    transacoes_pagas = data['transactions'][
        data['transactions']['payment_status'] == 'PAGO'
    ].copy()

    if transacoes_pagas.empty:
        st.info("Nenhuma transação paga encontrada para análise.")
        return

    # Converter data para datetime se necessário
    if 'data' in transacoes_pagas.columns:
        transacoes_pagas['data'] = pd.to_datetime(transacoes_pagas['data'], errors='coerce')

    # Análise comparativa
    receitas = transacoes_pagas[transacoes_pagas['tipo'] == 'ENTRADA']
    despesas = transacoes_pagas[transacoes_pagas['tipo'] == 'SAIDA']

    total_receitas = receitas['valor'].sum() if 'valor' in receitas.columns else 0
    total_despesas = despesas['valor'].sum() if 'valor' in despesas.columns else 0
    saldo = total_receitas - total_despesas

    # KPIs comparativos
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Receitas", f"R$ {total_receitas:,.2f}")

    with col2:
        st.metric("Total Despesas", f"R$ {total_despesas:,.2f}")

    with col3:
        delta_percent = ((total_receitas - total_despesas) / total_receitas * 100) if total_receitas > 0 else 0
        st.metric("Saldo", f"R$ {saldo:,.2f}",
                  delta=f"{delta_percent:.1f}%")

    # Gráfico comparativo
    fig = go.Figure(data=[
        go.Bar(name='Receitas', x=['Total'], y=[total_receitas], marker_color='#00CC96'),
        go.Bar(name='Despesas', x=['Total'], y=[total_despesas], marker_color='#EF553B')
    ])

    fig.update_layout(
        title="Comparação Geral: Receitas vs Despesas",
        barmode='group',
        height=400,
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Análise temporal
    st.subheader("Evolução Temporal")

    # Agrupar por mês se tiver dados de data
    if 'data' in transacoes_pagas.columns and not transacoes_pagas['data'].isna().all():
        transacoes_pagas['mes'] = transacoes_pagas['data'].dt.to_period('M')

        evolucao_mensal = transacoes_pagas.groupby(['mes', 'tipo'])['valor'].sum().unstack().fillna(0)

        if not evolucao_mensal.empty and len(evolucao_mensal) > 1:
            fig2 = go.Figure()

            if 'ENTRADA' in evolucao_mensal.columns:
                fig2.add_trace(go.Scatter(
                    x=evolucao_mensal.index.astype(str),
                    y=evolucao_mensal['ENTRADA'],
                    name='Receitas',
                    line=dict(color='#00CC96', width=3)
                ))

            if 'SAIDA' in evolucao_mensal.columns:
                fig2.add_trace(go.Scatter(
                    x=evolucao_mensal.index.astype(str),
                    y=evolucao_mensal['SAIDA'],
                    name='Despesas',
                    line=dict(color='#EF553B', width=3)
                ))

            fig2.update_layout(
                title="Evolução Mensal",
                xaxis_title="Mês",
                yaxis_title="Valor (R$)",
                height=400,
                template='plotly_white'
            )

            st.plotly_chart(fig2, use_container_width=True)

def show_despesas_detalhadas(data):
    """Página de análise detalhada de despesas - Visual Melhorado"""
    st.header("Análise Detalhada de Despesas")

    if not data or 'transactions' not in data:
        st.error("Nao foi possivel carregar os dados")
        return

    # Filtrar apenas despesas pagas
    despesas = data['transactions'][
        (data['transactions']['tipo'] == 'SAIDA') &
        (data['transactions']['payment_status'] == 'PAGO')
        ].copy()

    if despesas.empty:
        st.info("Nenhuma despesa encontrada para análise.")
        return

    # Estatísticas gerais
    total_despesas = despesas['valor'].sum() if 'valor' in despesas.columns else 0
    media_despesas = despesas['valor'].mean() if 'valor' in despesas.columns else 0
    qtd_despesas = len(despesas)
    maior_despesa = despesas['valor'].max() if 'valor' in despesas.columns else 0

    # KPI Cards com visual melhorado
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #f85149;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">TOTAL DESPESAS</p>
            <h2 style="color: #f85149; margin: 5px 0;">R$ {total_despesas:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #58a6ff;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">MEDIA POR DESPESA</p>
            <h2 style="color: #58a6ff; margin: 5px 0;">R$ {media_despesas:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #a371f7;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">QUANTIDADE</p>
            <h2 style="color: #a371f7; margin: 5px 0;">{qtd_despesas}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #d29922;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">MAIOR DESPESA</p>
            <h2 style="color: #d29922; margin: 5px 0;">R$ {maior_despesa:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("""
        <div style="background: linear-gradient(145deg, #161b22 0%, #21262d 100%);
            border: 1px solid #30363d; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
            <h4 style="color: #c9d1d9; margin: 0 0 0.5rem 0; font-size: 14px;">Despesas por Categoria</h4>
        </div>
        """, unsafe_allow_html=True)

        if 'categoria' in despesas.columns:
            despesas_por_categoria = despesas.groupby('categoria')['valor'].sum().sort_values(ascending=False)

            if not despesas_por_categoria.empty:
                colors = ['#f85149', '#ff7b72', '#ffa198', '#d29922', '#a371f7', '#58a6ff', '#39c5cf']
                fig_pie = go.Figure(go.Pie(
                    values=despesas_por_categoria.values,
                    labels=despesas_por_categoria.index,
                    hole=0.5,
                    marker=dict(colors=colors[:len(despesas_por_categoria)]),
                    textinfo='percent+label',
                    textposition='outside'
                ))
                fig_pie.update_layout(
                    template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    height=350, showlegend=False
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_chart2:
        st.markdown("""
        <div style="background: linear-gradient(145deg, #161b22 0%, #21262d 100%);
            border: 1px solid #30363d; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
            <h4 style="color: #c9d1d9; margin: 0 0 0.5rem 0; font-size: 14px;">Top 10 Despesas por Subcategoria</h4>
        </div>
        """, unsafe_allow_html=True)

        if 'subcategoria' in despesas.columns:
            despesas_por_sub = despesas.groupby('subcategoria')['valor'].sum().sort_values(ascending=False).head(10)
            if not despesas_por_sub.empty:
                fig_bar = go.Figure(go.Bar(
                    x=despesas_por_sub.values, y=despesas_por_sub.index, orientation='h',
                    marker=dict(color=despesas_por_sub.values, colorscale='Reds', showscale=False),
                    text=[f'R$ {v:,.2f}' for v in despesas_por_sub.values], textposition='auto'
                ))
                fig_bar.update_layout(
                    template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    height=350, yaxis=dict(autorange="reversed"), xaxis_title="Valor (R$)", yaxis_title=""
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


def show_receitas_detalhadas(data):
    """Página de análise detalhada de receitas - Visual Melhorado"""
    st.header("Análise Detalhada de Receitas")

    if not data or 'transactions' not in data:
        st.error("Nao foi possivel carregar os dados")
        return

    # Filtrar apenas receitas pagas
    receitas = data['transactions'][
        (data['transactions']['tipo'] == 'ENTRADA') &
        (data['transactions']['payment_status'] == 'PAGO')
        ].copy()

    if receitas.empty:
        st.info("Nenhuma receita encontrada para análise.")
        return

    # Estatísticas gerais
    total_receitas = receitas['valor'].sum() if 'valor' in receitas.columns else 0
    media_receitas = receitas['valor'].mean() if 'valor' in receitas.columns else 0
    qtd_receitas = len(receitas)
    maior_receita = receitas['valor'].max() if 'valor' in receitas.columns else 0

    # KPI Cards com visual melhorado
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #3fb950;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">TOTAL RECEITAS</p>
            <h2 style="color: #3fb950; margin: 5px 0;">R$ {total_receitas:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #58a6ff;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">MEDIA POR RECEITA</p>
            <h2 style="color: #58a6ff; margin: 5px 0;">R$ {media_receitas:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #a371f7;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">QUANTIDADE</p>
            <h2 style="color: #a371f7; margin: 5px 0;">{qtd_receitas}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 20px; border-radius: 10px; border-left: 4px solid #d29922;">
            <p style="color: #8b949e; margin: 0; font-size: 0.85rem;">MAIOR RECEITA</p>
            <h2 style="color: #d29922; margin: 5px 0;">R$ {maior_receita:,.2f}</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Análise por categoria com visual melhorado
    if 'categoria' in receitas.columns:
        receitas_por_categoria = receitas.groupby('categoria')['valor'].sum().sort_values(ascending=False)

        if not receitas_por_categoria.empty:
            col_cat1, col_cat2 = st.columns(2)

            with col_cat1:
                st.markdown("### Receitas por Categoria")
                for i, (categoria, valor) in enumerate(receitas_por_categoria.head(5).items()):
                    percentual = (valor / total_receitas * 100) if total_receitas > 0 else 0
                    color = ['#3fb950', '#58a6ff', '#a371f7', '#d29922', '#39c5cf'][i % 5]
                    st.markdown(f"""
                    <div style="background: #161b22; padding: 12px; border-radius: 8px; 
                                margin-bottom: 8px; border-left: 3px solid {color};">
                        <span style="color: #8b949e; font-size: 0.85rem;">{categoria}</span><br/>
                        <span style="color: {color}; font-size: 1.2rem; font-weight: bold;">R$ {valor:,.2f}</span>
                        <span style="color: #8b949e; font-size: 0.85rem;"> ({percentual:.1f}%)</span>
                    </div>
                    """, unsafe_allow_html=True)

            with col_cat2:
                fig_cat = go.Figure(go.Bar(
                    x=receitas_por_categoria.values, y=receitas_por_categoria.index, orientation='h',
                    marker=dict(color=receitas_por_categoria.values, colorscale='Greens', showscale=False),
                    text=[f'R$ {v:,.2f}' for v in receitas_por_categoria.values], textposition='auto'
                ))
                fig_cat.update_layout(
                    title="Distribuição por Categoria", template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    height=350, yaxis=dict(autorange="reversed"),
                    xaxis_title="Valor (R$)", yaxis_title=""
                )
                st.plotly_chart(fig_cat, use_container_width=True)

    # Evolucao temporal das receitas
    if 'data' in receitas.columns:
        receitas_temp = receitas.copy()
        receitas_temp['data'] = pd.to_datetime(receitas_temp['data'], errors='coerce')
        receitas_temp = receitas_temp.dropna(subset=['data'])

        if not receitas_temp.empty:
            receitas_temp['mes'] = receitas_temp['data'].dt.to_period('M').astype(str)
            receitas_mensal = receitas_temp.groupby('mes')['valor'].sum().reset_index()

            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=receitas_mensal['mes'], y=receitas_mensal['valor'],
                mode='lines+markers', fill='tozeroy',
                line=dict(color='#3fb950', width=3),
                marker=dict(size=8, color='#3fb950'),
                fillcolor='rgba(63, 185, 80, 0.2)'
            ))
            fig_line.update_layout(
                title="Evolução Mensal das Receitas", template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                height=300, xaxis_title="Mês", yaxis_title="Valor (R$)"
            )
            st.plotly_chart(fig_line, use_container_width=True)


def main():
    """Função principal para a página de Análises."""
    st.title("Análises Detalhadas")

    # Carregar dados uma vez
    try:
        with st.spinner("Carregando dados..."):
            data = data_loader.load_all_data()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        if "Credenciais não configuradas" in str(e):
            st.info("💡 Configure as credenciais no menu lateral para conectar ao Google Sheets.")
        return

    # Abas para cada tipo de análise
    tab1, tab2, tab3 = st.tabs([
        "📊 Receitas vs. Despesas",
        "💸 Despesas Detalhadas",
        "💰 Receitas Detalhadas"
    ])

    with tab1:
        show_receitas_vs_despesas(data)

    with tab2:
        show_despesas_detalhadas(data)

    with tab3:
        show_receitas_detalhadas(data)


if __name__ == "__main__":
    # Para executar esta página de forma isolada (se necessário)
    # Adicione a configuração de página aqui se for executar isoladamente
    # setup_page_config()
    main()